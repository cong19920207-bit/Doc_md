# -*- coding: utf-8 -*-
"""M4 后台只读观测：A05 会话列表与详情。"""
from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import main
from app.auth_store import ROLE_USER_ID, AuthStore, MemoryAuthRepo
from app.conv_store import ConvStore, MemoryConvRepo
from app.diag import DiagLog
from app.msg_store import MemoryMsgRepo, MsgStore
from tests.test_m2_exec_versions import FakeLogs, FakePipeline, _events, _flaky, _last

ROOT = Path(__file__).resolve().parents[3]
ADMIN_JS = (ROOT / "site" / "kb-admin" / "admin.js").read_text(encoding="utf-8")


def _section(marker: str) -> str:
    return ADMIN_JS.split(marker)[1].split("/* ----------")[0]


class ObserveLogs(FakeLogs):
    """在 M2 替身上补反馈时间与反馈分页（与 LogStore.page_feedback 同口径）。"""

    def __init__(self) -> None:
        super().__init__()
        self.tick = 0
        self.ping_ok = True
        self.fail_insert = False
        self.fail_final_update = False

    def ping(self) -> bool:
        return self.ping_ok

    def insert_running(self, row):
        if self.fail_insert:
            return False
        from datetime import datetime as _dt

        ok = super().insert_running(row)
        self.rows[row["round_id"]].setdefault("created_at", _dt.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3])
        return ok

    # 与 LogStore.overview_counts 的 SQL 同口径（内存实现，仅供测试）
    def _in_range(self, r, start, end):
        from app.listing import time_key

        ts = time_key(r.get("created_at"))
        return time_key(start) <= ts < time_key(end)

    def overview_counts(self, start, end):
        rows = [r for r in self.rows.values() if self._in_range(r, start, end)]
        acc = [r for r in rows if r.get("schema_ver") and r.get("logical_round_id")]
        term = ("completed", "failed", "interrupted")
        queue = [r for r in acc if r.get("msg_save") == "saved" and r.get("assistant_msg_id")
                 and r.get("status") in ("success", "refuse", "empty")]

        def group(key, items):
            out = {}
            for r in items:
                out[r.get(key)] = out.get(r.get(key), 0) + 1
            return out

        from app.listing import time_key

        def ms(r):
            from datetime import datetime as _dt
            fmt = "%Y-%m-%d %H:%M:%S.%f"
            return (_dt.strptime(time_key(r["finished_at"]), fmt) - _dt.strptime(time_key(r["created_at"]), fmt)).total_seconds() * 1000

        return {
            "total": len(rows),
            "legacy_rows": sum(1 for r in rows if not r.get("schema_ver")),
            "rejected": sum(1 for r in rows if r.get("schema_ver") and not r.get("logical_round_id")),
            "execs": len(acc),
            "refresh": sum(1 for r in acc if r.get("op_type") == "refresh"),
            "op_unknown": sum(1 for r in acc if r.get("op_type") is None),
            "new_rounds": len({r["logical_round_id"] for r in acc if r.get("op_type") == "send"}),
            "active_accounts": len({r.get("user_id") for r in acc if r.get("op_type") == "send"}),
            "kn_yes": sum(1 for r in acc if r.get("used_knowledge_rag") in (1, True)),
            "kn_no": sum(1 for r in acc if r.get("used_knowledge_rag") in (0, False)),
            "kn_unknown": sum(1 for r in acc if r.get("used_knowledge_rag") is None),
            "ms_saved": sum(1 for r in acc if r.get("msg_save") == "saved"),
            "ms_failed_final": sum(1 for r in acc if r.get("msg_save") == "failed" and not r.get("pending_reply")),
            "ms_failed_pending": sum(1 for r in acc if r.get("msg_save") == "failed" and r.get("pending_reply")),
            "ms_pending": sum(1 for r in acc if r.get("msg_save") == "pending"),
            "ms_na": sum(1 for r in acc if r.get("msg_save") == "not_applicable"),
            "ms_unknown": sum(1 for r in acc if r.get("msg_save") is None),
            "rt_partial": sum(1 for r in acc if r.get("runtime_save") == "partial"),
            "dur_unknown": sum(1 for r in acc if r.get("exec_state") in term and not r.get("finished_at")),
            "fb_queue": len(queue),
            "fb_up": sum(1 for r in queue if r.get("feedback") == "up"),
            "fb_down": sum(1 for r in queue if r.get("feedback") == "down"),
            "route": group("route", acc),
            "exec_state": group("exec_state", acc),
            "biz": group("biz_result", [r for r in acc if r.get("exec_state") in term]),
            "durations_ms": [ms(r) for r in acc if r.get("exec_state") in term and r.get("finished_at")],
        }

    def heat_rows(self, start, end, limit):
        from app.listing import time_key

        rows = [dict(r, round_id=rid) for rid, r in self.rows.items() if self._in_range(r, start, end)]
        rows.sort(key=lambda r: (time_key(r.get("created_at")), r["round_id"]), reverse=True)
        return rows[: limit + 1]

    def update_round(self, round_id, fields):
        if self.fail_final_update and "status" in fields:
            return False
        return super().update_round(round_id, fields)

    def set_feedback(self, round_id, feedback):
        res = super().set_feedback(round_id, feedback)
        if res == "ok":
            self.tick += 1
            self.rows[round_id]["feedback_at"] = f"2026-09-29 10:00:{self.tick:02d}.000"
        return res

    def page_feedback(self, *, value="down", time_col="feedback_at", rng=None, user_id="", conv_id="",
                      exec_id="", msg_id="", route="", before=None, size=50):
        from app.listing import time_key

        col = "created_at" if time_col == "created_at" else "feedback_at"
        items = []
        for rid, r in self.rows.items():
            if not r.get("feedback"):
                continue
            if value in ("up", "down") and r["feedback"] != value:
                continue
            if user_id and r.get("user_id") != user_id:
                continue
            if conv_id and r.get("conv_id") != conv_id:
                continue
            if exec_id and rid != exec_id:
                continue
            if msg_id and r.get("assistant_msg_id") != msg_id:
                continue
            if route and r.get("route") != route:
                continue
            items.append(dict(r, round_id=rid))
        items.sort(key=lambda r: (time_key(r.get(col)), r["round_id"]), reverse=True)
        if before:
            items = [r for r in items if (time_key(r.get(col)), r["round_id"]) < before]
        return items[:size], len(items) > size


async def _noop_index():
    return None


@pytest.fixture
def env(monkeypatch, tmp_path):
    auth = AuthStore(MemoryAuthRepo())
    auth.ensure_schema()
    auth.bootstrap_if_empty("admin", "secret")
    auth.create_account("alice", "pw", ROLE_USER_ID)
    convs = ConvStore(MemoryConvRepo())
    msgs = MsgStore(MemoryMsgRepo())
    logs = ObserveLogs()
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
    diag = DiagLog(tmp_path / "data")
    monkeypatch.setattr(main, "diag", diag)
    monkeypatch.setattr(main.tls, "root", tmp_path / "tls")
    with TestClient(main.app) as user:
        assert user.post("/api/kb/auth/login", json={"username": "alice", "password": "pw"}).status_code == 200
        admin = TestClient(main.app)
        assert admin.post("/api/kb/auth/login", json={"username": "admin", "password": "secret"}).status_code == 200
        yield {"user": user, "admin": admin, "auth": auth, "convs": convs, "msgs": msgs, "logs": logs, "pipe": pipe,
               "diag": diag, "tmp": tmp_path}


def _conv(client, title="t", **body) -> str:
    return client.post("/api/kb/conversations", json={"title": title, **body}).json()["id"]


def _ask(client, cid, query, crid):
    return _last(_events(client.post("/api/kb/ask", json={
        "conversation_id": cid, "query": query, "client_request_id": crid,
    }).text), "done")


def _refresh(client, cid, lrid, crid):
    ev = _events(client.post("/api/kb/ask", json={
        "conversation_id": cid, "op_type": "refresh", "logical_round_id": lrid, "client_request_id": crid,
    }).text)
    return _last(ev, "done") or _last(ev, "error")


def _pages(admin, **params):
    ids, pages, cursor = [], 0, ""
    while True:
        qp = dict(params)
        if cursor:
            qp["cursor"] = cursor
        data = admin.get("/api/kb/admin/conversations", params=qp).json()
        ids.extend(x["id"] for x in data["items"])
        pages += 1
        if not data["has_more"]:
            return ids, pages, data
        cursor = data["next_cursor"]


def _detail(admin, cid):
    res = admin.get(f"/api/kb/admin/conversations/{cid}")
    assert res.status_code == 200, res.text
    return res.json()


# ---------------- STEP-A05 ----------------

def test_a05_t01_keyword_hits_old_version_beyond_first_page(env):
    """T01：关键词按真实匹配集在服务端筛选，命中旧版本回复并给出消息/版本定位，不只查最近一页。"""
    user, admin, pipe = env["user"], env["admin"], env["pipe"]
    old = _conv(user, "很早的会话")
    pipe.answer = "旧回复：保级扣 ZXQ 财富值"
    base = _ask(user, old, "VIP 保级", "k-1")
    pipe.answer = "新回复"
    _refresh(user, old, base["logical_round_id"], "k-rf")
    for i in range(12):
        _ask(user, _conv(user, f"新会话{i}"), f"问{i}", f"k-n{i}")
    first = admin.get("/api/kb/admin/conversations", params={"page_size": 5}).json()
    assert old not in {x["id"] for x in first["items"]}
    ids, _pages_n, data = _pages(admin, q="ZXQ", page_size=5)
    assert ids == [old]
    hit = data["items"][0]["hits"][0]
    assert hit["msg_id"] == base["assistant_msg_id"]
    assert hit["version_no"] == 1 and hit["is_current"] is False
    assert "ZXQ" in hit["excerpt"]
    assert data["coverage"]["complete"] is True


def test_a05_t02_hidden_conversation_readable_without_restore(env):
    """T02：用户已隐藏的会话，管理员可查阅，标「用户侧已移除」，没有恢复入口。"""
    user, admin = env["user"], env["admin"]
    cid = _conv(user, "要删的")
    _ask(user, cid, "留痕", "h-1")
    assert user.delete(f"/api/kb/conversations/{cid}").status_code == 200
    ids, _, _ = _pages(admin, visibility="hidden")
    assert cid in ids
    assert cid not in _pages(admin, visibility="visible")[0]
    d = _detail(admin, cid)
    assert d["visibility"] == "hidden" and d["hidden_at"]
    assert d["interaction"]["state"] == "inaccessible"
    assert [v["content"] for g in d["rounds"] for v in g["versions"]] == ["好的。"]
    assert "用户侧已移除" in ADMIN_JS
    assert "恢复" not in _section("/* ---------- 会话（A05）")


def test_a05_t03_multiple_clears_show_real_boundaries(env):
    """T03：多次清空显示真实分界，每个回合归入对应分段。"""
    user, admin = env["user"], env["admin"]
    cid = _conv(user)
    _ask(user, cid, "第一段", "c-1")
    user.post(f"/api/kb/conversations/{cid}/clear")
    _ask(user, cid, "第二段", "c-2")
    user.post(f"/api/kb/conversations/{cid}/clear")
    _ask(user, cid, "第三段", "c-3")
    d = _detail(admin, cid)
    assert [c["boundary_seq"] for c in d["clears"]] == [2, 4]
    assert [(g["user"]["content"], g["segment"]) for g in d["rounds"]] == [("第一段", 0), ("第二段", 1), ("第三段", 2)]
    assert d["cleared"] is True and d["clear_count"] == 2
    assert "清空前保留记录，仅管理查阅" in ADMIN_JS
    assert _pages(admin, cleared="yes")[0] == [cid]


def test_a05_t04_refresh_thrice_one_user_many_versions_feedback_apart(env):
    """T04：刷新三次 → 同一 MSG_ID、同一 ROUND_ID，多个不同 VER_ID，各自反馈不合并。"""
    user, admin = env["user"], env["admin"]
    cid = _conv(user)
    base = _ask(user, cid, "退款怎么扣", "v-1")
    execs = [base["exec_id"]]
    for i in range(3):
        execs.append(_refresh(user, cid, base["logical_round_id"], f"v-rf{i}")["exec_id"])
    assert user.post(f"/api/kb/rounds/{execs[0]}/feedback", json={"feedback": "down"}).status_code == 200
    assert user.post(f"/api/kb/rounds/{execs[2]}/feedback", json={"feedback": "up"}).status_code == 200
    d = _detail(admin, cid)
    assert len(d["rounds"]) == 1 and d["round_count"] == 1
    g = d["rounds"][0]
    assert g["user"]["msg_id"] == base["user_msg_id"] and g["round_id"] == base["logical_round_id"]
    vs = g["versions"]
    assert [v["exec_id"] for v in vs] == execs
    assert len({v["msg_id"] for v in vs}) == 4
    assert [v["feedback"] for v in vs] == ["down", None, "up", None]
    assert g["current_msg_id"] == vs[-1]["msg_id"]


def test_a05_t05_t06_unsaved_version_not_listed_default_kept(env, monkeypatch):
    """T05/T06：没保存下来的新版本不进版本列表；当前采用版本与失败前相同。"""
    user, admin, msgs, logs = env["user"], env["admin"], env["msgs"], env["logs"]
    cid = _conv(user)
    base = _ask(user, cid, "VIP 规则", "u-1")
    _flaky(monkeypatch, msgs, -1)
    failed = _refresh(user, cid, base["logical_round_id"], "u-rf")
    assert failed["save_blocked"] is True
    monkeypatch.setattr(msgs, "append_assistant", MsgStore.append_assistant.__get__(msgs))
    main._PENDING_REPLIES.clear()
    logs.rows[failed["exec_id"]]["pending_reply"] = None
    assert user.post(f"/api/kb/conversations/{cid}/retry-save").json()["code"] == "save_source_lost"
    g = _detail(admin, cid)["rounds"][0]
    assert failed["exec_id"] not in {v["exec_id"] for v in g["versions"]}
    assert g["current_msg_id"] == base["assistant_msg_id"]


def test_a05_t07_busy_and_blocked_shown_apart_no_unlock(env):
    """T07：忙碌与保存阻塞分开显示与筛选；后台不提供解锁。"""
    user, admin, convs = env["user"], env["admin"], env["convs"]
    busy, blocked, idle = _conv(user, "忙"), _conv(user, "阻塞"), _conv(user, "空闲")
    assert convs.acquire_run(busy, "r-running") == ("ok", None)
    convs.set_save_block(blocked, "r-unsaved")
    assert _pages(admin, state="busy")[0] == [busy]
    assert _pages(admin, state="blocked")[0] == [blocked]
    assert idle in _pages(admin, state="idle")[0]
    b = _detail(admin, busy)["interaction"]
    s = _detail(admin, blocked)["interaction"]
    assert (b["state"], b["busy"], b["save_blocked"], b["running_exec_id"]) == ("busy", True, False, "r-running")
    assert (s["state"], s["busy"], s["save_blocked"], s["blocked_exec_id"]) == ("blocked", False, True, "r-unsaved")
    section = _section("/* ---------- 会话（A05）")
    assert "执行忙碌" in section and "消息保存阻塞" in section
    for word in ("解锁", "解除", "retry-save", "method: \"POST\"", "method: \"DELETE\""):
        assert word not in section


def test_a05_t10_pages_cover_all_beyond_forty(env):
    """T10：45 个会话按 10 条一页翻完，并集覆盖全部，不因分页或旧上限丢 id。"""
    user, admin = env["user"], env["admin"]
    made = {_conv(user, f"c{i}") for i in range(45)}
    ids, pages, _ = _pages(admin, page_size=10)
    assert pages == 5
    assert len(ids) == len(set(ids)) and made <= set(ids)


def test_a05_open_detail_is_read_only(env):
    """ADM §6.3：打开详情前后，该用户的有效消息（L1 来源）、消息总数、执行记录都不变；只留敏感读取审计。"""
    user, admin, msgs, logs, auth = env["user"], env["admin"], env["msgs"], env["logs"], env["auth"]
    cid = _conv(user)
    _ask(user, cid, "一", "r-1")
    user.post(f"/api/kb/conversations/{cid}/clear")
    _ask(user, cid, "二", "r-2")
    before = ([m["id"] for m in msgs.effective_messages(cid)], len(msgs.repo.rows), dict(logs.rows), msgs.clear_seq(cid))
    _detail(admin, cid)
    admin.get("/api/kb/admin/conversations", params={"q": "一"})
    after = ([m["id"] for m in msgs.effective_messages(cid)], len(msgs.repo.rows), dict(logs.rows), msgs.clear_seq(cid))
    assert before == after
    reads = [a for a in auth.list_audits() if a.get("action") == "sensitive_read" and a.get("object") == cid]
    assert reads and reads[0].get("object_type") == "conversation"


def test_a05_legacy_conversation_shows_cache_marked(env):
    """A05 门定稿：M1 前的旧会话只读展示 payload 缓存，标「旧会话，消息待迁移」，回合数不可确定。"""
    user, admin = env["user"], env["admin"]
    cid = _conv(user, "老会话", messages=[{"role": "user", "text": "旧问题"}, {"role": "assistant", "text": "旧回答"}])
    item = [x for x in admin.get("/api/kb/admin/conversations").json()["items"] if x["id"] == cid][0]
    assert item["legacy"] is True and item["round_count"] is None
    d = _detail(admin, cid)
    assert d["rounds"] == []
    assert "旧会话，消息待迁移" in d["legacy_note"] and "非服务端事实" in d["legacy_note"]
    assert [m["text"] for m in d["payload_messages"]] == ["旧问题", "旧回答"]


def test_a05_permission_errors_and_bad_filters(env, monkeypatch):
    user, admin, convs = env["user"], env["admin"], env["convs"]
    cid = _conv(user)
    assert user.get("/api/kb/admin/conversations").status_code == 403
    assert user.get(f"/api/kb/admin/conversations/{cid}").status_code == 403
    miss = admin.get("/api/kb/admin/conversations/nope")
    assert miss.status_code == 404 and miss.json()["code"] == "conversation_not_found"
    assert admin.get("/api/kb/admin/conversations", params={"state": "bogus"}).json()["code"] == "invalid_request"
    assert admin.get("/api/kb/admin/conversations", params={"cursor": "%%%"}).json()["code"] == "bad_cursor"
    by_name = admin.get("/api/kb/admin/conversations", params={"account": "alice"}).json()["items"]
    assert [x["id"] for x in by_name] == [cid] and by_name[0]["username"] == "alice"

    def boom(*a, **k):
        raise RuntimeError("db down")

    monkeypatch.setattr(convs, "admin_page", boom)
    res = admin.get("/api/kb/admin/conversations")
    assert res.status_code == 503 and res.json()["code"] == "list_unavailable"


# ---------------- STEP-A16 ----------------

def _fb_pages(admin, **params):
    ids, pages, cursor = [], 0, ""
    while True:
        qp = dict(params)
        if cursor:
            qp["cursor"] = cursor
        data = admin.get("/api/kb/admin/feedback", params=qp).json()
        ids.extend(x["exec_id"] for x in data["items"])
        pages += 1
        if not data["has_more"]:
            return ids, pages, data
        cursor = data["next_cursor"]


def test_a16_t59_down_on_old_version_still_points_to_it(env):
    """T59：旧版被踩后刷新成功，被踩列表与详情仍指向被评的旧版，不把新答案放进详情。"""
    user, admin, pipe = env["user"], env["admin"], env["pipe"]
    cid = _conv(user)
    pipe.answer = "旧版回答"
    base = _ask(user, cid, "退款怎么扣", "f-1")
    assert user.post(f"/api/kb/rounds/{base['exec_id']}/feedback", json={"feedback": "down"}).status_code == 200
    pipe.answer = "新版回答"
    new = _refresh(user, cid, base["logical_round_id"], "f-rf")
    assert new["adopted"] is True
    items = admin.get("/api/kb/admin/feedback").json()["items"]
    assert [x["exec_id"] for x in items] == [base["exec_id"]]
    it = items[0]
    assert (it["feedback"], it["version_no"], it["is_current"]) == ("down", 1, False)
    assert it["assistant_msg_id"] == base["assistant_msg_id"] and it["feedback_at"]
    d = admin.get(f"/api/kb/admin/feedback/{base['exec_id']}").json()
    assert d["rated_content"] == "旧版回答" and d["question"] == "退款怎么扣"
    assert d["stale"] is True and "此反馈属于旧版" in d["stale_note"]
    assert d["current_version"]["msg_id"] == new["assistant_msg_id"]
    assert "新版回答" not in str(d)
    reads = [a for a in env["auth"].list_audits() if a.get("action") == "sensitive_read" and a.get("object") == base["exec_id"]]
    assert reads and reads[0].get("object_type") == "feedback"


def test_a16_t60_admin_cannot_write_user_feedback(env):
    """T60：管理员（含超管）写用户的赞踩被服务端拒绝；页面反馈分段没有写入口。"""
    user, admin, logs = env["user"], env["admin"], env["logs"]
    cid = _conv(user)
    base = _ask(user, cid, "问题", "f-10")
    assert user.post(f"/api/kb/rounds/{base['exec_id']}/feedback", json={"feedback": "down"}).status_code == 200
    for value in ("up", None):
        assert admin.post(f"/api/kb/rounds/{base['exec_id']}/feedback", json={"feedback": value}).status_code == 403
    assert logs.rows[base["exec_id"]]["feedback"] == "down"
    section = _section("/* ---------- 反馈（A16）")
    assert "/feedback" in section
    for word in ("method:", "data-qa-fb", "标为已处理"):
        assert word not in section


def test_a16_more_than_500_paged_fully(env):
    """ADM-R07：超过 500 条反馈按服务端分页能查全，不只看最近 500 条。"""
    admin, logs = env["admin"], env["logs"]
    for i in range(520):
        logs.rows[f"r-{i:04d}"] = {
            "round_id": f"r-{i:04d}", "feedback": "down", "feedback_at": f"2026-09-{1 + i // 60:02d} 00:{i % 60:02d}:00.000",
            "schema_ver": 2, "user_id": "u", "created_at": "2026-09-01 00:00:00.000",
        }
    ids, pages, _ = _fb_pages(admin, page_size=200)
    assert pages == 3 and len(ids) == 520 == len(set(ids))


def test_a16_filters_legacy_and_errors(env, monkeypatch):
    user, admin, logs = env["user"], env["admin"], env["logs"]
    cid = _conv(user)
    a = _ask(user, cid, "一", "f-20")
    b = _ask(user, cid, "二", "f-21")
    user.post(f"/api/kb/rounds/{a['exec_id']}/feedback", json={"feedback": "down"})
    user.post(f"/api/kb/rounds/{b['exec_id']}/feedback", json={"feedback": "up"})
    logs.rows["old-1"] = {"round_id": "old-1", "feedback": "down", "feedback_at": "2026-01-01 00:00:00.000",
                          "answer": "旧轮次回答", "user_id": "x"}
    assert [x["exec_id"] for x in admin.get("/api/kb/admin/feedback", params={"value": "up"}).json()["items"]] == [b["exec_id"]]
    assert len(admin.get("/api/kb/admin/feedback", params={"value": "all"}).json()["items"]) == 3
    assert [x["exec_id"] for x in admin.get("/api/kb/admin/feedback", params={"account": "alice"}).json()["items"]] == [a["exec_id"]]
    assert [x["exec_id"] for x in admin.get("/api/kb/admin/feedback", params={"exec_id": a["exec_id"]}).json()["items"]] == [a["exec_id"]]
    old = [x for x in admin.get("/api/kb/admin/feedback").json()["items"] if x["exec_id"] == "old-1"][0]
    assert old["legacy"] is True and old["assistant_msg_id"] is None and old["version_no"] is None
    assert "无法可靠关联回答版本" in old["legacy_note"]
    assert admin.get("/api/kb/admin/feedback/old-1").json()["rated_content"] == "旧轮次回答"
    assert admin.get("/api/kb/admin/feedback", params={"value": "x"}).json()["code"] == "invalid_request"
    assert admin.get("/api/kb/admin/feedback", params={"handled": "invalid"}).json()["code"] == "invalid_request"
    no_fb = _ask(user, cid, "三", "f-22")
    assert admin.get(f"/api/kb/admin/feedback/{no_fb['exec_id']}").status_code == 404
    assert user.get("/api/kb/admin/feedback").status_code == 403

    def boom(**k):
        raise RuntimeError("db down")

    monkeypatch.setattr(logs, "page_feedback", boom)
    res = admin.get("/api/kb/admin/feedback")
    assert res.status_code == 503 and res.json()["code"] == "list_unavailable"


# ---------------- STEP-A18 ----------------

def _diag_item(admin, key):
    return [i for i in admin.get("/api/kb/admin/diagnostics").json()["items"] if i["key"] == key][0]


def _events_of(admin, **params):
    return admin.get("/api/kb/admin/diag-events", params=params).json()


def test_a18_t65_knowledge_down_not_everything_down(env, monkeypatch):
    """T65：知识索引不可用只标知识检索，说明不依赖知识的分支按实际依赖执行，消息事实源不跟着标坏。"""
    admin = env["admin"]
    monkeypatch.setattr(main.store, "ping", lambda: False)
    kn = _diag_item(admin, "knowledge")
    assert kn["status"] == "down" and "不视为全部不可用" in kn["impact"]
    assert _diag_item(admin, "messages")["status"] == "ok"
    assert _diag_item(admin, "memory")["status"] == "not_connected"


def test_a18_t66_ping_ok_but_message_save_failed_shown_apart(env, monkeypatch):
    """T66：数据库可 ping，但 Assistant 保存失败，分开显示，不被健康成功覆盖；保存异常分三类。"""
    user, admin, msgs, logs = env["user"], env["admin"], env["msgs"], env["logs"]
    cid = _conv(user)
    _flaky(monkeypatch, msgs, -1)
    done = _ask(user, cid, "问题", "d-1")
    assert done["save_blocked"] is True
    monkeypatch.setattr(msgs, "append_assistant", MsgStore.append_assistant.__get__(msgs))
    logs.fail_final_update = True
    _ask(user, _conv(user), "再问", "d-2")
    logs.fail_final_update = False
    logs.fail_insert = True
    _ask(user, _conv(user), "三问", "d-3")
    logs.fail_insert = False
    m = _diag_item(admin, "messages")
    assert m["db_ping"] is True and m["status"] == "degraded"
    assert m["recent"]["counts"]["assistant_save_blocked"] == 1 and m["recent"]["counts"]["assistant_save_fail"] == 1
    rt = _diag_item(admin, "runtime")
    assert rt["recent"]["counts"] == {"runtime_insert_fail": 1, "runtime_update_fail": 1}
    kinds = {e["type"]: e["save_kind"] for e in _events_of(admin)["items"]}
    assert kinds["assistant_save_blocked"] == "assistant" and kinds["runtime_insert_fail"] == "runtime"
    assert kinds["runtime_update_fail"] == "runtime"
    # 事件不含问句与回答
    raw = env["diag"].path.read_text(encoding="utf-8")
    assert "问题" not in raw and "好的。" not in raw


def test_a18_user_save_fail_recorded_as_user_kind(env, monkeypatch):
    user, admin, msgs = env["user"], env["admin"], env["msgs"]
    cid = _conv(user)

    def broken(row):
        raise RuntimeError("db down")

    monkeypatch.setattr(msgs.repo, "insert", broken)
    _ask(user, cid, "存不上", "d-10")
    ev = [e for e in _events_of(admin)["items"] if e["type"] == "user_save_fail"]
    assert ev and ev[0]["save_kind"] == "user" and ev[0]["conv_id"] == cid


def test_a18_t67_diag_write_fail_marks_observation_limited(env, monkeypatch):
    """T67：旁路记录写不进去时标「观察受限」，不编造一份完整失败 Runtime。"""
    user, admin, logs = env["user"], env["admin"], env["logs"]
    blocker = env["tmp"] / "not-a-dir"
    blocker.write_text("x", encoding="utf-8")
    monkeypatch.setattr(main, "diag", DiagLog(blocker))
    logs.fail_insert = True
    done = _ask(user, _conv(user), "问", "d-20")
    assert done["exec_id"] not in logs.rows
    rt = _diag_item(admin, "runtime")
    assert rt["status"] == "limited" and "观察受限" in rt["note"]
    data = _events_of(admin)
    assert data["coverage"]["complete"] is False
    assert [e["type"] for e in data["items"]] == ["runtime_insert_fail"]


def test_a18_t68_ack_does_not_unblock(env, monkeypatch):
    """T68：确认已查看保存异常，不解除会话保存阻塞，也不重新生成。"""
    user, admin, msgs, convs, pipe = env["user"], env["admin"], env["msgs"], env["convs"], env["pipe"]
    cid = _conv(user)
    _flaky(monkeypatch, msgs, -1)
    done = _ask(user, cid, "问题", "d-30")
    ev = [e for e in _events_of(admin)["items"] if e["type"] == "assistant_save_blocked"][0]
    calls = len(pipe.calls)
    res = admin.post(f"/api/kb/admin/diag-events/{ev['id']}/ack")
    assert res.status_code == 200 and res.json()["written"] is True
    assert convs.save_block_of(cid) == done["exec_id"]
    assert len(pipe.calls) == calls
    d = admin.get(f"/api/kb/admin/diag-events/{ev['id']}").json()
    assert d["acked"] is True and d["acks"][0]["actor_username"] == "admin"
    assert d["current"]["conversation"]["save_blocked"] is True
    assert d["current"]["exec"]["msg_save"] == "failed"
    assert "补写" in d["retries_note"]
    assert [e["id"] for e in _events_of(admin, acked="no")["items"] if e["id"] == ev["id"]] == []
    assert admin.post("/api/kb/admin/diag-events/nope/ack").status_code == 404


def test_a18_t69_open_health_page_no_writes_no_model(env, monkeypatch):
    """T69：打开/刷新诊断不发起模型调用、不重建索引、不写业务数据或审计。"""
    admin, msgs, logs, auth, pipe = env["admin"], env["msgs"], env["logs"], env["auth"], env["pipe"]

    async def no_rebuild():
        raise AssertionError("不应重建索引")

    monkeypatch.setattr(main.indexer, "rebuild", no_rebuild)
    before = (len(msgs.repo.rows), dict(logs.rows), len(auth.list_audits()), len(pipe.calls),
              env["diag"].path.exists() and env["diag"].path.read_text(encoding="utf-8"))
    for _ in range(2):
        assert admin.get("/api/kb/admin/diagnostics").status_code == 200
        assert admin.get("/api/kb/admin/diag-events").status_code == 200
    after = (len(msgs.repo.rows), dict(logs.rows), len(auth.list_audits()), len(pipe.calls),
             env["diag"].path.exists() and env["diag"].path.read_text(encoding="utf-8"))
    assert before == after
    assert admin.get("/api/kb/admin/diagnostics").json()["active_checks"] == ["mysql_ping", "qdrant_ping"]


def test_a18_t70_unauthorized_denied_anonymous_health_unchanged(env):
    """T70：无「健康」拒绝；匿名 /health 字段不扩。"""
    user = env["user"]
    assert user.get("/api/kb/admin/diagnostics").status_code == 403
    assert user.get("/api/kb/admin/diag-events").status_code == 403
    assert user.post("/api/kb/admin/diag-events/x/ack").status_code == 403
    anon = TestClient(main.app)
    body = anon.get("/api/kb/health").json()
    assert set(body) == {"qdrant_ready", "config_ready", "key_dashscope", "key_deepseek",
                         "chunk_count", "index_ready", "startup_error"}


def test_a18_t71_t72_tls_saved_but_enable_failed(env):
    """T71：证书上传成功、启用失败 → 如实显示只保存/失败，协议不变，不回显私钥。T72：说明非标准端口限制。"""
    admin = env["admin"]
    bad = "-----BEGIN CERTIFICATE-----\nnope\n-----END CERTIFICATE-----"
    key = "-----BEGIN PRIVATE KEY-----\nSECRETKEY\n-----END PRIVATE KEY-----"
    assert admin.post("/api/kb/admin/tls", json={"cert_pem": bad, "key_pem": key}).status_code == 200
    assert admin.post("/api/kb/admin/tls/enable").status_code == 400
    st = admin.get("/api/kb/admin/tls").json()
    assert st["enabled"] is False and st["scheme"] == "http" and st["pending"] is True
    assert st["last_enable_error"] and st["last_enable_error_at"]
    assert "SECRETKEY" not in str(st)
    assert st["redirect_https"] is False and "80/443" in st["port_note"]
    section = _section("/* ---------- 证书")
    assert "last_enable_error" in section and "port_note" in section


def test_a18_diag_file_rotation_keeps_three(tmp_path, monkeypatch):
    """G-E06-6：追加写、超过大小轮转、只保留 3 份旧文件；事件只含类型/模块/错误码/id/时间。"""
    from app import diag as diag_mod

    monkeypatch.setattr(diag_mod, "MAX_BYTES", 300)
    d = DiagLog(tmp_path)
    for i in range(60):
        d.record("model_error", "generate:x", exec_id=f"e{i}")
    names = sorted(p.name for p in (tmp_path / "diag").iterdir())
    assert names == ["events.jsonl", "events.jsonl.1", "events.jsonl.2", "events.jsonl.3"]
    events, broken = d.events()
    assert not broken and 0 < len(events) < 60
    assert set(events[0]) <= {"id", "ts", "type", "module", "code", "exec_id", "acks", "acked", "save_kind"}


# ---------------- STEP-A15 ----------------

def _metric(ov, key):
    for sec in ov["sections"]:
        for m in sec["metrics"]:
            if m["key"] == key:
                return m
    raise KeyError(key)


def test_a15_t49_rounds_execs_and_retransmit(env):
    """T49：新提问一轮、刷新两次、一次重传 → 新逻辑回合 1、执行 3、刷新 2，重传不进执行。"""
    user, admin, logs = env["user"], env["admin"], env["logs"]
    cid = _conv(user)
    base = _ask(user, cid, "VIP 保级", "o-1")
    r1 = _refresh(user, cid, base["logical_round_id"], "o-rf1")
    r2 = _refresh(user, cid, base["logical_round_id"], "o-rf2")
    dup = _last(_events(user.post("/api/kb/ask", json={
        "conversation_id": cid, "query": "VIP 保级", "client_request_id": "o-1"}).text), "error")
    assert dup["type"] == "duplicate_request"
    ov = admin.get("/api/kb/admin/overview").json()
    assert _metric(ov, "new_rounds")["value"] == 1
    ex = _metric(ov, "executions")
    assert ex["value"] == 3 and ex["rejected"] == 1
    assert _metric(ov, "refreshes")["value"] == 2
    assert _metric(ov, "active_accounts")["value"] == 1
    assert {base["exec_id"], r1["exec_id"], r2["exec_id"]} <= set(logs.rows)
    # 执行耗时有终态时间样本
    assert _metric(ov, "duration")["value"]["samples"] >= 3
    assert all(logs.rows[e].get("finished_at") for e in (base["exec_id"], r1["exec_id"]))
    assert ov["range"]["days"] == 7 and ov["cache"] == "none" and ov["data_cutoff"]


def test_a15_t50_t53_heat_rules():
    """T50～T53：未实际调用不计热度也不加未归类；同执行同功能只 +1；旧记录与资格未知单列。"""
    from app.overview import compute_heat

    rows = [
        {"schema_ver": 2, "used_knowledge_rag": 0, "c_gen": [], "route": "knowledge_query"},    # T50
        {"schema_ver": 2, "used_knowledge_rag": 1,
         "c_gen": [{"feature_id": "vip"}, {"feature_id": "vip"}, {"feature_id": "refund"}]},      # T51
        {"schema_ver": 2, "used_knowledge_rag": 0, "c_gen": None},                              # T52 ack
        {"schema_ver": 2, "used_knowledge_rag": None, "c_gen": [{"feature_id": "vip"}]},         # T53 资格未知
        {"schema_ver": 2, "used_knowledge_rag": 1, "c_gen": None},                              # 生成集未采集
        {"schema_ver": 2, "used_knowledge_rag": 1, "c_gen": []},                                # 确实无功能
        {"c_gen": [{"feature_id": "vip"}]},                                                     # 旧记录
    ]
    h = compute_heat(rows)
    assert h["items"] == [{"feature_id": "refund", "count": 1}, {"feature_id": "vip", "count": 1}]
    assert h["unclassified"] == 1
    assert h["unknown_qualification"] == 1 and h["unknown_c_gen"] == 1
    assert h["legacy"]["rows"] == 1 and h["legacy"]["items"] == [{"feature_id": "vip", "count": 1}]
    assert h["coverage"]["complete"] is True


def test_a15_t54_limited_window_marked():
    """T54：范围内超过扫描上限时标覆盖不完整并给实际窗口。"""
    from app.overview import compute_heat

    rows = [{"schema_ver": 2, "used_knowledge_rag": 1, "c_gen": [{"feature_id": "vip"}],
             "created_at": f"2026-09-{d:02d} 00:00:00"} for d in range(28, 0, -1)]
    h = compute_heat(rows, limit=10)
    cov = h["coverage"]
    assert cov["complete"] is False and cov["scanned"] == 10
    assert cov["window_start"] == "2026-09-19 00:00:00" and cov["window_end"] == "2026-09-28 00:00:00"
    assert h["items"][0]["count"] == 10


def test_a15_t56_t57_not_applicable_and_pending_apart():
    """T56：无已评价回复 → 赞占比不适用。T57：运行中、待补写、未知不进分母，单列。"""
    from app.overview import compose, compute_heat

    counts = {
        "execs": 6, "exec_state": {"completed": 3, "failed": 1, "running": 1, None: 1},
        "biz": {"answered": 3, None: 1},
        "ms_saved": 3, "ms_failed_final": 1, "ms_failed_pending": 1, "ms_pending": 1,
        "fb_queue": 3, "fb_up": 0, "fb_down": 0, "durations_ms": [100, 200, 300, 400], "dur_unknown": 1,
    }
    ov = compose(counts, compute_heat([]))
    up = _metric(ov, "feedback_up_ratio")["value"]
    assert up["denominator"] == 0 and up["value"] is None and up["display"] == "不适用"
    assert _metric(ov, "feedback_coverage")["value"]["display"] == "0.0%"
    err = _metric(ov, "exec_error_rate")
    assert (err["value"]["numerator"], err["value"]["denominator"]) == (1, 4)
    assert err["running"] == 1 and err["unknown"] == 1
    ms = _metric(ov, "msg_save_fail_rate")
    assert (ms["value"]["numerator"], ms["value"]["denominator"]) == (1, 4)
    assert ms["pending_retry"] == 1 and ms["pending"] == 1
    d = _metric(ov, "duration")
    assert d["value"] == {"samples": 4, "mean_ms": 250.0, "p50_ms": 250.0, "p95_ms": 385.0} and d["unknown"] == 1
    for key in ("memory_calls", "evidence_check", "model_usage"):
        assert _metric(ov, key)["status"] == "not_connected"
    for sec in ov["sections"]:
        for m in sec["metrics"]:
            assert m["source"] and m["time_field"] and m["unit"] and m["rule"]


def test_a15_t55_t58_semantics_permission_no_leak(env):
    """T55：反馈概览按生成时间、反馈列表按反馈时间，口径分开标注。T58：概览只给聚合，不含账号与正文；无权 403。"""
    user, admin = env["user"], env["admin"]
    cid = _conv(user)
    base = _ask(user, cid, "只出现在正文里的问句XYZ", "o-10")
    user.post(f"/api/kb/rounds/{base['exec_id']}/feedback", json={"feedback": "down"})
    ov = admin.get("/api/kb/admin/overview").json()
    fb = [s for s in ov["sections"] if s["key"] == "feedback"][0]
    assert "反馈时间" in fb["note"] and "不混算" in fb["note"]
    assert _metric(ov, "feedback_coverage")["value"]["numerator"] == 1
    assert admin.get("/api/kb/admin/feedback").json()["time_field"].startswith("feedback_at")
    text = str(ov)
    assert "alice" not in text and "XYZ" not in text and cid not in text
    assert user.get("/api/kb/admin/overview").status_code == 403
    too_long = admin.get("/api/kb/admin/overview", params={"since": "2026-01-01", "until": "2026-09-29"})
    assert too_long.status_code == 400 and too_long.json()["code"] == "range_too_large"
    assert admin.get("/api/kb/admin/overview", params={"domain": "test"}).json()["status"] == "recorded"
    roles = admin.get("/api/kb/admin/roles").json()
    assert "数据概览" not in roles["pending"]


def test_a15_overview_page_static():
    section = _section("/* ---------- 运行概览（A15）")
    assert '"/admin/overview"' in ADMIN_JS and 'hasPerm("数据概览")' in ADMIN_JS
    assert "不适用" in section and "未接入" in section
    assert "method:" not in section


def test_a18_page_is_observe_only():
    section = _section("/* ---------- 诊断（A18）")
    assert "标记已查看" in section and "观察受限" in section
    for word in ("retry-save", ">重试保存<", "解锁", "修复", "/reindex"):
        assert word not in section
