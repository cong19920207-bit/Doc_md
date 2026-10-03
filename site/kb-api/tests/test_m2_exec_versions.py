# -*- coding: utf-8 -*-
"""多轮编排 M2：同会话互斥与幂等、刷新出新版本并沿用原快照、保存失败同文补写与保存阻塞、按版本赞踩与热度资格。"""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import main, msg_store
from app.auth_store import ROLE_USER_ID, AuthStore, MemoryAuthRepo
from app.conv_store import ConvStore, MemoryConvRepo
from app.logs import LogStore
from app.models_ext import ModelError
from app.msg_store import MemoryMsgRepo, MsgStore

ROOT = Path(__file__).resolve().parents[3]
INIT_SQL = (ROOT / "site" / "kb-api" / "sql" / "init.sql").read_text(encoding="utf-8")
QA_JS = (ROOT / "site" / "feature-interaction" / "qa.js").read_text(encoding="utf-8")


class FakeLogs:
    """替身执行日志：支持按请求号查找、写反馈。"""

    def __init__(self) -> None:
        self.rows: dict[str, dict] = {}
        self.last_error = None

    def insert_running(self, row: dict) -> bool:
        self.rows[row["round_id"]] = dict(row)
        return True

    def update_round(self, round_id: str, fields: dict) -> bool:
        self.rows.setdefault(round_id, {"round_id": round_id}).update(fields)
        return True

    def get_round(self, round_id: str) -> dict | None:
        row = self.rows.get(round_id)
        return json.loads(json.dumps(row, default=str)) if row else None

    def find_by_request(self, conv_id: str, crid: str) -> dict | None:
        for rid, row in self.rows.items():
            if row.get("conv_id") == conv_id and row.get("client_request_id") == crid:
                return dict(row, round_id=rid)
        return None

    def set_feedback(self, round_id: str, feedback):
        if round_id not in self.rows:
            return "not_found"
        self.rows[round_id]["feedback"] = feedback
        return "ok"

    def delete_conv(self, conv_id: str) -> None:
        self.rows = {k: v for k, v in self.rows.items() if v.get("conv_id") != conv_id}

    def ensure_feedback_columns(self) -> bool:
        return True

    def ensure_runtime_columns(self) -> bool:
        return True


class FakePipeline:
    def __init__(self) -> None:
        self.calls: list[tuple[str, object]] = []
        self.answer = "好的。"
        self.blocks = [{"path": "a.md", "chunk_id": "c1", "content": "正文", "feature_id": "vip"}]
        self.same_topic = False
        self.fail_generate = False
        self.on_generate = None

    async def rewrite(self, original, history, cfg):
        self.calls.append(("rewrite", list(history)))
        return {"rewrite_query": original, "same_topic": self.same_topic, "named_feature_ids": []}

    async def retrieve(self, original, rewrite_query, named_ids, cfg):
        self.calls.append(("retrieve", rewrite_query))
        return {"mode": "hybrid", "lanes": {}, "candidates": [{"path": "a.md"}]}

    async def rerank(self, query, candidates, named, prev_blocks, same_topic, cfg):
        self.calls.append(("rerank", list(prev_blocks)))
        return list(self.blocks)

    async def stream_answer(self, original, rw, c_gen, cfg):
        self.calls.append(("generate", original))
        if self.on_generate:
            self.on_generate()
        if self.fail_generate:
            raise ModelError("gen_fail", "boom")
        yield self.answer


async def _noop_index():
    return None


@pytest.fixture
def env(monkeypatch):
    auth = AuthStore(MemoryAuthRepo())
    auth.ensure_schema()
    auth.bootstrap_if_empty("admin", "secret")
    auth.create_account("alice", "pw", ROLE_USER_ID)
    convs = ConvStore(MemoryConvRepo())
    msgs = MsgStore(MemoryMsgRepo())
    logs = FakeLogs()
    pipe = FakePipeline()
    monkeypatch.setattr(main, "auth", auth)
    monkeypatch.setattr(main, "convs", convs)
    monkeypatch.setattr(main, "msgs", msgs)
    monkeypatch.setattr(main, "logs", logs)
    monkeypatch.setattr(main, "pipeline", pipe)
    monkeypatch.setattr(main, "_startup_index", _noop_index)
    monkeypatch.setattr(main, "_fail_type", lambda *a, **k: None)
    monkeypatch.setattr(main, "SAVE_RETRY_DELAYS", (0.0, 0.0))
    monkeypatch.setattr(main, "_PENDING_REPLIES", {})
    with TestClient(main.app) as client:
        assert client.post("/api/kb/auth/login", json={"username": "alice", "password": "pw"}).status_code == 200
        yield {"client": client, "convs": convs, "msgs": msgs, "logs": logs, "pipe": pipe}


def _events(text: str) -> list[tuple[str, dict]]:
    out = []
    for block in text.split("\n\n"):
        event, data = "message", []
        for line in block.split("\n"):
            if line.startswith("event:"):
                event = line[6:].strip()
            elif line.startswith("data:"):
                data.append(line[5:].strip())
        if data:
            out.append((event, json.loads("\n".join(data))))
    return out


def _last(events, name):
    found = [d for e, d in events if e == name]
    return found[-1] if found else None


def _new_conv(client) -> str:
    return client.post("/api/kb/conversations", json={"title": "t"}).json()["id"]


def _ask(client, conv_id, query, crid=None, **extra):
    body = {"conversation_id": conv_id, "query": query}
    if crid:
        body["client_request_id"] = crid
    body.update(extra)
    return _events(client.post("/api/kb/ask", json=body).text)


def _refresh(client, conv_id, logical_round_id, crid=None):
    body = {"conversation_id": conv_id, "op_type": "refresh", "logical_round_id": logical_round_id, "query": "忽略"}
    if crid:
        body["client_request_id"] = crid
    return _events(client.post("/api/kb/ask", json=body).text)


def _assistants(msgs, cid, round_id):
    return [r for r in msgs.round_rows(cid, round_id) if r["role"] == "assistant"]


def _rewrite_histories(pipe):
    return [h for name, h in pipe.calls if name == "rewrite"]


# ---------------- STEP-Q07 ----------------

def test_q07_execution_holds_conversation_and_second_device_rejected(env):
    """AT-14：执行期间另一设备同会话发送被拒（忙碌），不写 User、不调模型；结束后释放。"""
    client, convs, msgs, pipe = env["client"], env["convs"], env["msgs"], env["pipe"]
    cid = _new_conv(client)
    other_cid = _new_conv(client)
    seen = {}

    def during():
        seen["same"] = convs.acquire_run(cid, "r-device-b")
        seen["other"] = convs.acquire_run(other_cid, "r-device-b2")

    pipe.on_generate = during
    done = _last(_ask(client, cid, "设备 A 的问题", "qa-1"), "done")
    assert done["status"] == "success"
    assert seen["same"] == ("busy", done["exec_id"])
    # RQ-07：只锁同一会话，其他会话不受影响
    assert seen["other"] == ("ok", None)
    convs.release_run(other_cid, "r-device-b2")
    pipe.on_generate = None

    # 模拟设备 B 的执行仍占用：设备 A 的新发送被拒
    assert convs.acquire_run(cid, "r-device-b") == ("ok", None)
    pipe.calls.clear()
    ev = _ask(client, cid, "设备 A 的第二问", "qa-2")
    err = _last(ev, "error")
    assert err["type"] == "conversation_busy"
    assert err["running_exec_id"] == "r-device-b"
    assert _last(ev, "accepted") is None
    assert pipe.calls == []
    assert [r["content"] for r in msgs.effective_messages(cid) if r["role"] == "user"] == ["设备 A 的问题"]
    # 其他会话仍可发送
    assert _last(_ask(client, other_cid, "别的会话", "qa-3"), "done")["status"] == "success"
    # 设备 B 结束后可再发；忙碌时没写 User，同一请求号重试照常受理
    convs.release_run(cid, "r-device-b")
    assert _last(_ask(client, cid, "设备 A 的第二问", "qa-2"), "done")["status"] == "success"


def test_q07_retransmit_is_duplicate_not_busy_and_not_rerun(env):
    """C39：同一请求网络重传不重跑；即便会话正被占用，也先识别为重复而不是忙碌。"""
    client, convs, pipe = env["client"], env["convs"], env["pipe"]
    cid = _new_conv(client)
    first = _last(_ask(client, cid, "VIP 保级", "qa-10"), "done")
    calls = len(pipe.calls)
    convs.acquire_run(cid, "r-someone")
    dup = _last(_ask(client, cid, "VIP 保级", "qa-10"), "error")
    assert dup["type"] == "duplicate_request"
    assert dup["existing"]["exec_id"] == first["exec_id"]
    assert len(pipe.calls) == calls


def test_q07_refresh_retransmit_is_duplicate(env):
    client, msgs, pipe = env["client"], env["msgs"], env["pipe"]
    cid = _new_conv(client)
    base = _last(_ask(client, cid, "第一问", "qa-20"), "done")
    one = _last(_refresh(client, cid, base["logical_round_id"], "rf-1"), "done")
    calls = len(pipe.calls)
    dup = _last(_refresh(client, cid, base["logical_round_id"], "rf-1"), "error")
    assert dup["type"] == "duplicate_request"
    assert dup["existing"]["exec_id"] == one["exec_id"]
    assert len(pipe.calls) == calls
    assert len(_assistants(msgs, cid, base["logical_round_id"])) == 2


def test_q07_lease_expiry_and_release_only_own():
    """崩溃后租期到期可再抢占；释放只放本执行的执行权。"""
    convs = ConvStore(MemoryConvRepo())
    conv = convs.create("acc")
    cid = conv["id"]
    assert convs.acquire_run(cid, "e1") == ("ok", None)
    convs.release_run(cid, "e-other")
    assert convs.acquire_run(cid, "e2") == ("busy", "e1")
    convs.repo.rows[cid]["run_until"] = datetime.utcnow() - timedelta(seconds=1)
    assert convs.acquire_run(cid, "e2") == ("ok", None)


def test_q07_client_wiring():
    assert '"conversation_busy"' in QA_JS
    assert "run_exec_id VARCHAR(64) NULL" in INIT_SQL
    assert "INDEX idx_qa_rounds_conv_req (conv_id, client_request_id)" in INIT_SQL


# ---------------- STEP-Q08 ----------------

def test_q08_refresh_last_adds_exec_and_version_only(env):
    """AT-09：刷新最后一条，原 MSG_ID 与 ROUND_ID 不变，不新增 User，新增一个版本与一个执行。"""
    client, msgs, logs, pipe = env["client"], env["msgs"], env["logs"], env["pipe"]
    cid = _new_conv(client)
    base = _last(_ask(client, cid, "退款怎么扣", "qa-30"), "done")
    lrid = base["logical_round_id"]
    pipe.answer = "新的回答"
    ev = _refresh(client, cid, lrid, "rf-30")
    acc, done = _last(ev, "accepted"), _last(ev, "done")
    assert acc["user_msg_id"] == base["user_msg_id"] and acc["logical_round_id"] == lrid
    assert done["exec_id"] != base["exec_id"]
    assert done["version_no"] == 2 and done["adopted"] is True
    rows = msgs.effective_messages(cid)
    assert [r["role"] for r in rows].count("user") == 1
    assert len({r["round_id"] for r in rows}) == 1
    versions = _assistants(msgs, cid, lrid)
    assert [(v["version_no"], v["is_current"]) for v in versions] == [(1, 0), (2, 1)]
    assert versions[0]["id"] == base["assistant_msg_id"]
    assert logs.rows[done["exec_id"]]["op_type"] == "refresh"
    assert logs.rows[done["exec_id"]]["logical_round_id"] == lrid
    # 下一问的 L1 读当前采用版本
    pipe.calls.clear()
    _ask(client, cid, "下一问", "qa-31")
    assert _rewrite_histories(pipe)[-1] == [
        {"role": "user", "text": "退款怎么扣"},
        {"role": "assistant", "text": "新的回答"},
    ]


def test_q08_failed_new_version_keeps_default_and_feedback(env):
    """AT-28（版本部分）：新版本生成失败，当前采用版本及其反馈不变。"""
    client, msgs, logs, pipe = env["client"], env["msgs"], env["logs"], env["pipe"]
    cid = _new_conv(client)
    base = _last(_ask(client, cid, "VIP 保级", "qa-40"), "done")
    assert client.post(f"/api/kb/rounds/{base['exec_id']}/feedback", json={"feedback": "up"}).status_code == 200
    pipe.fail_generate = True
    done_err = _last(_refresh(client, cid, base["logical_round_id"], "rf-40"), "error")
    assert done_err["type"] == "gen_fail"
    assert done_err["adopted"] is False
    versions = _assistants(msgs, cid, base["logical_round_id"])
    current = [v for v in versions if v["is_current"]]
    assert [v["id"] for v in current] == [base["assistant_msg_id"]]
    assert logs.rows[base["exec_id"]]["feedback"] == "up"
    assert versions[-1]["completeness"] == "error_notice" and versions[-1]["is_current"] == 0


def test_q08_refresh_middle_uses_original_snapshot(env):
    """AT-10：刷新中间一条，历史快照消息集合等于原问题当时的快照，不含之后的消息。"""
    client, msgs, logs, pipe = env["client"], env["msgs"], env["logs"], env["pipe"]
    cid = _new_conv(client)
    _ask(client, cid, "问题一", "qa-50")
    b = _last(_ask(client, cid, "问题二", "qa-51"), "done")
    _ask(client, cid, "问题三", "qa-52")
    orig = logs.rows[b["exec_id"]]["snapshot"]
    pipe.calls.clear()
    done = _last(_refresh(client, cid, b["logical_round_id"], "rf-50"), "done")
    snap = logs.rows[done["exec_id"]]["snapshot"]
    assert snap["l1_msg_ids"] == orig["l1_msg_ids"]
    assert "snapshot_limited" not in snap
    assert [h["text"] for h in _rewrite_histories(pipe)[-1]] == ["问题一", "好的。"]
    later_ids = {r["id"] for r in msgs.effective_messages(cid) if r["seq"] > orig["cut_seq"]}
    assert not later_ids & {i for pair in snap["l1_msg_ids"] for i in pair}


def test_q08_refresh_next_day_keeps_time_base(env, monkeypatch):
    """AT-34（数据层）：隔日刷新沿用原问题的时间基准，不改成刷新当天。"""
    client, logs = env["client"], env["logs"]
    day1 = datetime(2026, 9, 28, 9, 0, 0)
    day2 = datetime(2026, 9, 29, 9, 0, 0)
    monkeypatch.setattr(msg_store, "_now", lambda: day1)
    cid = _new_conv(client)
    base = _last(_ask(client, cid, "昨天的充值算首充吗", "qa-60"), "done")
    monkeypatch.setattr(msg_store, "_now", lambda: day2)
    done = _last(_refresh(client, cid, base["logical_round_id"], "rf-60"), "done")
    t0 = logs.rows[base["exec_id"]]["snapshot"]["time_base"]
    t1 = logs.rows[done["exec_id"]]["snapshot"]["time_base"]
    assert t0 == t1 == str(day1)
    assert t1 != str(day2)


def test_q08_follow_up_reads_specified_exec_not_latest(env):
    """AT-37：三次刷新后续接采用的那次，读到的 EXEC_ID 是被采用版本的，不是该回合最后一次执行。"""
    client, msgs, logs, pipe = env["client"], env["msgs"], env["logs"], env["pipe"]
    cid = _new_conv(client)
    base = _last(_ask(client, cid, "VIP 规则", "qa-70"), "done")
    lrid = base["logical_round_id"]
    execs = []
    for i in range(3):
        pipe.blocks = [{"path": f"v{i}.md", "chunk_id": f"c{i}", "content": "x", "feature_id": "vip"}]
        pipe.fail_generate = i == 2
        ev = _refresh(client, cid, lrid, f"rf-70-{i}")
        execs.append((_last(ev, "done") or _last(ev, "error"))["exec_id"])
    pipe.fail_generate = False
    current = [v for v in _assistants(msgs, cid, lrid) if v["is_current"]]
    assert [v["exec_id"] for v in current] == [execs[1]]
    pipe.same_topic = True
    pipe.calls.clear()
    done = _last(_ask(client, cid, "那保级呢", "qa-71"), "done")
    snap = logs.rows[done["exec_id"]]["snapshot"]
    assert snap["prev_exec_id"] == execs[1] != execs[2]
    prev = [p for name, p in pipe.calls if name == "rerank"][-1]
    assert [b["path"] for b in prev] == ["v1.md"]


def test_q08_cleared_round_cannot_refresh_and_legacy_snapshot_flagged(env):
    client, logs = env["client"], env["logs"]
    cid = _new_conv(client)
    a = _last(_ask(client, cid, "旧问题", "qa-80"), "done")
    b = _last(_ask(client, cid, "新问题", "qa-81"), "done")
    # M1 期间写的快照没有消息 id：退化读法并标明限制
    logs.rows[b["exec_id"]]["snapshot"].pop("l1_msg_ids")
    done = _last(_refresh(client, cid, b["logical_round_id"], "rf-80"), "done")
    assert logs.rows[done["exec_id"]]["snapshot"]["snapshot_limited"] == "legacy_snapshot"
    client.post(f"/api/kb/conversations/{cid}/clear")
    err = _last(_refresh(client, cid, a["logical_round_id"], "rf-81"), "error")
    assert err["type"] == "round_not_found"


def test_q08_client_wiring():
    assert "logical_round_id" in QA_JS
    assert "versions" in QA_JS and "viewIndex" in QA_JS
    assert "data-ver-step" in QA_JS
    assert "刷新失败，已保留原回答" in QA_JS


# ---------------- STEP-Q09 ----------------

def _flaky(monkeypatch, msgs, fail_times):
    real = msgs.append_assistant
    state = {"left": fail_times, "calls": 0}

    def wrapped(*a, **k):
        state["calls"] += 1
        if state["left"] != 0:
            state["left"] -= 1
            raise RuntimeError("db down")
        return real(*a, **k)

    monkeypatch.setattr(msgs, "append_assistant", wrapped)
    return state


def test_q09_first_retry_saves_same_result(env, monkeypatch):
    """AT-40：第一次补写成功，只更新保存状态，执行与业务结果不变。"""
    client, msgs, logs = env["client"], env["msgs"], env["logs"]
    cid = _new_conv(client)
    st = _flaky(monkeypatch, msgs, 1)
    done = _last(_ask(client, cid, "退款怎么扣", "qa-90"), "done")
    assert st["calls"] == 2
    assert done["msg_save"] == "saved" and done["save_blocked"] is False
    assert done["statuses"]["biz_result"] == "answered"
    row = logs.rows[done["exec_id"]]
    assert row["pending_reply"] is None
    assert [r["content"] for r in msgs.effective_messages(cid)] == ["退款怎么扣", "好的。"]
    assert env["convs"].save_block_of(cid) is None


def test_q09_all_retries_fail_blocks_conversation_then_retry_save(env, monkeypatch):
    """C40 / AT-28（保存部分）：补写全部失败 → 保存失败并阻塞该会话；另一设备不能发；重试保存后恢复。"""
    client, msgs, logs, pipe = env["client"], env["msgs"], env["logs"], env["pipe"]
    cid = _new_conv(client)
    other = _new_conv(client)
    st = _flaky(monkeypatch, msgs, -1)
    done = _last(_ask(client, cid, "VIP 保级扣什么", "qa-100"), "done")
    assert st["calls"] == 3
    assert done["msg_save"] == "failed" and done["save_blocked"] is True
    assert done["statuses"]["exec_state"] == "completed"
    carrier = logs.rows[done["exec_id"]]["pending_reply"]
    assert carrier["content"] == "好的。"
    assert client.get(f"/api/kb/conversations/{cid}").json()["saveBlockedExecId"] == done["exec_id"]

    pipe.calls.clear()
    device_b = TestClient(main.app)
    assert device_b.post("/api/kb/auth/login", json={"username": "alice", "password": "pw"}).status_code == 200
    err = _last(_ask(device_b, cid, "抢发", "qa-101"), "error")
    assert err["type"] == "save_blocked" and err["blocked_exec_id"] == done["exec_id"]
    assert pipe.calls == []
    assert _last(_ask(device_b, other, "别的会话", "qa-102"), "done")["status"] == "success"

    # 仍失败：阻塞保持
    fail = client.post(f"/api/kb/conversations/{cid}/retry-save", json={"exec_id": done["exec_id"]})
    assert fail.status_code == 503 and fail.json()["code"] == "retry_save_fail"
    monkeypatch.setattr(msgs, "append_assistant", MsgStore.append_assistant.__get__(msgs))
    ok = client.post(f"/api/kb/conversations/{cid}/retry-save", json={"exec_id": done["exec_id"]}).json()
    assert ok["ok"] is True and ok["assistant_msg_id"]
    assert [r["content"] for r in msgs.effective_messages(cid)] == ["VIP 保级扣什么", "好的。"]
    row = logs.rows[done["exec_id"]]
    assert row["msg_save"] == "saved" and row["assistant_msg_id"] == ok["assistant_msg_id"]
    assert row["status"] == "success" and row["biz_result"] == "answered"
    again = client.post(f"/api/kb/conversations/{cid}/retry-save").json()
    assert again["already"] is True
    assert len([r for r in msgs.effective_messages(cid) if r["role"] == "assistant"]) == 1
    assert _last(_ask(client, cid, "继续问", "qa-103"), "done")["status"] == "success"


def test_q09_refresh_save_fail_keeps_old_default_until_retry(env, monkeypatch):
    client, msgs, pipe = env["client"], env["msgs"], env["pipe"]
    cid = _new_conv(client)
    base = _last(_ask(client, cid, "退款规则", "qa-110"), "done")
    lrid = base["logical_round_id"]
    pipe.answer = "刷新后的答案"
    _flaky(monkeypatch, msgs, -1)
    done = _last(_refresh(client, cid, lrid, "rf-110"), "done")
    assert done["save_blocked"] is True
    assert [v["id"] for v in _assistants(msgs, cid, lrid) if v["is_current"]] == [base["assistant_msg_id"]]
    monkeypatch.setattr(msgs, "append_assistant", MsgStore.append_assistant.__get__(msgs))
    ok = client.post(f"/api/kb/conversations/{cid}/retry-save").json()
    assert ok["ok"] is True and ok["adopted"] is True and ok["version_no"] == 2
    current = [v for v in _assistants(msgs, cid, lrid) if v["is_current"]]
    assert [v["content"] for v in current] == ["刷新后的答案"]


def test_q09_carrier_lost_unblocks_without_regenerating(env, monkeypatch):
    client, msgs, logs, pipe = env["client"], env["msgs"], env["logs"], env["pipe"]
    cid = _new_conv(client)
    _flaky(monkeypatch, msgs, -1)
    done = _last(_ask(client, cid, "问题", "qa-120"), "done")
    main._PENDING_REPLIES.clear()
    logs.rows[done["exec_id"]]["pending_reply"] = None
    calls = len(pipe.calls)
    res = client.post(f"/api/kb/conversations/{cid}/retry-save").json()
    assert res["code"] == "save_source_lost" and res["unblocked"] is True
    assert len(pipe.calls) == calls
    assert logs.rows[done["exec_id"]]["error_type"] == "save_source_lost"
    assert env["convs"].save_block_of(cid) is None


def test_q09_block_kept_in_process_when_db_write_fails(env, monkeypatch):
    client, convs, msgs = env["client"], env["convs"], env["msgs"]
    cid = _new_conv(client)

    def broken(*a, **k):
        raise RuntimeError("db down")

    monkeypatch.setattr(convs.repo, "set_block", broken)
    _flaky(monkeypatch, msgs, -1)
    done = _last(_ask(client, cid, "问题", "qa-130"), "done")
    assert convs.acquire_run(cid, "x") == ("blocked", done["exec_id"])


def test_q09_client_wiring():
    assert "retry-save" in QA_JS
    assert "重试保存" in QA_JS
    assert '"save_blocked"' in QA_JS
    assert "save_block_exec_id VARCHAR(64) NULL" in INIT_SQL
    assert "pending_reply JSON NULL" in INIT_SQL


# ---------------- STEP-Q21 ----------------

def test_q21_feedback_bound_per_version(env):
    """AT-31：刷新前踩、刷新后赞，两个版本的反馈分别保存，新版不继承旧版。"""
    client, logs = env["client"], env["logs"]
    cid = _new_conv(client)
    base = _last(_ask(client, cid, "VIP 保级", "qa-140"), "done")
    assert client.post(f"/api/kb/rounds/{base['exec_id']}/feedback", json={"feedback": "down"}).status_code == 200
    new = _last(_refresh(client, cid, base["logical_round_id"], "rf-140"), "done")
    assert logs.rows[new["exec_id"]].get("feedback") is None
    assert client.post(f"/api/kb/rounds/{new['exec_id']}/feedback", json={"feedback": "up"}).status_code == 200
    assert logs.rows[base["exec_id"]]["feedback"] == "down"
    assert logs.rows[new["exec_id"]]["feedback"] == "up"


def test_q21_technical_error_and_unsaved_not_rateable(env, monkeypatch):
    """RQ-14：纯技术错误回复不开放赞踩；未保存的回复也不接受反馈。"""
    client, pipe, msgs = env["client"], env["pipe"], env["msgs"]
    cid = _new_conv(client)
    pipe.fail_generate = True
    err = _last(_ask(client, cid, "问题", "qa-150"), "error")
    res = client.post(f"/api/kb/rounds/{err['exec_id']}/feedback", json={"feedback": "up"})
    assert res.status_code == 409 and res.json()["code"] == "feedback_not_allowed"
    pipe.fail_generate = False
    cid2 = _new_conv(client)
    _flaky(monkeypatch, msgs, -1)
    done = _last(_ask(client, cid2, "问题", "qa-151"), "done")
    assert client.post(f"/api/kb/rounds/{done['exec_id']}/feedback", json={"feedback": "up"}).status_code == 409


def test_q21_heat_only_counts_actual_knowledge_calls():
    """AT-24：ack 等未实际调用知识的执行不进热度、也不加未归类；旧记录按旧口径计入并单列。"""
    rows = [
        {"schema_ver": 2, "used_knowledge_rag": 1, "c_gen": [{"feature_id": "vip"}, {"feature_id": "vip"}]},
        {"schema_ver": 2, "used_knowledge_rag": 0, "c_gen": []},
        {"schema_ver": 2, "used_knowledge_rag": 1, "c_gen": []},
        {"c_gen": [{"feature_id": "referral"}]},
        {"c_gen": []},
    ]
    data = LogStore.aggregate_heat(rows)
    items = {i["feature_id"]: i for i in data["items"]}
    assert items["vip"]["count"] == 1 and items["vip"]["legacy_count"] == 0
    assert items["referral"]["count"] == 1 and items["referral"]["legacy_count"] == 1
    assert data["unclassified"] == 2
    assert data["unclassified_legacy"] == 1
    assert data["legacy_rows"] == 2


def test_q21_client_feedback_uses_viewed_version():
    assert "feedback_not_allowed" in QA_JS
