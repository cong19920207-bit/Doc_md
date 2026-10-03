# -*- coding: utf-8 -*-
"""多轮编排 M1：服务端消息事实源、Runtime 多维状态、会话隐藏、清空边界、服务端 L1。"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import main, msg_store
from app.auth_store import ROLE_USER_ID, AuthStore, MemoryAuthRepo
from app.conv_store import ConvStore, MemoryConvRepo
from app.msg_store import MemoryMsgRepo, MsgStore

ROOT = Path(__file__).resolve().parents[3]
INIT_SQL = (ROOT / "site" / "kb-api" / "sql" / "init.sql").read_text(encoding="utf-8")
QA_JS = (ROOT / "site" / "feature-interaction" / "qa.js").read_text(encoding="utf-8")


class FakeLogs:
    """替身执行日志：记录每次写入，可按需模拟 insert / 最终 update 失败。"""

    def __init__(self) -> None:
        self.rows: dict[str, dict] = {}
        self.fail_insert = False
        self.fail_final_update = False
        self.last_error = None

    def insert_running(self, row: dict) -> bool:
        if self.fail_insert:
            return False
        self.rows[row["round_id"]] = dict(row)
        return True

    def update_round(self, round_id: str, fields: dict) -> bool:
        if self.fail_final_update and "status" in fields:
            return False
        self.rows.setdefault(round_id, {}).update(fields)
        return True

    def get_round(self, round_id: str) -> dict | None:
        row = self.rows.get(round_id)
        return dict(row) if row else None

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
    with TestClient(main.app) as client:
        assert client.post("/api/kb/auth/login", json={"username": "alice", "password": "pw"}).status_code == 200
        yield {"client": client, "convs": convs, "msgs": msgs, "logs": logs, "pipe": pipe, "auth": auth}


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


# ---------------- STEP-Q01 ----------------

def test_q01_init_sql_has_message_table():
    assert "CREATE TABLE IF NOT EXISTS kb_conv_messages" in INIT_SQL
    assert "UNIQUE KEY uk_conv_msg_req (conv_id, client_request_id)" in INIT_SQL
    assert "UNIQUE KEY uk_conv_msg_seq (conv_id, seq)" in INIT_SQL
    assert "CREATE TABLE IF NOT EXISTS kb_conv_clears" in INIT_SQL
    assert "last_seq BIGINT NOT NULL DEFAULT 0" in INIT_SQL
    assert "client_request_id" in QA_JS
    assert 'op_type: "refresh"' in QA_JS
    assert '"user_save_fail"' in QA_JS


def test_q01_ack_user_and_assistant_both_saved(env):
    """CSTR-Q01：发送「谢谢」得到回复，User、Assistant 两条都落库。"""
    client, msgs = env["client"], env["msgs"]
    cid = _new_conv(client)
    ev = _ask(client, cid, "谢谢", "q-1")
    accepted = _last(ev, "accepted")
    done = _last(ev, "done")
    assert accepted and done
    rows = msgs.effective_messages(cid)
    assert [r["role"] for r in rows] == ["user", "assistant"]
    assert rows[0]["content"] == "谢谢"
    assert rows[1]["content"] == "好的。"
    assert rows[0]["round_id"] == rows[1]["round_id"] == accepted["logical_round_id"]
    assert rows[0]["id"] == accepted["user_msg_id"] == done["user_msg_id"]
    assert rows[1]["id"] == done["assistant_msg_id"]
    assert done["msg_save"] == "saved"
    # 逻辑回合不是旧 qa_rounds.round_id
    assert done["logical_round_id"] != done["round_id"]


def test_q01_refuse_reply_also_saved(env):
    """不按结果类型筛选：0 块拒答的回复同样写入。"""
    client, msgs, pipe = env["client"], env["msgs"], env["pipe"]
    pipe.blocks = []
    cid = _new_conv(client)
    ev = _ask(client, cid, "未写的问题", "q-2")
    assert _last(ev, "done")["status"] == "empty"
    rows = msgs.effective_messages(cid)
    assert [r["role"] for r in rows] == ["user", "assistant"]
    assert rows[1]["completeness"] == "complete"


def test_q01_user_save_fail_no_model_and_retry_single_round(env, monkeypatch):
    """AT-27：User 写失败不调模型；重试不产生两个逻辑回合。"""
    client, msgs, pipe = env["client"], env["msgs"], env["pipe"]
    cid = _new_conv(client)
    real_insert = msgs.repo.insert

    def broken(row):
        raise RuntimeError("db down")

    monkeypatch.setattr(msgs.repo, "insert", broken)
    ev = _ask(client, cid, "VIP 怎么保级", "q-3")
    err = _last(ev, "error")
    assert err["type"] == "user_save_fail"
    assert _last(ev, "accepted") is None
    assert pipe.calls == []
    assert msgs.effective_messages(cid) == []

    monkeypatch.setattr(msgs.repo, "insert", real_insert)
    ev = _ask(client, cid, "VIP 怎么保级", "q-3")
    assert _last(ev, "accepted") is not None
    assert _last(ev, "done") is not None
    model_calls = len(pipe.calls)

    ev = _ask(client, cid, "VIP 怎么保级", "q-3")
    dup = _last(ev, "error")
    assert dup["type"] == "duplicate_request"
    assert dup["existing"]["user_msg_id"]
    assert len(pipe.calls) == model_calls
    rows = msgs.effective_messages(cid)
    assert [r["role"] for r in rows].count("user") == 1
    assert len({r["round_id"] for r in rows}) == 1


def test_q01_same_timestamp_order_stable(monkeypatch):
    """同一时间戳的多条消息：服务端 seq 唯一，读取顺序稳定。"""
    fixed = datetime(2026, 9, 29, 12, 0, 0)
    monkeypatch.setattr(msg_store, "_now", lambda: fixed)
    store = MsgStore(MemoryMsgRepo())
    u1 = store.append_user("c1", "第一句", "a", "e1")
    a1 = store.append_assistant("c1", u1, "e1", "答一", "complete")
    u2 = store.append_user("c1", "第二句", "b", "e2")
    rows = store.effective_messages("c1")
    assert [r["id"] for r in rows] == [u1["id"], a1["id"], u2["id"]]
    assert len({r["seq"] for r in rows}) == 3
    assert len({str(r["created_at"]) for r in rows}) == 1
    assert store.effective_messages("c1") == rows


def test_q01_unknown_conversation_rejected_before_model(env):
    client, pipe = env["client"], env["pipe"]
    ev = _ask(client, "c-not-mine", "你好", "q-4")
    assert _last(ev, "error")["type"] == "conversation_not_found"
    assert pipe.calls == []


def test_q02_normal_exec_six_statuses_separate(env):
    """AT-32：一次正常执行，同一 EXEC_ID 上六类状态各自有值，不合并成一个 success。"""
    client, logs = env["client"], env["logs"]
    cid = _new_conv(client)
    done = _last(_ask(client, cid, "VIP 保级规则", "q-10"), "done")
    st = done["statuses"]
    assert st == {
        "biz_result": "answered",
        "exec_state": "completed",
        # STEP-Q19 起知识回答实际做证据检查（替身检查器通过）
        "check_status": "pass",
        "text_integrity": "complete",
        "msg_save": "saved",
        "runtime_save": "saved",
    }
    row = logs.rows[done["exec_id"]]
    assert row["schema_ver"] == 2
    assert row["op_type"] == "send"
    assert row["logical_round_id"] == done["logical_round_id"]
    assert row["user_msg_id"] == done["user_msg_id"]
    assert row["assistant_msg_id"] == done["assistant_msg_id"]
    assert row["used_knowledge_rag"] is True
    assert row["runtime_save"] == "saved"
    # 旧 status 照写，旧反馈/热度不受影响
    assert row["status"] == "success"


def test_q02_final_update_fail_runtime_partial_msg_saved(env):
    """AT-15：insert 成功、最终 update 失败 → Runtime 局部，消息保存保持自己的结果。"""
    client, logs = env["client"], env["logs"]
    logs.fail_final_update = True
    cid = _new_conv(client)
    done = _last(_ask(client, cid, "退款怎么扣", "q-11"), "done")
    assert done["statuses"]["runtime_save"] == "partial"
    assert done["statuses"]["msg_save"] == "saved"
    assert logs.rows[done["exec_id"]]["runtime_save"] == "partial"


def test_q02_insert_fail_runtime_failed(env):
    client, logs = env["client"], env["logs"]
    logs.fail_insert = True
    cid = _new_conv(client)
    done = _last(_ask(client, cid, "退款怎么扣", "q-12"), "done")
    assert done["log_written"] is False
    assert done["statuses"]["runtime_save"] == "failed"
    assert done["statuses"]["msg_save"] == "saved"


def test_q02_msg_save_fail_with_answer_kept_separate(env, monkeypatch):
    """AT-32 边界：业务已回答而消息保存失败，两项分别记录。"""
    client, msgs = env["client"], env["msgs"]
    cid = _new_conv(client)
    real_append = msgs.append_assistant

    def broken(*a, **k):
        raise RuntimeError("db down")

    monkeypatch.setattr(msgs, "append_assistant", broken)
    done = _last(_ask(client, cid, "VIP 保级", "q-13"), "done")
    monkeypatch.setattr(msgs, "append_assistant", real_append)
    st = done["statuses"]
    assert st["biz_result"] == "answered"
    assert st["msg_save"] == "failed"
    assert st["runtime_save"] == "saved"
    assert done["assistant_msg_id"] is None


def test_q02_status_columns_independent_and_legacy_unknown():
    """AT-32 存储层：检查 pass、业务部分、消息失败三项互不覆盖；旧记录无 schema_ver 读为未知。"""
    from app.logs import runtime_statuses, sanitize_runtime_fields

    fields = sanitize_runtime_fields({
        "schema_ver": 2,
        "check_status": "pass",
        "biz_result": "partial",
        "msg_save": "failed",
        "exec_state": "bogus",
    })
    assert fields["check_status"] == "pass"
    assert fields["biz_result"] == "partial"
    assert fields["msg_save"] == "failed"
    assert "exec_state" not in fields
    row = dict(fields)
    st = runtime_statuses(row)
    assert (st["check_status"], st["biz_result"], st["msg_save"]) == ("pass", "partial", "failed")
    assert st["exec_state"] is None
    legacy = runtime_statuses({"status": "success", "round_id": "old"})
    assert all(v is None for v in legacy.values())
    assert "biz_result VARCHAR(24) NULL" in INIT_SQL
    assert "runtime_save VARCHAR(16) NULL" in INIT_SQL


# ---------------- STEP-Q03 ----------------

def _all_pages(client, limit):
    seen, pages, offset = [], 0, 0
    while offset is not None:
        data = client.get(f"/api/kb/conversations?offset={offset}&limit={limit}").json()
        seen.extend(x["id"] for x in data["items"])
        offset = data["next_offset"]
        pages += 1
    return seen, pages


def test_q03_41st_conversation_keeps_all(env):
    """AT-12：已有 40 个会话 S，再建第 41 个，S 仍全部可翻到。"""
    client = env["client"]
    s = {_new_conv(client) for _ in range(40)}
    extra = _new_conv(client)
    ids, _pages = _all_pages(client, 50)
    assert s <= set(ids)
    assert extra in ids
    assert len(ids) == 41
    assert "MAX_CONVS" not in QA_JS
    assert "data-conv-more" in QA_JS


def test_q03_pages_union_equals_all_visible(env):
    """AT-12 边界：各页 CONV_SET 并集 = 全部未隐藏会话，不因页大小截掉旧 id。"""
    client = env["client"]
    made = {_new_conv(client) for _ in range(23)}
    ids, pages = _all_pages(client, 5)
    assert pages == 5
    assert len(ids) == len(set(ids))
    assert set(ids) == made
    big = client.get("/api/kb/conversations?limit=100000").json()
    assert len(big["items"]) == 23
    assert big["next_offset"] is None


def test_q03_page_size_clamped():
    from app.conv_store import PAGE_DEFAULT, PAGE_MAX, clamp_page

    assert clamp_page(None, None) == (0, PAGE_DEFAULT)
    assert clamp_page(-3, 999999) == (0, PAGE_MAX)
    assert clamp_page("x", "y") == (0, PAGE_DEFAULT)


def test_q03_user_delete_hides_across_devices_keeps_data(env):
    """C26：用户删除后另一设备登录不可见，直接 GET 也不可访问；数据库保留。"""
    client, convs, msgs = env["client"], env["convs"], env["msgs"]
    cid = _new_conv(client)
    _ask(client, cid, "留痕的一问", "q-20")
    assert client.delete(f"/api/kb/conversations/{cid}").status_code == 200

    other = TestClient(main.app)
    assert other.post("/api/kb/auth/login", json={"username": "alice", "password": "pw"}).status_code == 200
    listed = {x["id"] for x in other.get("/api/kb/conversations").json()["items"]}
    assert cid not in listed
    assert other.get(f"/api/kb/conversations/{cid}").status_code == 404
    assert other.put(f"/api/kb/conversations/{cid}", json={"title": "复活"}).status_code == 404
    assert other.delete(f"/api/kb/conversations/{cid}").status_code == 404
    ev = _ask(other, cid, "还能问吗", "q-21")
    assert _last(ev, "error")["type"] == "conversation_not_found"

    raw = convs.repo.get(cid)
    assert raw is not None and raw.get("hidden_at")
    assert len(msgs.repo.list_range(cid, 0, 0, None)) == 2
    admin_ids = {x["id"] for x in convs.list_all_public()}
    assert cid in admin_ids


# ---------------- STEP-Q04 ----------------

def test_q04_clear_boundary_other_device_and_new_question(env):
    """AT-11：清空后另一设备只见边界之后；清空后完整业务问题照常查询。"""
    client, msgs, pipe = env["client"], env["msgs"], env["pipe"]
    cid = _new_conv(client)
    _ask(client, cid, "VIP 保级扣什么", "q-30")
    cleared = client.post(f"/api/kb/conversations/{cid}/clear")
    assert cleared.status_code == 200
    assert cleared.json()["clear_seq"] == 2

    other = TestClient(main.app)
    assert other.post("/api/kb/auth/login", json={"username": "alice", "password": "pw"}).status_code == 200
    assert other.get(f"/api/kb/conversations/{cid}/messages").json()["items"] == []

    pipe.calls.clear()
    ev = _ask(client, cid, "退款后财富值怎么扣", "q-31")
    assert _last(ev, "done")["status"] == "success"
    assert any(name == "retrieve" for name, _ in pipe.calls)
    items = other.get(f"/api/kb/conversations/{cid}/messages").json()["items"]
    assert [m["content"] for m in items] == ["退款后财富值怎么扣", "好的。"]
    assert all(m["seq"] > 2 for m in items)
    # 清空前消息仍在库中
    assert len(msgs.repo.list_range(cid, 0, 0, None)) == 4


def test_q04_late_reply_of_pre_clear_round_stays_hidden():
    """G-E06-2：清空前开始的执行晚到结果照常落库，但不进入有效范围。"""
    store = MsgStore(MemoryMsgRepo())
    u1 = store.append_user("c1", "清空前的问题", "a", "e1")
    boundary = store.clear("c1", "acc")
    assert boundary == u1["seq"]
    late = store.append_assistant("c1", u1, "e1", "晚到的回答", "complete")
    assert late["seq"] > boundary
    assert store.effective_messages("c1") == []
    assert len(store.repo.list_range("c1", 0, 0, None)) == 2
    u2 = store.append_user("c1", "清空后的问题", "b", "e2")
    assert [r["id"] for r in store.effective_messages("c1")] == [u2["id"]]


def test_q04_multiple_clears_kept_and_endpoints_guarded(env):
    client, msgs = env["client"], env["msgs"]
    cid = _new_conv(client)
    _ask(client, cid, "一", "q-32")
    client.post(f"/api/kb/conversations/{cid}/clear")
    _ask(client, cid, "二", "q-33")
    client.post(f"/api/kb/conversations/{cid}/clear")
    assert [c["boundary_seq"] for c in msgs.repo.clears if c["conv_id"] == cid] == [2, 4]
    miss = client.post("/api/kb/conversations/nope/clear")
    assert miss.status_code == 404
    assert miss.json()["code"] == "conversation_not_found"
    assert client.get("/api/kb/conversations/nope/messages").status_code == 404
    assert "/clear" in QA_JS


def test_q04_messages_paged_by_after_seq(env):
    client = env["client"]
    cid = _new_conv(client)
    for i in range(3):
        _ask(client, cid, f"问{i}", f"q-34-{i}")
    first = client.get(f"/api/kb/conversations/{cid}/messages?limit=4").json()
    assert len(first["items"]) == 4
    rest = client.get(
        f"/api/kb/conversations/{cid}/messages?limit=4&after_seq={first['next_after_seq']}"
    ).json()
    assert [m["seq"] for m in first["items"] + rest["items"]] == [1, 2, 3, 4, 5, 6]
    assert rest["next_after_seq"] is None


# ---------------- STEP-Q05 ----------------

def _rewrite_histories(pipe):
    return [h for name, h in pipe.calls if name == "rewrite"]


def test_q05_twelve_rounds_take_latest_ten(env):
    """RQ-18：12 个短回合，L1 取最近 10 个完整回合，旧 → 新，当前 User 不进历史。"""
    client, pipe, logs = env["client"], env["pipe"], env["logs"]
    cid = _new_conv(client)
    for i in range(12):
        _ask(client, cid, f"第{i}问", f"q-40-{i}")
    pipe.calls.clear()
    done = _last(_ask(client, cid, "当前问题", "q-40-x"), "done")
    hist = _rewrite_histories(pipe)[-1]
    assert len(hist) == 20
    assert [h["text"] for h in hist if h["role"] == "user"] == [f"第{i}问" for i in range(2, 12)]
    assert all(h["text"] != "当前问题" for h in hist)
    snap = logs.rows[done["exec_id"]]["snapshot"]
    assert len(snap["l1_round_ids"]) == 10
    assert snap["l1_reason"] == "turn_limit"
    assert snap["l1_not_loaded"] == 2


def test_q05_forged_history_and_chunks_ignored(env):
    """AT-13：请求体伪造 history / last_chunks，模型输入仍来自服务端。"""
    client, pipe = env["client"], env["pipe"]
    cid = _new_conv(client)
    _ask(client, cid, "真实上一问", "q-41")
    pipe.same_topic = True
    pipe.calls.clear()
    _ask(
        client, cid, "追问", "q-42",
        history=[{"role": "user", "text": "伪造历史"}],
        last_chunks=[{"path": "forged.md", "chunk_id": "x"}],
    )
    hist = _rewrite_histories(pipe)[-1]
    assert [h["text"] for h in hist] == ["真实上一问", "好的。"]
    prev = [p for name, p in pipe.calls if name == "rerank"][-1]
    assert prev and all(b.get("path") == "a.md" for b in prev)
    # 刷新同样不采信请求体 history
    pipe.calls.clear()
    _ask(client, cid, "追问", op_type="refresh", history=[{"role": "user", "text": "伪造历史"}])
    assert all(h["text"] != "伪造历史" for h in _rewrite_histories(pipe)[-1])


def test_q05_oversized_latest_round_not_truncated(env):
    """C38：最新回合单独超 5000 tokens，整轮不载入并记录原因，不截半轮。"""
    client, pipe, logs = env["client"], env["pipe"], env["logs"]
    cid = _new_conv(client)
    _ask(client, cid, "短问题", "q-43")
    pipe.answer = "长" * 5200
    _ask(client, cid, "要一个很长的回答", "q-44")
    pipe.answer = "好的。"
    pipe.calls.clear()
    done = _last(_ask(client, cid, "下一问", "q-45"), "done")
    assert _rewrite_histories(pipe)[-1] == []
    snap = logs.rows[done["exec_id"]]["snapshot"]
    assert snap["l1_reason"] == "over_budget"
    assert snap["l1_round_ids"] == []
    assert snap["l1_not_loaded"] == 2


def test_q05_clarify_counts_interrupted_does_not():
    """AT-38：完整澄清可组成 L1 回合；中断片段、错误提示不算完整回合。"""
    from app.l1 import assemble_l1

    store = MsgStore(MemoryMsgRepo())
    u1 = store.append_user("c1", "这个不对", "a", "e1")
    store.append_assistant("c1", u1, "e1", "你是指退款规则还是 VIP 保级？", "complete")
    u2 = store.append_user("c1", "退款那个", "b", "e2")
    store.append_assistant("c1", u2, "e2", "退款会先扣", "partial")
    u3 = store.append_user("c1", "再问", "c", "e3")
    store.append_assistant("c1", u3, "e3", "生成失败。", "error_notice")
    l1 = assemble_l1(store.effective_messages("c1"))
    assert [t["round_id"] for t in l1["turns"]] == [u1["round_id"]]
    assert l1["incomplete"] == 2


def test_q05_token_estimate_and_budget_boundary():
    from app.l1 import assemble_l1, count_tokens

    assert count_tokens("中文abcd") == 3
    assert count_tokens("") == 0
    store = MsgStore(MemoryMsgRepo())
    for i in range(3):
        u = store.append_user("c1", "问" * 1000, f"r{i}", f"e{i}")
        store.append_assistant("c1", u, f"e{i}", "答" * 1000, "complete")
    l1 = assemble_l1(store.effective_messages("c1"))
    # 每轮 2000 tokens：只能整轮放下 2 轮
    assert len(l1["turns"]) == 2
    assert l1["tokens"] == 4000
    assert l1["reason"] == "over_budget"


def test_q05_clear_cuts_l1_context(env):
    """AT-11（L1 部分）：讨论 VIP 后清空，再问「那退款呢」，模型输入不含清空前语境。"""
    client, pipe = env["client"], env["pipe"]
    cid = _new_conv(client)
    _ask(client, cid, "VIP 保级扣财富值吗", "q-46")
    client.post(f"/api/kb/conversations/{cid}/clear")
    pipe.same_topic = True
    pipe.calls.clear()
    _ask(client, cid, "那退款呢", "q-47")
    hist = _rewrite_histories(pipe)[-1]
    assert hist == []
    prev = [p for name, p in pipe.calls if name == "rerank"][-1]
    assert prev == []


def test_q01_refresh_does_not_forge_user(env):
    client, msgs = env["client"], env["msgs"]
    cid = _new_conv(client)
    _ask(client, cid, "第一问", "q-5")
    before = msgs.effective_messages(cid)
    ev = _ask(client, cid, "第一问", op_type="refresh")
    assert _last(ev, "done") is not None
    after = msgs.effective_messages(cid)
    assert [r["role"] for r in after].count("user") == 1
    assert len(after) == len(before)
