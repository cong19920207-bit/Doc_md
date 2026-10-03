# -*- coding: utf-8 -*-
"""多轮编排 M5：Router v3 → 非知识分支 → 任务准备 → 唯一 Rewriter → Generate 交接 → 证据检查 → 断线继续。"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import main, msg_store, settings
from app.auth_store import ROLE_USER_ID, AuthStore, MemoryAuthRepo
from app.branches import BranchError, parse_clarification, pick_reply, time_context
from app.evidence import (
    CHECK_FAIL_MESSAGE,
    CheckError,
    EvidenceChecker,
    draft_hash,
    evidence_items,
    number_issue,
    parse_check,
)
from app.pipeline import Pipeline, RewriteInvalid, build_rewrite_user, parse_rewrite_v3
from app.tasks import (
    HISTORY_UNSUPPORTED,
    TASK_CHECKS,
    TaskPreparer,
    TaskPrepError,
    build_prep_messages,
    parse_task_prep,
    settle,
    task_brief,
)
from app.conv_store import ConvStore, MemoryConvRepo
from app.logs import RUNTIME_COLUMNS, RUNTIME_JSON_FIELDS, sanitize_runtime_fields
from app.models_ext import ModelError
from app.msg_store import MemoryMsgRepo, MsgStore
from app.router import (
    ROUTES,
    ConversationRouter,
    RouterError,
    build_router_messages,
    parse_router_output,
    router_runtime,
)

ROOT = Path(__file__).resolve().parents[3]
INIT_SQL = (ROOT / "site" / "kb-api" / "sql" / "init.sql").read_text(encoding="utf-8")
QA_JS = (ROOT / "site" / "feature-interaction" / "qa.js").read_text(encoding="utf-8")
_REAL_FAIL_TYPE = main._fail_type


class FakeLogs:
    """替身执行日志：保留每次 update 的字段，便于检查「只写一次」。"""

    def __init__(self) -> None:
        self.rows: dict[str, dict] = {}
        self.updates: list[tuple[str, dict]] = []
        self.last_error = None

    def insert_running(self, row: dict) -> bool:
        self.rows[row["round_id"]] = dict(row)
        return True

    def update_round(self, round_id: str, fields: dict) -> bool:
        self.updates.append((round_id, dict(fields)))
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

    def ensure_feedback_columns(self) -> bool:
        return True

    def ensure_runtime_columns(self) -> bool:
        return True


class FakePipeline:
    def __init__(self) -> None:
        self.calls: list[tuple[str, object]] = []
        self.cfgs: list[dict] = []
        self.answer = "好的。"
        self.blocks = [{"path": "a.md", "chunk_id": "c1", "content": "正文", "feature_id": "vip"}]
        self.rw: dict | Exception | None = None
        # STEP-Q10 用：先吐一段、等闸门放行再吐余下，或中途抛错
        self.head = ""
        self.gate = None
        self.stream_error: Exception | None = None

    async def rewrite(self, original, history, cfg):
        self.calls.append(("rewrite", list(history)))
        self.cfgs.append(dict(cfg))
        if isinstance(self.rw, Exception):
            raise self.rw
        if self.rw is not None:
            return dict(self.rw)
        return {"rewrite_query": original, "same_topic": False, "named_feature_ids": []}

    async def retrieve(self, original, rewrite_query, named_ids, cfg):
        self.calls.append(("retrieve", rewrite_query))
        return {"mode": "hybrid", "lanes": {}, "candidates": [{"path": "a.md"}]}

    async def rerank(self, query, candidates, named, prev_blocks, same_topic, cfg):
        self.calls.append(("rerank", list(prev_blocks)))
        return list(self.blocks)

    async def stream_answer(self, original, rw, c_gen, cfg):
        self.calls.append(("generate", original))
        self.cfgs.append(dict(cfg))
        if self.head:
            yield self.head
        if self.gate is not None:
            await self.gate.wait()
        if isinstance(self.stream_error, Exception):
            raise self.stream_error
        yield self.answer


class FakeModels:
    """替身模型：按队列返回原始文本或抛出异常，记录每次收到的 messages。"""

    def __init__(self, default: str | None = None) -> None:
        self.replies: list[object] = []
        self.seen: list[list[dict]] = []
        self.default = default

    async def rewrite(self, messages, temperature):
        self.seen.append(messages)
        fallback = self.default if self.default is not None else _router_json("knowledge_query", False)
        reply = self.replies.pop(0) if self.replies else fallback
        if isinstance(reply, Exception):
            raise reply
        return reply


def _router_json(route, requires_history, confidence=0.9, reason="分类理由", **extra):
    obj = {"route": route, "requires_history": requires_history, "confidence": confidence, "reason": reason}
    obj.update(extra)
    return json.dumps(obj, ensure_ascii=False)


def _task(tid, goal, check="ready", mode="查询", **extra):
    t = {"task_id": tid, "goal": goal, "mode": mode, "scope": "", "constraints": [],
         "depends_on": [], "check": check, "gap_ids": []}
    t.update(extra)
    return t


def _gap(gid, task_ids, type_="user_condition", clue="", candidates=None, status="open"):
    return {"gap_id": gid, "task_ids": task_ids, "type": type_, "required": True, "status": status,
            "candidates": candidates or [], "clue": clue}


def _prep_json(tasks, excluded=None, gaps=None, rc="", **extra):
    obj = {"tasks": tasks, "excluded": excluded or [], "information_gaps": gaps or [], "response_constraint": rc}
    obj.update(extra)
    return json.dumps(obj, ensure_ascii=False)


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
    fake_models = FakeModels()
    prep_models = FakeModels(default=_prep_json([_task("T1", "按原句查询规则")]))
    monkeypatch.setattr(main, "task_preparer", TaskPreparer(prep_models))
    check_models = FakeModels(default=json.dumps({"check_status": "pass", "issues": [], "conflict": False}))
    monkeypatch.setattr(main, "evidence_checker", EvidenceChecker(check_models))
    monkeypatch.setattr(main, "auth", auth)
    monkeypatch.setattr(main, "convs", convs)
    monkeypatch.setattr(main, "msgs", msgs)
    monkeypatch.setattr(main, "logs", logs)
    monkeypatch.setattr(main, "pipeline", pipe)
    monkeypatch.setattr(main, "router", ConversationRouter(fake_models))
    monkeypatch.setattr(main, "models", fake_models)
    monkeypatch.setattr(main, "_startup_index", _noop_index)
    monkeypatch.setattr(main, "_fail_type", lambda *a, **k: None)
    with TestClient(main.app) as client:
        assert client.post("/api/kb/auth/login", json={"username": "alice", "password": "pw"}).status_code == 200
        yield {
            "client": client, "convs": convs, "msgs": msgs, "logs": logs,
            "pipe": pipe, "models": fake_models, "prep": prep_models, "check": check_models,
        }


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


def _exec_id(events) -> str:
    return (_last(events, "done") or _last(events, "error"))["exec_id"]


# ---------------- STEP-Q11 ----------------

def test_q11_schema_accepts_valid_output_and_records_extra_keys():
    got = parse_router_output(_router_json("knowledge_query", True, 0.93, "查此前场景的退款", memory_query="x"))
    assert got == {
        "route": "knowledge_query",
        "requires_history": True,
        "confidence": 0.93,
        "reason": "查此前场景的退款",
        "extra_keys": ["memory_query"],
    }
    # 容错：外包代码块或说明文字时取第一个对象
    fenced = "```json\n" + _router_json("ack", False, 1, "感谢收口") + "\n```"
    assert parse_router_output(fenced)["route"] == "ack"
    assert parse_router_output(_router_json("unclear", False, 0, "无指向"))["confidence"] == 0.0
    for route in ROUTES:
        assert parse_router_output(_router_json(route, False))["route"] == route


@pytest.mark.parametrize("raw,detail", [
    ("我觉得是 unclear", "not_json"),
    ("{route: knowledge_query}", "not_json"),
    ("[1, 2]", "not_object"),
    (json.dumps({"requires_history": False, "confidence": 0.5, "reason": "r"}), "missing:route"),
    (json.dumps({"route": "ack", "confidence": 0.5, "reason": "r"}), "missing:requires_history"),
    (json.dumps({"route": "ack", "requires_history": False, "reason": "r"}), "missing:confidence"),
    (json.dumps({"route": "ack", "requires_history": False, "confidence": 0.5}), "missing:reason"),
    (_router_json("context_dependent", True), "route"),
    (_router_json("KNOWLEDGE_QUERY", True), "route"),
    (_router_json("knowledge_query", "true"), "requires_history"),
    (_router_json("knowledge_query", 1), "requires_history"),
    (_router_json("knowledge_query", False, 1.2), "confidence"),
    (_router_json("knowledge_query", False, -0.1), "confidence"),
    (_router_json("knowledge_query", False, True), "confidence"),
    (_router_json("knowledge_query", False, "0.9"), "confidence"),
    ('{"route":"ack","requires_history":false,"confidence":NaN,"reason":"r"}', "confidence"),
    (_router_json("knowledge_query", False, 0.9, ""), "reason"),
    (_router_json("knowledge_query", False, 0.9, 3), "reason"),
])
def test_q11_schema_rejects_illegal_output_as_exec_error(raw, detail):
    """RQ-01 / S01 §9.2：非法输出是分类执行异常，不是 unclear。"""
    with pytest.raises(RouterError) as info:
        parse_router_output(raw)
    assert info.value.code == "router_invalid"
    assert info.value.detail == detail


def test_q11_empty_response_is_call_failure():
    with pytest.raises(RouterError) as info:
        parse_router_output("   ")
    assert info.value.code == "router_fail"


def test_q11_prompt_and_input_follow_template():
    """C01 / C05 / C09 相关规则在 Prompt 中；L1 与当前输入分开；不预置阈值。"""
    prompt = settings.ROUTER_PROMPT
    for route in ROUTES:
        assert route in prompt
    assert "同窗、同词、短句不单独决定历史依赖" in prompt          # C01
    assert "“好的，那退款呢”不是 ack" in prompt                    # C05
    assert "不认识业务词不等于越界" in prompt                      # C09
    assert "0.7" not in prompt
    turns = [{"user": "VIP 保级规则是什么？", "assistant": "按月统计……"}]
    msgs = build_router_messages("YallaPay 链接支付有什么规则？", turns)
    assert msgs[0] == {"role": "system", "content": prompt}
    user = msgs[1]["content"]
    assert "[回合1] User: VIP 保级规则是什么？" in user
    assert user.rstrip().endswith("当前输入：YallaPay 链接支付有什么规则？\n\n只输出 JSON。")
    assert "承接线索" not in user
    empty = build_router_messages("那个呢？", [])[1]["content"]
    assert "（无）" in empty


@pytest.mark.parametrize("exc,code", [
    (ModelError("llm_fail", "模型请求失败：timeout"), "router_fail"),
    (ModelError("missing_key", "缺 Key：未配置 DEEPSEEK_API_KEY", 400), "missing_key"),
    (RuntimeError("boom"), "router_fail"),
])
@pytest.mark.anyio
async def test_q11_router_call_failures(exc, code):
    models = FakeModels()
    models.replies = [exc]
    with pytest.raises(RouterError) as info:
        await ConversationRouter(models).route("VIP 保级规则是什么？", [], {"temperature": 0.2})
    assert info.value.code == code


@pytest.fixture
def anyio_backend():
    return "asyncio"


def test_q11_c01_runtime_records_original_route(env):
    """C01：同窗聊过 VIP，本轮问 YallaPay → knowledge_query / false，写入 Runtime。"""
    client, models, logs = env["client"], env["models"], env["logs"]
    cid = _new_conv(client)
    _ask(client, cid, "VIP 保级规则是什么？", "c01-1")
    models.replies = [_router_json("knowledge_query", False, 0.88, "独立查询 YallaPay 规则")]
    ev = _ask(client, cid, "YallaPay 链接支付有什么规则？", "c01-2")
    assert _last(ev, "done")["status"] == "success"
    assert ("stage", {"stage": "route", "round_id": _exec_id(ev)}) in ev
    row = logs.rows[_exec_id(ev)]
    assert row["route"] == "knowledge_query"
    assert row["requires_history"] is False
    assert row["router"]["confidence"] == 0.88
    assert row["router"]["valid"] is True
    assert row["router"]["reason"] == "独立查询 YallaPay 规则"
    # Router 输入含服务端 L1（上一回合），当前原句单独传入、不在 L1 中
    user = models.seen[-1][1]["content"]
    assert "[回合1] User: VIP 保级规则是什么？" in user
    assert "共 1 个完整回合" in user
    assert "YallaPay" not in user.split("当前输入：")[0]


@pytest.mark.parametrize("query,case", [
    ("好的，那退款怎么算？", "C05"),
    ("查一下 Hayyo 新功能 X 的奖励规则", "C09"),
])
def test_q11_c05_c09_knowledge_query_proceeds(env, query, case):
    """C05 非 ack、C09 不认识的 X：Router 判为 knowledge_query 时照常进入知识链路。"""
    client, models, logs, pipe = env["client"], env["models"], env["logs"], env["pipe"]
    cid = _new_conv(client)
    models.replies = [_router_json("knowledge_query", case == "C05", 0.8, case)]
    ev = _ask(client, cid, query, case)
    assert _last(ev, "done")["status"] == "success"
    assert logs.rows[_exec_id(ev)]["route"] == "knowledge_query"
    assert [c[0] for c in pipe.calls] == ["rewrite", "retrieve", "rerank", "generate"]
    assert models.seen[-1][1]["content"].endswith(f"当前输入：{query}\n\n只输出 JSON。")


def test_q11_invalid_output_is_exec_error_not_unclear(env):
    """非法 JSON：执行异常，不检索、不生成，不写成 unclear/clarify；提示按 error_notice 落库并释放执行权。"""
    client, models, logs, pipe, msgs = env["client"], env["models"], env["logs"], env["pipe"], env["msgs"]
    cid = _new_conv(client)
    models.replies = ["我觉得是 unclear"]
    ev = _ask(client, cid, "那个呢？", "bad-1")
    err = _last(ev, "error")
    assert err["type"] == "router_invalid"
    assert _last(ev, "done") is None
    assert pipe.calls == []
    row = logs.rows[err["exec_id"]]
    assert row["route"] is None and row["requires_history"] is None
    assert row["router"]["valid"] is False
    assert row["router"]["error"] == "router_invalid"
    assert row["router"]["raw"] == "我觉得是 unclear"
    assert row["error_type"] == "router_invalid"
    assert row["exec_state"] == "failed"
    assert row["biz_result"] is None
    assert row["status"] == "gen_fail"
    rows = msgs.effective_messages(cid)
    assert [r["role"] for r in rows] == ["user", "assistant"]
    assert rows[1]["completeness"] == "error_notice"
    # 执行权已释放，同会话可继续发送
    ev2 = _ask(client, cid, "VIP 保级规则是什么？", "bad-2")
    assert _last(ev2, "done")["status"] == "success"


def test_q11_call_failure_no_retry(env):
    """调用失败记 router_fail，不重试（E02 未定）。"""
    client, models, logs, pipe = env["client"], env["models"], env["logs"], env["pipe"]
    cid = _new_conv(client)
    models.replies = [ModelError("llm_fail", "模型 502")]
    ev = _ask(client, cid, "VIP 保级规则是什么？", "fail-1")
    err = _last(ev, "error")
    assert err["type"] == "router_fail"
    assert len(models.seen) == 1
    assert pipe.calls == []
    assert logs.rows[err["exec_id"]]["router"]["error"] == "router_fail"
    assert "raw" not in logs.rows[err["exec_id"]]["router"]


def test_q11_low_confidence_only_recorded(env):
    """G-E03：低置信度兜底未启用，confidence 只记录，不改变分支。"""
    client, models, logs, pipe = env["client"], env["models"], env["logs"], env["pipe"]
    cid = _new_conv(client)
    models.replies = [_router_json("knowledge_query", False, 0.01, "不太确定")]
    ev = _ask(client, cid, "VIP 保级规则是什么？", "low-1")
    assert _last(ev, "done")["status"] == "success"
    assert logs.rows[_exec_id(ev)]["router"]["confidence"] == 0.01
    assert ("retrieve", "VIP 保级规则是什么？") in pipe.calls


def test_q11_route_written_once_per_exec(env):
    """原始 route 只在 Router 这一步写入，同一执行后续更新不改写。"""
    client, logs = env["client"], env["logs"]
    cid = _new_conv(client)
    ev = _ask(client, cid, "VIP 保级规则是什么？", "once-1")
    eid = _exec_id(ev)
    route_writes = [f for rid, f in logs.updates if rid == eid and ("route" in f or "requires_history" in f)]
    assert len(route_writes) == 1


def test_q11_refresh_routes_with_snapshot_l1(env):
    """刷新是新执行，单独分类；Router 读原快照 L1，不读原问题之后的对话。"""
    client, models, logs = env["client"], env["models"], env["logs"]
    cid = _new_conv(client)
    first = _ask(client, cid, "VIP 保级规则是什么？", "rf-1")
    _ask(client, cid, "那退款呢？", "rf-2")
    lr = _last(first, "accepted")["logical_round_id"]
    ev = _refresh(client, cid, lr, "rf-3")
    assert _last(ev, "done")["status"] == "success"
    user = models.seen[-1][1]["content"]
    assert "共 0 个完整回合" in user
    assert "那退款呢" not in user
    assert user.endswith("当前输入：VIP 保级规则是什么？\n\n只输出 JSON。")
    assert logs.rows[_exec_id(ev)]["route"] == "knowledge_query"
    assert logs.rows[_exec_id(first)]["route"] == "knowledge_query"


def test_q11_runtime_storage_and_frontend():
    assert ("route", "VARCHAR(24) NULL") in RUNTIME_COLUMNS
    assert ("requires_history", "TINYINT NULL") in RUNTIME_COLUMNS
    assert "router" in RUNTIME_JSON_FIELDS
    for ddl in ("route VARCHAR(24) NULL", "requires_history TINYINT NULL", "router JSON NULL"):
        assert ddl in INIT_SQL
    out = sanitize_runtime_fields(router_runtime(parse_router_output(_router_json("ack", True))))
    assert out["route"] == "ack" and out["requires_history"] == 1
    assert json.loads(out["router"])["prompt_ver"] == "router-v3"
    # 枚举外的 route 不写入
    assert "route" not in sanitize_runtime_fields({"route": "context_dependent"})
    assert 'route: "理解问题中…"' in QA_JS


# ---------------- STEP-Q12 ----------------

def _assistant_rows(msgs, cid):
    return [r for r in msgs.effective_messages(cid) if r["role"] == "assistant"]


def test_q12_c04_ack_pool_no_further_calls(env):
    """C04：ack 从话术池取一句，Router 之后不再调用 LLM/RAG；回复照常落库。"""
    client, models, logs, pipe, msgs = env["client"], env["models"], env["logs"], env["pipe"], env["msgs"]
    cid = _new_conv(client)
    models.replies = [_router_json("ack", False, 0.95, "感谢收口")]
    ev = _ask(client, cid, "好的，谢谢", "ack-1")
    done = _last(ev, "done")
    assert done["status"] == "success"
    assert done["text"] in settings.ACK_REPLY_POOL
    assert done["c_gen"] == []
    assert len(models.seen) == 1
    assert pipe.calls == []
    row = logs.rows[done["exec_id"]]
    assert row["route"] == "ack"
    assert row["biz_result"] == "not_applicable"
    assert row["exec_state"] == "completed"
    assert row["used_knowledge_rag"] is False
    saved = _assistant_rows(msgs, cid)
    assert [r["content"] for r in saved] == [done["text"]]
    assert saved[0]["completeness"] == "complete"


def test_q12_reply_pools_are_independent():
    """两个话术池独立：越界句不在 ack 池里；空池是配置异常，不静默返回空回复。"""
    assert set(settings.ACK_REPLY_POOL).isdisjoint(settings.OUT_OF_SCOPE_REPLY_POOL)
    assert pick_reply(["  ", "收到。"]) == "收到。"
    with pytest.raises(BranchError) as info:
        pick_reply(["", "  "])
    assert info.value.code == "reply_pool_empty"


def test_q12_c06_smalltalk_short_reply_without_rag(env):
    """C06：smalltalk 用 Smalltalk Prompt，只收 L1 与当前输入，不调用 Memory/Knowledge。"""
    client, models, logs, pipe = env["client"], env["models"], env["logs"], env["pipe"]
    cid = _new_conv(client)
    models.replies = [_router_json("smalltalk", False, 0.9, "情绪表达"), "辛苦了，有 Hayyo 规则想查随时问我。"]
    ev = _ask(client, cid, "今天好累", "st-1")
    done = _last(ev, "done")
    assert done["text"] == "辛苦了，有 Hayyo 规则想查随时问我。"
    assert ("stage", {"stage": "smalltalk", "round_id": done["round_id"]}) in ev
    assert len(models.seen) == 2
    sys_msg, user_msg = models.seen[1]
    assert sys_msg["content"] == settings.SMALLTALK_PROMPT
    assert "1～2 句" in settings.SMALLTALK_PROMPT and "引导回 Hayyo" in settings.SMALLTALK_PROMPT
    assert user_msg["content"].endswith("当前输入：今天好累")
    assert pipe.calls == []
    row = logs.rows[done["exec_id"]]
    assert row["biz_result"] == "not_applicable"
    assert row["used_knowledge_rag"] is False


@pytest.mark.parametrize("query", ["法国首都是哪里？", "帮我设计新的 VIP 保级规则"])
def test_q12_c07_c08_out_of_scope_no_retrieve(env, query):
    """C07、C08：越界走独立话术池，不回答、不检索、Router 之后无模型调用。"""
    client, models, logs, pipe = env["client"], env["models"], env["logs"], env["pipe"]
    cid = _new_conv(client)
    models.replies = [_router_json("out_of_scope", False, 0.9, "越界")]
    done = _last(_ask(client, cid, query, "oos-" + str(len(query))), "done")
    assert done["text"] in settings.OUT_OF_SCOPE_REPLY_POOL
    assert done["text"] not in settings.ACK_REPLY_POOL
    assert len(models.seen) == 1
    assert pipe.calls == []
    row = logs.rows[done["exec_id"]]
    assert row["biz_result"] == "refused"
    assert row["used_knowledge_rag"] is False


def test_q12_c12_unclear_empty_history_clarifies(env):
    """C12：空历史「那个呢？」→ Clarification Generator 生成一句澄清，不检索。"""
    client, models, logs, pipe = env["client"], env["models"], env["logs"], env["pipe"]
    cid = _new_conv(client)
    models.replies = [
        _router_json("unclear", False, 0.7, "无指向"),
        json.dumps({"clarification": "你想了解哪个功能的规则？比如 VIP 或 YallaPay。"}, ensure_ascii=False),
    ]
    ev = _ask(client, cid, "那个呢？", "uc-1")
    done = _last(ev, "done")
    assert done["text"] == "你想了解哪个功能的规则？比如 VIP 或 YallaPay。"
    assert ("stage", {"stage": "clarify", "round_id": done["round_id"]}) in ev
    sys_msg, user_msg = models.seen[1]
    assert sys_msg["content"] == settings.CLARIFY_PROMPT
    content = user_msg["content"]
    assert "共 0 个完整回合" in content and "（无）" in content
    assert "停止原因：router_unclear" in content
    assert "当前原句：那个呢？" in content
    assert pipe.calls == []
    assert logs.rows[done["exec_id"]]["biz_result"] == "clarify"


@pytest.mark.parametrize("raw,ok", [
    ('{"clarification": "你指的是哪个功能？"}', True),
    ('```json\n{"clarification": "你指的是哪个功能？"}\n```', True),
    ('{"clarification": "问题", "candidates": []}', False),
    ('{"clarification": "  "}', False),
    ('{"clarification": 1}', False),
    ("你指的是哪个功能？", False),
])
def test_q12_clarification_output_schema(raw, ok):
    """S01 §7.9：合法 JSON，唯一字段 clarification，值为非空字符串。"""
    if ok:
        assert parse_clarification(raw) == "你指的是哪个功能？"
        return
    with pytest.raises(BranchError) as info:
        parse_clarification(raw)
    assert info.value.code == "clarify_invalid"


@pytest.mark.parametrize("route,reply,code", [
    ("unclear", ModelError("llm_fail", "模型请求失败：timeout"), "clarify_fail"),
    ("unclear", "不是 JSON", "clarify_invalid"),
    ("smalltalk", "   ", "smalltalk_fail"),
])
def test_q12_branch_failure_is_exec_error(env, monkeypatch, tmp_path, route, reply, code):
    """分支模型失败是执行异常：如实提示、不写成反问、不转知识链路；诊断记模型异常。"""
    client, models, logs, pipe, msgs = env["client"], env["models"], env["logs"], env["pipe"], env["msgs"]
    diag = main.DiagLog(tmp_path)
    monkeypatch.setattr(main, "diag", diag)
    cid = _new_conv(client)
    models.replies = [_router_json(route, False), reply]
    err = _last(_ask(client, cid, "那个呢？", "bf-" + code), "error")
    assert err["type"] == code
    assert "？" not in err["message"]
    assert pipe.calls == []
    row = logs.rows[err["exec_id"]]
    assert row["exec_state"] == "failed"
    assert row["error_type"] == code
    saved = _assistant_rows(msgs, cid)
    assert saved[0]["completeness"] == "error_notice"
    events, _ = diag.events()
    assert [(e["type"], e["code"]) for e in events] == [("model_error", f"{route}:{code}")]
    # 执行权已释放：同会话下一问能正常开始
    models.replies = [_router_json("ack", False)]
    assert _last(_ask(client, cid, "好的", "bf-next-" + code), "done")["status"] == "success"


def test_q12_at23_knowledge_outage_does_not_block_ack(env, monkeypatch):
    """AT-23 / CSTR-Q06：Qdrant 不可用时 ack 照常回复且不 ping 知识索引；知识查询仍按原检查报索引未就绪。"""
    client, models = env["client"], env["models"]
    pings: list[int] = []

    def down() -> bool:
        pings.append(1)
        return False

    monkeypatch.setattr(main, "_fail_type", _REAL_FAIL_TYPE)
    monkeypatch.setattr(main, "missing_keys", lambda: [])
    monkeypatch.setattr(main.store, "ping", down)
    monkeypatch.setattr(main.store, "chunk_count", lambda: 0)
    cid = _new_conv(client)
    models.replies = [_router_json("ack", False)]
    done = _last(_ask(client, cid, "好的，谢谢", "at23-1"), "done")
    assert done["status"] == "success" and done["text"] in settings.ACK_REPLY_POOL
    assert pings == []
    models.replies = [_router_json("knowledge_query", False)]
    err = _last(_ask(client, cid, "VIP 保级规则是什么？", "at23-2"), "error")
    assert err["type"] == "index_not_ready"
    assert pings == [1]


def test_q12_time_context_and_frontend_stages():
    """时间基准取原问题提问时间，未知时如实说明；前端有两个分支的阶段文案。"""
    assert "未知" in time_context(None)
    # G-E08：UTC 存储时间按显示时区换算
    assert "2026-09-29 16:00（Asia/Shanghai）" in time_context("2026-09-29 08:00:00")
    assert 'smalltalk: "回复中…"' in QA_JS
    assert 'clarify: "整理澄清问题…"' in QA_JS


# ---------------- STEP-Q13 ----------------

def test_q13_schema_accepts_valid_prep():
    got = parse_task_prep(_prep_json(
        [_task("T1", "查 VIP 保级规则", constraints=["用表格"]), _task("T2", "对照 A/B", mode="对照",
                                                                    depends_on=["T1"], gap_ids=["G1"],
                                                                    check="needs_user_input")],
        excluded=[{"text": "设计新机制", "reason": "out_of_scope"}],
        gaps=[_gap("G1", ["T2"], clue="要对照的另一个渠道")],
        rc="表格", note="x",
    ))
    assert [t["task_id"] for t in got["tasks"]] == ["T1", "T2"]
    assert got["tasks"][0]["constraints"] == ["用表格"]
    assert got["excluded"][0]["text"] == "设计新机制"
    assert got["information_gaps"][0]["gap_id"] == "G1"
    assert got["extra_keys"] == ["note"]
    fenced = "```json\n" + _prep_json([_task("T1", "查规则")]) + "\n```"
    assert parse_task_prep(fenced)["tasks"][0]["goal"] == "查规则"
    assert len(TASK_CHECKS) == 8


@pytest.mark.parametrize("raw,detail", [
    ("不是 JSON", "not_json"),
    ("[]", "not_object"),
    (json.dumps({"tasks": [], "excluded": [], "information_gaps": []}), "missing:response_constraint"),
    (_prep_json([]), "no_task"),
    (_prep_json([_task("T1", "查", mode="设计")]), "mode"),
    (_prep_json([_task("T1", "查", check="knowledge_insufficient")]), "check"),
    (_prep_json([_task("T1", "")]), "goal"),
    (_prep_json([_task("T1", "查"), _task("T1", "再查")]), "task_id"),
    (_prep_json([_task("X1", "查")]), "task_id"),
    (_prep_json([_task("T1", "查", depends_on=["T9"])]), "depends_on"),
    (_prep_json([_task("T1", "查", depends_on=["T2"]), _task("T2", "查", depends_on=["T1"])]), "depends_cycle"),
    (_prep_json([_task("T1", "查", gap_ids=["G9"])]), "gap_ids"),
    (_prep_json([_task("T1", "查")], gaps=[_gap("G1", ["T9"])]), "gap_task_ids"),
    (_prep_json([_task("T1", "查")], gaps=[_gap("G1", ["T1"], type_="x")]), "gap_type"),
    (_prep_json([_task(f"T{i}", "查") for i in range(1, 8)]), "too_many_tasks"),
])
def test_q13_schema_rejects_illegal_prep(raw, detail):
    with pytest.raises(TaskPrepError) as info:
        parse_task_prep(raw)
    assert info.value.code == "task_prep_invalid"
    assert info.value.detail == detail


def test_q13_empty_prep_response_is_call_failure():
    with pytest.raises(TaskPrepError) as info:
        parse_task_prep("  ")
    assert info.value.code == "task_prep_fail"


def test_q13_c36_comparison_missing_side_is_not_completed():
    """C36：只找到 A 却要 A/B 对照 → 对照任务依赖未就绪，不冒充完成。"""
    settled = settle(parse_task_prep(_prep_json([
        _task("T1", "查 A 渠道退款规则"),
        _task("T2", "查 B 渠道退款规则", check="needs_history", gap_ids=["G1"]),
        _task("T3", "对照 A/B 退款规则", mode="对照", depends_on=["T1", "T2"]),
    ], gaps=[_gap("G1", ["T2"], type_="history_object", clue="此前提到的 B 渠道")])))
    checks = {t["task_id"]: t["check"] for t in settled["tasks"]}
    assert checks == {"T1": "ready", "T2": "needs_history", "T3": "blocked_by_dependency"}
    assert settled["outcome"] == "run" and settled["partial"] is True
    brief = task_brief(settled)
    assert "[执行] T1" in brief
    assert f"[未完成] T2 查询：查 B 渠道退款规则：{HISTORY_UNSUPPORTED}" in brief
    assert "[未完成] T3 对照：对照 A/B 退款规则：依赖的「查 B 渠道退款规则」尚未完成" in brief
    assert "不得写成已完成" in brief and "没有规则" in brief


def test_q13_at01_constraints_reach_generate(env):
    """AT-01：独立的表格/对照约束实际送达 Rewrite 与 Generate（requires_history=false 也有任务准备）。"""
    client, models, prep, pipe, logs = env["client"], env["models"], env["prep"], env["pipe"], env["logs"]
    cid = _new_conv(client)
    models.replies = [_router_json("knowledge_query", False)]
    prep.replies = [_prep_json(
        [_task("T1", "对照 VIP 与 SVIP 的保级规则", mode="对照", constraints=["用表格对照"])], rc="表格输出",
    )]
    done = _last(_ask(client, cid, "用表格对照 VIP 和 SVIP 的保级规则", "at01"), "done")
    assert done["status"] == "success"
    assert "requires_history=false" in prep.seen[-1][1]["content"]
    rewrite_cfg, gen_cfg = pipe.cfgs
    for cfg in (rewrite_cfg, gen_cfg):
        assert "用表格对照" in cfg["_task_brief"] and "回答约束：表格输出" in cfg["_task_brief"]
    row = logs.rows[done["exec_id"]]
    assert row["biz_result"] == "answered"
    assert row["task_prep"]["valid"] is True
    assert row["task_prep"]["outcome"] == "run"
    assert row["task_prep"]["tasks"][0]["constraints"] == ["用表格对照"]
    # 真实 Pipeline 组装的消息里确有这段说明；无任务说明时不变
    real = Pipeline(None, None, lambda: {})
    block = {"path": "a.md", "chunk_id": "c1", "content": "正文", "feature_id": "vip"}
    user = real.generate_messages("原句", {"rewrite_query": "q"}, [block], gen_cfg)[1]["content"]
    assert "用表格对照" in user and user.index("回答约束") < user.index("本轮生成集")
    plain = real.generate_messages("原句", {"rewrite_query": "q"}, [block], {})[1]["content"]
    assert "本轮任务" not in plain
    assert "用表格对照" in build_rewrite_user("原句", [], task_brief=gen_cfg["_task_brief"])
    assert "本轮任务" not in build_rewrite_user("原句", [])


def test_q13_c37_partial_delivery_marks_partial(env):
    """C37：三项独立任务一项缺语境 → 交付两项、说明第三项原因，业务结果记部分完成。"""
    client, models, prep, pipe, logs = env["client"], env["models"], env["prep"], env["pipe"], env["logs"]
    cid = _new_conv(client)
    models.replies = [_router_json("knowledge_query", True)]
    prep.replies = [_prep_json([
        _task("T1", "查 VIP 保级规则"), _task("T2", "查 SVIP 保级规则"),
        _task("T3", "查此前说的那个渠道的退款规则", check="needs_history", gap_ids=["G1"]),
    ], gaps=[_gap("G1", ["T3"], type_="history_object", clue="较早提到的渠道")])]
    done = _last(_ask(client, cid, "VIP、SVIP 保级规则，还有之前那个渠道的退款", "c37"), "done")
    assert done["status"] == "success"
    brief = pipe.cfgs[-1]["_task_brief"]
    assert brief.count("[执行]") == 2 and brief.count("[未完成]") == 1
    assert HISTORY_UNSUPPORTED in brief
    row = logs.rows[done["exec_id"]]
    assert row["biz_result"] == "partial"
    assert row["task_prep"]["partial"] is True
    assert [t["check"] for t in row["task_prep"]["tasks"]] == ["ready", "ready", "needs_history"]


def test_q13_rq03_mixed_out_of_scope_part_not_executed(env):
    """RQ-03：「整理保级规则，再设计新机制」只执行整理，设计部分标不执行。"""
    client, models, prep, pipe, logs = env["client"], env["models"], env["prep"], env["pipe"], env["logs"]
    cid = _new_conv(client)
    models.replies = [_router_json("knowledge_query", False)]
    prep.replies = [_prep_json(
        [_task("T1", "整理现有 VIP 保级规则", mode="整理")],
        excluded=[{"text": "设计新的保级机制", "reason": "out_of_scope"}],
    )]
    done = _last(_ask(client, cid, "整理现有保级规则，再设计新机制", "rq03"), "done")
    brief = pipe.cfgs[-1]["_task_brief"]
    assert "[执行] T1 整理：整理现有 VIP 保级规则" in brief
    assert "[不执行] 设计新的保级机制：超出当前支持范围，未执行" in brief
    assert logs.rows[done["exec_id"]]["biz_result"] == "partial"


def test_q13_at04_missing_user_condition_clarifies_without_search(env):
    """AT-04：缺用户必须指定的条件 → 针对性澄清，不检索，不伪装成历史缺口。"""
    client, models, prep, pipe, logs = env["client"], env["models"], env["prep"], env["pipe"], env["logs"]
    cid = _new_conv(client)
    models.replies = [
        _router_json("knowledge_query", False),
        json.dumps({"clarification": "你想查哪个国家/地区的充值渠道？"}, ensure_ascii=False),
    ]
    prep.replies = [_prep_json(
        [_task("T1", "查充值渠道手续费", check="needs_user_input", gap_ids=["G1"])],
        gaps=[_gap("G1", ["T1"], clue="国家/地区")],
    )]
    ev = _ask(client, cid, "充值手续费多少？", "at04")
    done = _last(ev, "done")
    assert done["text"] == "你想查哪个国家/地区的充值渠道？"
    assert pipe.calls == []
    content = models.seen[-1][1]["content"]
    assert models.seen[-1][0]["content"] == settings.CLARIFY_PROMPT
    assert "尚未解决的信息点：\n- 查充值渠道手续费：国家/地区" in content
    assert "停止原因：task_needs_user_input" in content
    row = logs.rows[done["exec_id"]]
    assert row["biz_result"] == "clarify"
    assert row["used_knowledge_rag"] is False
    assert row["task_prep"]["outcome"] == "clarify"


def test_q13_only_history_gap_reports_unfinished(env):
    """只剩缺较早历史的任务：如实说明未完成，不检索、不调模型、不改说成澄清。"""
    client, models, prep, pipe, logs = env["client"], env["models"], env["prep"], env["pipe"], env["logs"]
    cid = _new_conv(client)
    models.replies = [_router_json("knowledge_query", True)]
    prep.replies = [_prep_json([_task("T1", "查上周说的那个活动规则", check="needs_history")])]
    done = _last(_ask(client, cid, "上周说的那个活动规则呢？", "hist"), "done")
    assert done["text"] == f"本轮未能完成：\n- 查上周说的那个活动规则：{HISTORY_UNSUPPORTED}"
    assert pipe.calls == [] and len(models.seen) == 1
    assert logs.rows[done["exec_id"]]["biz_result"] == "insufficient"


def test_q13_all_excluded_uses_out_of_scope_pool(env):
    client, models, prep, pipe, logs = env["client"], env["models"], env["prep"], env["pipe"], env["logs"]
    cid = _new_conv(client)
    models.replies = [_router_json("knowledge_query", False)]
    prep.replies = [_prep_json([], excluded=[{"text": "评审保级设计哪里不好", "reason": "out_of_scope"}])]
    done = _last(_ask(client, cid, "评审一下保级设计哪里不好", "allx"), "done")
    assert done["text"] in settings.OUT_OF_SCOPE_REPLY_POOL
    assert pipe.calls == []
    assert logs.rows[done["exec_id"]]["biz_result"] == "refused"


def _no_l1(*_a, **_k):
    return {"turns": [], "tokens": 0, "window": [], "reason": "empty", "not_loaded": 0, "incomplete": 0}


def test_q13_at08_answer_after_clarify_carries_original_task(env, monkeypatch):
    """AT-08：澄清回合已滚出 L1，用户答「第二个」→ 从消息与 Runtime 恢复原任务与候选，交给 Router 与任务准备。"""
    client, models, prep, pipe, logs = env["client"], env["models"], env["prep"], env["pipe"], env["logs"]
    cid = _new_conv(client)
    models.replies = [
        _router_json("knowledge_query", False),
        json.dumps({"clarification": "你说的等级是 VIP 还是靓号档？"}, ensure_ascii=False),
    ]
    prep.replies = [_prep_json(
        [_task("T1", "查等级的保级规则", check="ambiguous", gap_ids=["G1"])],
        gaps=[_gap("G1", ["T1"], type_="candidate_choice", clue="等级指哪一套", candidates=["VIP", "靓号档"])],
    )]
    first = _ask(client, cid, "等级的保级规则是什么？", "at08-1")
    first_exec = _last(first, "done")["exec_id"]
    assert logs.rows[first_exec]["biz_result"] == "clarify"

    monkeypatch.setattr(main, "assemble_l1", _no_l1)
    models.replies = [_router_json("knowledge_query", True)]
    prep.replies = [_prep_json([_task("T1", "查靓号档的保级规则")])]
    done = _last(_ask(client, cid, "第二个", "at08-2"), "done")
    assert done["status"] == "success"
    router_in = models.seen[-1][1]["content"]
    assert "共 0 个完整回合" in router_in
    assert "承接线索：\n上一轮结果：澄清" in router_in
    assert "原任务原句：等级的保级规则是什么？" in router_in
    assert "上一轮回复：你说的等级是 VIP 还是靓号档？" in router_in
    assert "候选：VIP、靓号档" in router_in
    prep_in = prep.seen[-1][1]["content"]
    assert "原任务原句：等级的保级规则是什么？" in prep_in and prep_in.endswith("当前原句：第二个\n\n只输出 JSON。")
    row = logs.rows[done["exec_id"]]
    assert row["task_prep"]["carry"] == {
        "from_exec_id": first_exec, "from_logical_round_id": _last(first, "accepted")["logical_round_id"],
    }
    # 第一轮澄清不检索；承接后的第二轮才检索
    assert [c[0] for c in pipe.calls].count("retrieve") == 1
    assert "查靓号档的保级规则" in pipe.cfgs[-1]["_task_brief"]


def test_q13_carry_only_after_clarify_or_partial_and_not_across_clear(env):
    """上一轮已正常回答不承接；清空后旧澄清不可承接。"""
    client, models, prep = env["client"], env["models"], env["prep"]
    cid = _new_conv(client)
    _ask(client, cid, "VIP 保级规则是什么？", "cw-1")
    _ask(client, cid, "那 SVIP 呢？", "cw-2")
    assert "承接线索：（无）" in prep.seen[-1][1]["content"]

    models.replies = [_router_json("unclear", False), json.dumps({"clarification": "你指哪个？"}, ensure_ascii=False)]
    _ask(client, cid, "那个呢？", "cw-3")
    assert client.post(f"/api/kb/conversations/{cid}/clear").status_code == 200
    _ask(client, cid, "第二个", "cw-4")
    assert "承接线索：（无）" in prep.seen[-1][1]["content"]
    assert "承接线索" not in models.seen[-1][1]["content"]


def test_q13_carry_after_router_unclear_without_tasks(env):
    """Router unclear 的澄清没有任务集，也按原句与澄清消息承接。"""
    client, models, prep = env["client"], env["models"], env["prep"]
    cid = _new_conv(client)
    models.replies = [_router_json("unclear", False), json.dumps({"clarification": "你指哪个功能？"}, ensure_ascii=False)]
    _ask(client, cid, "那个呢？", "ru-1")
    _ask(client, cid, "VIP", "ru-2")
    prep_in = prep.seen[-1][1]["content"]
    assert "原任务原句：那个呢？" in prep_in and "上一轮回复：你指哪个功能？" in prep_in
    assert "未完成项" not in prep_in


@pytest.mark.parametrize("reply,code", [
    ("不是 JSON", "task_prep_invalid"),
    (ModelError("llm_fail", "timeout"), "task_prep_fail"),
])
def test_q13_prep_failure_is_exec_error(env, monkeypatch, tmp_path, reply, code):
    """任务准备失败/非法：执行异常，不降级为单任务、不检索、不重试；error_notice 落库并记诊断。"""
    client, models, prep, pipe, logs, msgs = (
        env["client"], env["models"], env["prep"], env["pipe"], env["logs"], env["msgs"],
    )
    diag = main.DiagLog(tmp_path)
    monkeypatch.setattr(main, "diag", diag)
    cid = _new_conv(client)
    models.replies = [_router_json("knowledge_query", False)]
    prep.replies = [reply]
    err = _last(_ask(client, cid, "VIP 保级规则是什么？", "pf-" + code), "error")
    assert err["type"] == code
    assert pipe.calls == []
    assert len(prep.seen) == 1
    row = logs.rows[err["exec_id"]]
    assert row["task_prep"]["valid"] is False and row["task_prep"]["error"] == code
    assert row["exec_state"] == "failed"
    assert _assistant_rows(msgs, cid)[0]["completeness"] == "error_notice"
    assert [(e["type"], e["code"]) for e in diag.events()[0]] == [("model_error", f"task_prep:{code}")]


def test_q13_non_run_outcomes_skip_knowledge_check(env, monkeypatch):
    """澄清出口不依赖知识索引：Qdrant 不可用时照常澄清。"""
    client, models, prep = env["client"], env["models"], env["prep"]
    monkeypatch.setattr(main, "_fail_type", _REAL_FAIL_TYPE)
    monkeypatch.setattr(main, "missing_keys", lambda: [])
    monkeypatch.setattr(main.store, "ping", lambda: False)
    monkeypatch.setattr(main.store, "chunk_count", lambda: 0)
    cid = _new_conv(client)
    models.replies = [_router_json("knowledge_query", False), json.dumps({"clarification": "哪个国家？"}, ensure_ascii=False)]
    prep.replies = [_prep_json([_task("T1", "查手续费", check="needs_user_input")])]
    assert _last(_ask(client, cid, "手续费多少？", "nk-1"), "done")["text"] == "哪个国家？"


def test_q13_prompt_storage_and_frontend():
    msgs = build_prep_messages("原句", [], "knowledge_query", False)
    assert msgs[0]["content"] == settings.TASK_PREP_PROMPT
    assert "承接线索：（无）" in msgs[1]["content"]
    for word in ("needs_user_input", "excluded", "response_constraint", "已交付项不要重做"):
        assert word in settings.TASK_PREP_PROMPT
    assert ("task_prep", "JSON NULL") in RUNTIME_COLUMNS
    assert "task_prep" in RUNTIME_JSON_FIELDS
    assert "task_prep JSON NULL" in INIT_SQL
    assert 'task_prep: "梳理任务中…"' in QA_JS


# ---------------- STEP-Q17 ----------------

def _rw_json(status="ready", query="VIP 保级规则是什么", named=None, same=False, missing=None, rc="", conf=0.9, **extra):
    obj = {"status": status, "standalone_query": query, "response_constraint": rc,
           "missing_context": missing or [], "confidence": conf,
           "named_feature_ids": named or [], "same_topic": same}
    obj.update(extra)
    return json.dumps(obj, ensure_ascii=False)


def _rw(status="ready", query="VIP 保级规则是什么", missing=None, rc=""):
    return {"status": status, "standalone_query": query, "rewrite_query": query, "same_topic": False,
            "named_feature_ids": [], "response_constraint": rc, "missing_context": missing or [],
            "confidence": 0.9, "extra_keys": [], "prompt_ver": "rewrite-v3"}


class _RwModels:
    def __init__(self, reply):
        self.reply = reply
        self.seen: list[list[dict]] = []

    async def rewrite(self, messages, temperature):
        self.seen.append(messages)
        return self.reply


def test_q17_schema_maps_to_legacy_fields():
    got = parse_rewrite_v3(_rw_json(named=["vip", "coupon", "不存在的功能"], same=True, rc="用表格", answer="知识库没有该规则"))
    assert got["rewrite_query"] == got["standalone_query"] == "VIP 保级规则是什么"
    assert got["named_feature_ids"] == ["vip", "coupon"]
    assert got["same_topic"] is True
    assert got["response_constraint"] == "用表格"
    # AT-35：Rewriter 未检索就下的知识结论不采信，只记字段名
    assert got["extra_keys"] == ["answer"]
    needs = parse_rewrite_v3(_rw_json("needs_context", "不该有的问句",
                                      missing=[{"task_id": "T1", "type": "history_object", "clue": "此前的渠道"}]))
    assert needs["standalone_query"] == "" and needs["rewrite_query"] == ""


@pytest.mark.parametrize("raw,detail", [
    ("", "empty_response"),
    ("不是 JSON", "not_json"),
    (json.dumps({"rewrite_query": "旧格式", "same_topic": False, "named_feature_ids": []}), "missing:status"),
    (_rw_json(status="done"), "status"),
    (_rw_json(query="  "), "empty_query"),
    (_rw_json(conf=1.5), "confidence"),
    (_rw_json(conf=True), "confidence"),
    (_rw_json(same="false"), "same_topic"),
    (_rw_json(named="vip"), "named_feature_ids"),
    (_rw_json(missing=[{"task_id": "T1", "type": "history_object", "clue": "x"}]), "ready_with_missing"),
    (_rw_json("needs_context", ""), "needs_context_without_gap"),
    (_rw_json("needs_context", "", missing=[{"task_id": "T1", "type": "knowledge", "clue": "x"}]), "missing_context"),
])
def test_q17_schema_rejects_illegal_output(raw, detail):
    with pytest.raises(RewriteInvalid) as info:
        parse_rewrite_v3(raw)
    assert info.value.detail == detail


def test_q17_missing_context_must_point_to_allowed_task():
    raw = _rw_json("needs_context", "", missing=[{"task_id": "T9", "type": "user_condition", "clue": "国家"}])
    with pytest.raises(RewriteInvalid) as info:
        parse_rewrite_v3(raw, ["T1"])
    assert info.value.detail == "missing_context_task"


@pytest.mark.anyio
async def test_q17_single_rewrite_entry_uses_code_prompt():
    """唯一 Rewrite 入口：用代码内 v3 Prompt，不被 /config 旧 rewrite_prompt 覆盖；L1 与任务说明进入输入。"""
    models = _RwModels(_rw_json(query="YallaPay 链接支付的退款规则", named=["yallapay"], same=True))
    pipe = Pipeline(None, models, lambda: {})
    cfg = {"rewrite_prompt": "旧后台 Prompt", "history_turns": 5, "_task_brief": "本轮任务：- [执行] T1 查询：退款"}
    got = await pipe.rewrite("那退款呢？", [{"role": "user", "text": "YallaPay 链接支付怎么用"},
                                            {"role": "assistant", "text": "链接支付说明……"}], cfg)
    sys_msg, user_msg = models.seen[0]
    assert sys_msg["content"] == settings.REWRITE_V3_PROMPT
    assert "旧后台 Prompt" not in sys_msg["content"]
    assert "user: YallaPay 链接支付怎么用" in user_msg["content"]
    assert "本轮任务：- [执行] T1 查询：退款" in user_msg["content"]
    # C03：独立问句只含本场景，映射给旧 Pipeline
    assert got["rewrite_query"] == "YallaPay 链接支付的退款规则"
    assert got["named_feature_ids"] == ["yallapay"]


class _LaneStore:
    def __init__(self):
        self.calls: list[dict] = []

    def hybrid_search(self, query_text, vector, k, collections=None, feature_id=None):
        self.calls.append({"feature_id": feature_id, "collections": list(collections or [])})
        return [{"path": f"{feature_id or 'all'}.md", "chunk_id": "c1", "feature_id": feature_id or "vip"}]


class _EmbedModels:
    async def embed(self, texts):
        return [[0.0] * 4 for _ in texts]


@pytest.mark.anyio
async def test_q17_at02_multi_feature_routing_kept():
    """AT-02：新 JSON 接旧 Pipeline 后多功能分路与保底不丢。"""
    rw = parse_rewrite_v3(_rw_json(query="VIP 与体验券规则", named=["vip", "coupon"]))
    store = _LaneStore()
    pipe = Pipeline(store, _EmbedModels(), lambda: {})
    got = await pipe.retrieve("VIP 和体验券", rw["rewrite_query"], rw["named_feature_ids"], {})
    assert got["mode"] == "multi"
    assert [c["feature_id"] for c in store.calls] == ["vip", "coupon"]
    assert "VIP 与体验券规则" in got["query_text"]


def test_q17_c33_at03_needs_context_does_not_retrieve(env):
    """C33 / AT-03：requires_history=false 但 Rewriter 发现历史指代 → needs_context，不检索空串、
    不重跑 Router、不再次改写、不调用 Memory；调用计数写入 Runtime。"""
    client, models, pipe, logs = env["client"], env["models"], env["pipe"], env["logs"]
    cid = _new_conv(client)
    models.replies = [_router_json("knowledge_query", False)]
    pipe.rw = _rw("needs_context", "", missing=[{"task_id": "T1", "type": "history_object", "clue": "此前提到的渠道"}])
    done = _last(_ask(client, cid, "那个渠道的退款怎么算？", "c33"), "done")
    assert [c[0] for c in pipe.calls] == ["rewrite"]
    assert len(models.seen) == 1
    assert HISTORY_UNSUPPORTED in done["text"] and "此前提到的渠道" in done["text"]
    row = logs.rows[done["exec_id"]]
    assert row["biz_result"] == "missing_context"
    assert row["used_knowledge_rag"] is False
    assert row["rewrite"]["status"] == "needs_context"
    # Q16 起计数另含追溯判断与 Memory 调用；预算未配置时不启用，二者为 0
    assert row["call_usage"] == {"router": 1, "task_prep": 1, "rewrite": 1, "smalltalk": 0, "clarify": 0,
                                 "generate": 0, "check": 0, "repair": 0, "recall": 0, "memory": 0}


def test_q17_needs_context_user_condition_clarifies(env):
    client, models, pipe, logs = env["client"], env["models"], env["pipe"], env["logs"]
    cid = _new_conv(client)
    models.replies = [_router_json("knowledge_query", False),
                      json.dumps({"clarification": "你想查哪个国家的渠道？"}, ensure_ascii=False)]
    pipe.rw = _rw("needs_context", "", missing=[{"task_id": "T1", "type": "user_condition", "clue": "国家"}])
    done = _last(_ask(client, cid, "手续费多少", "q17-uc"), "done")
    assert done["text"] == "你想查哪个国家的渠道？"
    assert "尚未解决的信息点：\n- 按原句查询规则：国家" in models.seen[-1][1]["content"]
    assert "停止原因：rewrite_needs_context" in models.seen[-1][1]["content"]
    assert [c[0] for c in pipe.calls] == ["rewrite"]
    row = logs.rows[done["exec_id"]]
    assert row["biz_result"] == "clarify"
    assert row["call_usage"]["clarify"] == 1 and row["call_usage"]["rewrite"] == 1


def test_q17_invalid_output_is_rewrite_fail(env, monkeypatch, tmp_path):
    client, models, pipe, logs = env["client"], env["models"], env["pipe"], env["logs"]
    monkeypatch.setattr(main, "diag", main.DiagLog(tmp_path))
    cid = _new_conv(client)
    models.replies = [_router_json("knowledge_query", False)]
    pipe.rw = RewriteInvalid("empty_query", '{"status":"ready","standalone_query":""}')
    err = _last(_ask(client, cid, "VIP 规则", "q17-bad"), "error")
    assert err["type"] == "rewrite_fail"
    assert [c[0] for c in pipe.calls] == ["rewrite"]
    row = logs.rows[err["exec_id"]]
    assert row["rewrite"]["valid"] is False and row["rewrite"]["detail"] == "empty_query"
    assert row["call_usage"]["rewrite"] == 1


def test_q17_ready_records_rewrite_and_usage(env):
    client, models, pipe, logs = env["client"], env["models"], env["pipe"], env["logs"]
    cid = _new_conv(client)
    models.replies = [_router_json("knowledge_query", False)]
    pipe.rw = _rw(query="VIP 保级规则", rc="简短")
    done = _last(_ask(client, cid, "VIP 保级？", "q17-ok"), "done")
    row = logs.rows[done["exec_id"]]
    assert row["rewrite_query"] == "VIP 保级规则"
    assert row["rewrite"]["status"] == "ready" and row["rewrite"]["response_constraint"] == "简短"
    assert row["call_usage"]["rewrite"] == 1 and row["call_usage"]["generate"] == 1
    assert ("retrieve", "VIP 保级规则") in pipe.calls
    for col in ("rewrite JSON NULL", "call_usage JSON NULL", "evidence_check JSON NULL"):
        assert col in INIT_SQL
    assert {"rewrite", "call_usage", "evidence_check"} <= set(RUNTIME_JSON_FIELDS)


# ---------------- STEP-Q18 ----------------

_BLOCK = {"path": "prd/design/vip/brief/current.md", "chunk_id": "vip.keep", "feature_id": "vip",
          "content": "VIP 保级按月计算。", "content_hash": "h-vip"}


def _answered_round(client, models, cid, question, answer, crid):
    """先做一轮正常回答，让下一问的 L1 里有这条回答。"""
    models.replies = [_router_json("knowledge_query", False)]
    return _ask(client, cid, question, crid)


def test_q18_c02_history_answer_and_no_repeat_reach_generate(env):
    """C02：「还有么」→ Generate 同时收到此前实际回答与不重复约束。"""
    client, models, pipe = env["client"], env["models"], env["pipe"]
    cid = _new_conv(client)
    pipe.answer = "VIP 有专属标识与金色昵称。"
    _answered_round(client, models, cid, "VIP 有哪些权益？", pipe.answer, "c02-1")
    models.replies = [_router_json("knowledge_query", True)]
    pipe.rw = _rw(query="VIP 除标识与金色昵称外的其他权益", rc="不重复此前已答内容")
    pipe.answer = "另有发图片权限。"
    done = _last(_ask(client, cid, "还有么？", "c02-2"), "done")
    assert done["status"] == "success"
    handoff = pipe.cfgs[-1]["_handoff"]
    assert handoff["avoid_repeat"] is True
    assert "Assistant: VIP 有专属标识与金色昵称。" in handoff["history"][0]
    user = Pipeline(None, None, lambda: {}).generate_messages(
        "还有么？", pipe.rw, [_BLOCK], pipe.cfgs[-1])[1]["content"]
    assert "改写给出的回答约束：不重复此前已答内容" in user
    assert "相关历史对话" in user and "VIP 有专属标识与金色昵称。" in user


def test_q18_c10_verification_target_is_previous_answer(env):
    """C10：核验上一条回答 → 带目标回答原文进入 Generate。"""
    client, models, prep, pipe = env["client"], env["models"], env["prep"], env["pipe"]
    cid = _new_conv(client)
    pipe.answer = "退款当天到账。"
    _answered_round(client, models, cid, "退款多久到账？", pipe.answer, "c10-1")
    models.replies = [_router_json("knowledge_query", True)]
    prep.replies = [_prep_json([_task("T1", "核验上一条关于退款到账时间的说法", mode="核验")])]
    _last(_ask(client, cid, "你刚才的退款说法有依据吗？", "c10-2"), "done")
    handoff = pipe.cfgs[-1]["_handoff"]
    assert handoff["verify"] is True
    assert handoff["verification_target"] == "退款当天到账。"
    user = Pipeline(None, None, lambda: {}).generate_messages(
        "你刚才的退款说法有依据吗？", _rw(), [_BLOCK], pipe.cfgs[-1])[1]["content"]
    assert "核验目标（被核验的此前回答原文）：\n退款当天到账。" in user
    # C35：新证据推翻历史结论时先更正
    assert "先明确更正" in user


@pytest.mark.parametrize("task_mode,rc,gap", [
    ("查询", "别重复之前说的", "此前回答原文（要求不重复）"),
    ("核验", "", "被核验的此前回答原文"),
])
def test_q18_c34_contract_fails_without_history(env, task_mode, rc, gap):
    """C34：要求不重复/核验但没有可用的此前回答 → 合同校验失败，不检索、不生成、不当正常通过。"""
    client, models, prep, pipe, logs = env["client"], env["models"], env["prep"], env["pipe"], env["logs"]
    cid = _new_conv(client)
    models.replies = [_router_json("knowledge_query", False)]
    prep.replies = [_prep_json([_task("T1", "查退款规则", mode=task_mode)])]
    pipe.rw = _rw(query="退款规则", rc=rc)
    err = _last(_ask(client, cid, "退款规则？", "c34-" + task_mode), "error")
    assert err["type"] == "generate_contract_fail"
    assert gap in err["message"]
    assert [c[0] for c in pipe.calls] == ["rewrite"]
    assert logs.rows[err["exec_id"]]["exec_state"] == "failed"


def test_q18_at22_excerpt_marked_and_hash_not_reused():
    """AT-22：回源失败只剩片段 → 明确标片段、不带 hash；回源成功时 hash 换成本次正文的 hash。"""
    from app.pipeline import fill_block_content, public_c_gen

    prev = {"path": "a.md", "chunk_id": "c1", "excerpt": "旧片段", "content_hash": "old-hash"}
    only_excerpt = fill_block_content(prev, store=None)
    assert only_excerpt["content_scope"] == "excerpt" and only_excerpt["content_hash"] == ""

    class Store:
        def lookup_payload(self, path, chunk_id):
            return {"path": path, "chunk_id": chunk_id, "content": "新正文", "content_hash": "new-hash"}

    refilled = fill_block_content(prev, Store())
    assert refilled["content"] == "新正文" and refilled["content_hash"] == "new-hash"
    assert refilled["content_scope"] == "full"
    user = Pipeline(None, None, lambda: {}).generate_messages("问", _rw(), [only_excerpt, refilled], {})[1]["content"]
    assert "正文范围：片段（非全文）\n旧片段" in user
    assert "content_hash=new-hash" in user and "old-hash" not in user
    assert public_c_gen([only_excerpt])[0]["content_scope"] == "excerpt"
    assert "content" not in public_c_gen([refilled])[0]


def test_q18_c32_time_and_version_limit_in_generate(env):
    """C32：问「去年规则」时生成输入带本地提问时间与知识版本限制，不用聊天时间替代规则版本。"""
    client, models, pipe = env["client"], env["models"], env["pipe"]
    cid = _new_conv(client)
    models.replies = [_router_json("knowledge_query", False)]
    _last(_ask(client, cid, "去年生效的 VIP 保级规则是什么？", "c32"), "done")
    handoff = pipe.cfgs[-1]["_handoff"]
    assert handoff["time_text"] and handoff["time_text"].endswith("（Asia/Shanghai）")
    user = Pipeline(None, None, lambda: {}).generate_messages("去年？", _rw(), [_BLOCK], pipe.cfgs[-1])[1]["content"]
    assert settings.KNOWLEDGE_VERSION_NOTE in user
    assert "不含历史版本" in settings.KNOWLEDGE_VERSION_NOTE
    assert f"本轮提问时间：{handoff['time_text']}" in user


def test_q18_at17_results_by_actual_knowledge(env):
    """AT-17：零命中 → 依据不足；点名多功能只命中一部分 → 部分有证据。冲突随 Q19 检查。"""
    client, models, pipe, logs = env["client"], env["models"], env["pipe"], env["logs"]
    cid = _new_conv(client)
    models.replies = [_router_json("knowledge_query", False)]
    pipe.rw = dict(_rw(query="VIP 与体验券规则"), named_feature_ids=["vip", "coupon"])
    done = _last(_ask(client, cid, "VIP 和体验券规则", "at17-1"), "done")
    assert logs.rows[done["exec_id"]]["biz_result"] == "partial"
    pipe.blocks = []
    pipe.rw = _rw(query="不存在的规则")
    models.replies = [_router_json("knowledge_query", False)]
    empty = _last(_ask(client, cid, "不存在的规则", "at17-2"), "done")
    assert empty["status"] == "empty"
    assert logs.rows[empty["exec_id"]]["biz_result"] == "insufficient"
    from app.logs import STATUS_ENUMS
    assert {"conflict", "missing_context"} <= STATUS_ENUMS["biz_result"]


def test_q18_citation_recheck_endpoint(env, monkeypatch):
    """S01 §20.2：引用点击复核。hash 一致给正文；不一致 409 不给新正文；读不到 404；未登录 401。"""
    client = env["client"]
    payloads = {("a.md", "c1"): {"path": "a.md", "chunk_id": "c1", "content": "当前正文", "content_hash": "h1",
                                 "heading": "标题", "anchor": "a1", "feature_id": "vip"}}
    monkeypatch.setattr(main.store, "lookup_payload", lambda p, c: dict(payloads[(p, c)]) if (p, c) in payloads else None)
    ok = client.get("/api/kb/chunk", params={"path": "a.md", "chunk_id": "c1", "content_hash": "h1"})
    assert ok.status_code == 200 and ok.json()["content"] == "当前正文"
    changed = client.get("/api/kb/chunk", params={"path": "a.md", "chunk_id": "c1", "content_hash": "h0"})
    assert changed.status_code == 409 and changed.json()["code"] == "source_changed"
    assert "当前正文" not in changed.text
    gone = client.get("/api/kb/chunk", params={"path": "b.md", "chunk_id": "x", "content_hash": "h1"})
    assert gone.status_code == 404 and gone.json()["code"] == "source_not_found"
    assert client.get("/api/kb/chunk", params={"path": "a.md"}).status_code == 400
    client.post("/api/kb/auth/logout")
    assert client.get("/api/kb/chunk", params={"path": "a.md", "chunk_id": "c1"}).status_code == 401
    assert "function checkCitation" in QA_JS and "data-cite-hash" in QA_JS and '"/chunk?"' in QA_JS
    # 旧接口 404 没有业务 code 时仍打开文档；有 code 才拦住
    assert "if (!data.code)" in QA_JS and "openCitation(path, anchor, heading)" in QA_JS


# ---------------- STEP-Q19 ----------------

def _chk(status="pass", issues=None, conflict=False):
    return json.dumps({"check_status": status, "issues": issues or [], "conflict": conflict}, ensure_ascii=False)


def _issue(span, ids=("E1",), reason="证据不支持"):
    return {"answer_span": span, "evidence_ids": list(ids), "reason": reason}


def _assistant_texts(msgs, cid):
    return [r["content"] for r in msgs.effective_messages(cid) if r["role"] == "assistant"]


def test_q19_check_schema():
    ids, draft = ["E1", "E2"], "A 渠道退款需要审核，审核通过后当天到账。"
    ok = parse_check(_chk(), ids, draft)
    assert ok == {"check_status": "pass", "issues": [], "conflict": False}
    bad = parse_check(_chk("fail", [_issue("审核通过后当天到账")]), ids, draft)
    assert bad["issues"][0]["evidence_ids"] == ["E1"]
    assert parse_check(_chk("fail", [_issue("", ids=())]), ids, draft)["issues"][0]["answer_span"] == ""


@pytest.mark.parametrize("raw,code,detail", [
    ("", "check_fail", "empty_response"),
    ("不是 JSON", "check_invalid", "not_json"),
    (json.dumps({"check_status": "pass", "issues": []}), "check_invalid", "missing:conflict"),
    (_chk("maybe"), "check_invalid", "check_status"),
    (_chk("pass", [_issue("当天到账")]), "check_invalid", "status_issues_mismatch"),
    (_chk("fail", []), "check_invalid", "status_issues_mismatch"),
    (_chk("fail", [_issue("当天到账", ids=("E9",))]), "check_invalid", "evidence_ids"),
    (_chk("fail", [_issue("草稿里没有这句")]), "check_invalid", "answer_span"),
    (_chk("fail", [_issue("当天到账", reason="")]), "check_invalid", "issue_fields"),
    (json.dumps({"check_status": "pass", "issues": [], "conflict": "no"}), "check_invalid", "conflict"),
])
def test_q19_check_schema_rejects_illegal(raw, code, detail):
    """超时、空响应、非法 JSON、字段矛盾都是检查异常，不塞成 pass。"""
    with pytest.raises(CheckError) as info:
        parse_check(raw, ["E1"], "审核通过后当天到账。")
    assert (info.value.code, info.value.detail) == (code, detail)


def test_q19_at30_fail_repair_once_then_pass(env):
    """AT-30：草稿含不支持的承诺 → fail → 修正一次 → 复查通过；正式保存修正稿，草稿被替换。"""
    client, models, pipe, logs, msgs, check = (
        env["client"], env["models"], env["pipe"], env["logs"], env["msgs"], env["check"],
    )
    cid = _new_conv(client)
    models.replies = [_router_json("knowledge_query", False)]
    pipe.answer = "A 渠道退款需要审核，审核通过后当天到账。"
    repaired = "A 渠道退款需要审核；本次原文不足以确认当天到账。"
    check.replies = [_chk("fail", [_issue("审核通过后当天到账")]), repaired, _chk("pass")]
    ev = _ask(client, cid, "A 渠道退款要审核吗？当天到账吗？", "at30")
    done = _last(ev, "done")
    assert done["text"] == repaired
    assert _last(ev, "check") == {"check_status": "pass", "replaced": True, "text": repaired, "round_id": done["round_id"]}
    assert ("stage", {"stage": "repair", "round_id": done["round_id"]}) in ev
    assert _assistant_texts(msgs, cid) == [repaired]
    row = logs.rows[done["exec_id"]]
    assert row["check_status"] == "pass"
    rec = row["evidence_check"]
    assert rec["repair_count"] == 1 and [r["check_status"] for r in rec["rounds"]] == ["fail", "pass"]
    # AT-36：通过结论只对应这份正文；保存的正是被检查通过的那份
    assert rec["final_hash"] == draft_hash(repaired) == rec["rounds"][1]["draft_hash"]
    assert rec["evidence"][0]["evidence_id"] == "E1" and "content" not in rec["evidence"][0]
    assert row["call_usage"]["check"] == 2 and row["call_usage"]["repair"] == 1
    # 检查输入：同一份 c_gen、带 E 编号、待检查的是新草稿
    first_in, second_in = check.seen[0][1]["content"], check.seen[2][1]["content"]
    assert "[E1] path=a.md chunk_id=c1\n正文" in first_in
    assert first_in.endswith(f"待检查答案：\n{pipe.answer}\n\n只输出 JSON。")
    assert second_in.endswith(f"待检查答案：\n{repaired}\n\n只输出 JSON。")
    assert "审核通过后当天到账" in check.seen[1][1]["content"]


def test_q19_at39_rejected_twice_not_delivered_and_no_second_repair(env):
    """复查仍失败 → 不修第二次、该项不交付；被否决的草稿不成为正式版本（AT-39）。"""
    client, models, pipe, logs, msgs, check = (
        env["client"], env["models"], env["pipe"], env["logs"], env["msgs"], env["check"],
    )
    cid = _new_conv(client)
    models.replies = [_router_json("knowledge_query", False)]
    pipe.answer = "保级线是 100 金币。"
    check.replies = [_chk("fail", [_issue("保级线是 100 金币")]), "保级线是 100 金币，按月计。",
                     _chk("fail", [_issue("保级线是 100 金币")])]
    ev = _ask(client, cid, "VIP 保级线？", "at39")
    done = _last(ev, "done")
    assert "未能形成可靠回答" in done["text"] and "已修正一次仍未通过" in done["text"]
    assert _last(ev, "check")["check_status"] == "fail" and _last(ev, "check")["replaced"] is True
    texts = _assistant_texts(msgs, cid)
    assert texts == [done["text"]]
    assert all("100 金币" not in t for t in texts)
    row = logs.rows[done["exec_id"]]
    assert row["check_status"] == "fail" and row["biz_result"] == "insufficient"
    assert row["call_usage"]["check"] == 2 and row["call_usage"]["repair"] == 1
    assert len(check.seen) == 3


def test_q19_refresh_failing_check_keeps_current_version(env):
    """刷新出的新结果未通过交付检查 → 不替换原有效默认版本。"""
    client, models, pipe, msgs, check = env["client"], env["models"], env["pipe"], env["msgs"], env["check"]
    cid = _new_conv(client)
    models.replies = [_router_json("knowledge_query", False)]
    pipe.answer = "VIP 保级按月计算。"
    first = _ask(client, cid, "VIP 保级怎么算？", "rf19-1")
    lr = _last(first, "accepted")["logical_round_id"]
    pipe.answer = "保级线是 999。"
    check.replies = [_chk("fail", [_issue("保级线是 999")]), "保级线是 999。", _chk("fail", [_issue("保级线是 999")])]
    models.replies = [_router_json("knowledge_query", False)]
    done = _last(_refresh(client, cid, lr, "rf19-2"), "done")
    assert done["adopted"] is False
    current = [r["content"] for r in msgs.effective_messages(cid) if r["role"] == "assistant" and r["is_current"]]
    assert current == ["VIP 保级按月计算。"]


@pytest.mark.parametrize("fail_at", ["first", "recheck", "repair"])
def test_q19_at30_check_exception_not_released(env, monkeypatch, tmp_path, fail_at):
    """检查/复查超时或修正失败 → 执行异常，不放行、不重试；只落失败说明。"""
    client, models, pipe, logs, msgs, check = (
        env["client"], env["models"], env["pipe"], env["logs"], env["msgs"], env["check"],
    )
    monkeypatch.setattr(main, "diag", main.DiagLog(tmp_path))
    cid = _new_conv(client)
    models.replies = [_router_json("knowledge_query", False)]
    pipe.answer = "当天到账。"
    timeout = ModelError("llm_fail", "timeout")
    check.replies = {
        "first": [timeout],
        "recheck": [_chk("fail", [_issue("当天到账")]), "修正稿", timeout],
        "repair": [_chk("fail", [_issue("当天到账")]), ModelError("llm_fail", "boom")],
    }[fail_at]
    ev = _ask(client, cid, "到账时间？", "exc-" + fail_at)
    err = _last(ev, "error")
    assert err["type"] == ("repair_fail" if fail_at == "repair" else "check_fail")
    assert err["message"] == CHECK_FAIL_MESSAGE
    assert _last(ev, "check")["check_status"] == "error"
    assert _last(ev, "done") is None
    row = logs.rows[err["exec_id"]]
    assert row["check_status"] == "error" and row["exec_state"] == "failed"
    assert _assistant_texts(msgs, cid) == [CHECK_FAIL_MESSAGE]
    assert all(r["completeness"] == "error_notice" for r in msgs.effective_messages(cid) if r["role"] == "assistant")


def test_q19_budget_too_short_skips_repair(env, monkeypatch):
    """剩余时间不足 120 秒时不派发修正，直接按未通过收口。"""
    client, models, pipe, check = env["client"], env["models"], env["pipe"], env["check"]
    monkeypatch.setattr(main, "RUN_LEASE_SEC", 60)
    cid = _new_conv(client)
    models.replies = [_router_json("knowledge_query", False)]
    pipe.answer = "当天到账。"
    check.replies = [_chk("fail", [_issue("当天到账")])]
    done = _last(_ask(client, cid, "到账？", "budget"), "done")
    assert "剩余时间不足以修正" in done["text"]
    assert len(check.seen) == 1


def test_q19_at18_numbers_present_but_relation_wrong_fails(env):
    """AT-18：数字都在证据里但业务关系错 → 语义检查 fail 就不能判有依据（数字规则不放行）。"""
    client, models, pipe, check = env["client"], env["models"], env["pipe"], env["check"]
    pipe.blocks = [{"path": "a.md", "chunk_id": "c1", "content": "VIP1 需 100 财富值，VIP2 需 200 财富值。", "feature_id": "vip"}]
    cid = _new_conv(client)
    models.replies = [_router_json("knowledge_query", False)]
    pipe.answer = "VIP1 需 200 财富值。"
    assert number_issue(pipe.answer, pipe.blocks) is None
    check.replies = [_chk("fail", [_issue("VIP1 需 200 财富值", reason="200 属于 VIP2")]), "VIP1 需 100 财富值。", _chk("pass")]
    done = _last(_ask(client, cid, "VIP1 要多少财富值？", "at18"), "done")
    assert done["text"] == "VIP1 需 100 财富值。"
    assert "数字都出现在原文里但业务关系说错" in settings.CHECK_PROMPT


def test_q19_leaked_number_forces_fail_even_if_model_passes(env):
    """旧数字规则并入检查：数字不在证据中 → 即使模型判 pass 也按 fail 进入修正。"""
    client, models, pipe, logs, check = env["client"], env["models"], env["pipe"], env["logs"], env["check"]
    cid = _new_conv(client)
    models.replies = [_router_json("knowledge_query", False)]
    pipe.answer = "保级线是 99999。"
    check.replies = [_chk("pass"), "文档未写保级线的具体数字。", _chk("pass")]
    done = _last(_ask(client, cid, "保级线？", "leak"), "done")
    assert done["text"] == "文档未写保级线的具体数字。"
    first = logs.rows[done["exec_id"]]["evidence_check"]["rounds"][0]
    assert first["check_status"] == "fail" and "99999" in first["issues"][-1]["reason"]


def test_q19_conflict_from_check_sets_biz_result(env):
    client, models, logs, check = env["client"], env["models"], env["logs"], env["check"]
    cid = _new_conv(client)
    models.replies = [_router_json("knowledge_query", False)]
    check.replies = [_chk("pass", conflict=True)]
    done = _last(_ask(client, cid, "VIP 保级规则？", "conflict"), "done")
    assert logs.rows[done["exec_id"]]["biz_result"] == "conflict"


def test_q19_non_knowledge_branches_skip_check(env):
    client, models, logs, check = env["client"], env["models"], env["logs"], env["check"]
    cid = _new_conv(client)
    models.replies = [_router_json("ack", False)]
    done = _last(_ask(client, cid, "好的谢谢", "ack19"), "done")
    assert check.seen == []
    assert logs.rows[done["exec_id"]]["check_status"] == "not_run"
    assert evidence_items([{"path": "a", "chunk_id": "c", "content": "x"}])[0]["evidence_id"] == "E1"


# ---------------- STEP-Q10 ----------------

def _req(client):
    from types import SimpleNamespace

    account = main.auth.get_live_account(client.cookies.get(settings.AUTH_COOKIE_NAME))
    return SimpleNamespace(state=SimpleNamespace(account=account))


def _decode(chunk: bytes) -> tuple[str, dict]:
    return _events(chunk.decode("utf-8"))[0]


async def _drain_tasks():
    import asyncio

    while main._EXEC_TASKS:
        await asyncio.gather(*list(main._EXEC_TASKS), return_exceptions=True)


@pytest.mark.anyio
async def test_q10_at29_close_page_server_completes_and_reopen_reads_only(env):
    """AT-29：生成中关闭页面 → 服务端照常完成并保存；重开后状态接口只读结果，不再调用模型。"""
    import asyncio

    client, pipe, msgs, models = env["client"], env["pipe"], env["msgs"], env["models"]
    cid = _new_conv(client)
    req = _req(client)
    pipe.head, pipe.answer, pipe.gate = "草稿前半，", "后半。", asyncio.Event()
    body = {"conversation_id": cid, "query": "VIP 保级？", "client_request_id": "at29", "round_id": "r-at29"}
    gen = main._ask_events(req, body)
    seen = []
    while True:
        event, data = _decode(await gen.__anext__())
        seen.append(event)
        if event == "token":
            break
    running = await main.exec_status("r-at29", req)
    assert running["terminal"] is False and running["statuses"]["exec_state"] == "running"
    await gen.aclose()  # 关闭页面：只结束订阅
    pipe.gate.set()
    await _drain_tasks()
    assert [r["content"] for r in msgs.effective_messages(cid) if r["role"] == "assistant"] == ["草稿前半，后半。"]
    calls_before, seen_before = len(pipe.calls), len(models.seen)
    got = await main.exec_status("r-at29", req)
    assert got["terminal"] is True and got["derived"] is False
    assert got["text"] == "草稿前半，后半。"
    assert got["statuses"]["exec_state"] == "completed" and got["statuses"]["msg_save"] == "saved"
    assert got["statuses"]["check_status"] == "pass"
    assert got["c_gen"] and "content" not in got["c_gen"][0]
    assert len(pipe.calls) == calls_before and len(models.seen) == seen_before
    assert [c[0] for c in pipe.calls].count("generate") == 1


def test_q10_status_endpoint_owner_only_and_derived_interrupt(env):
    """状态接口：非本人 404；本进程没在跑且租期不属于它的 running 执行按中断报告，不写库。"""
    client, logs = env["client"], env["logs"]
    cid = _new_conv(client)
    me = _req(client).state.account
    logs.rows["r-stale"] = {"round_id": "r-stale", "conv_id": cid, "user_id": me["id"], "exec_state": "running",
                            "status": "running", "schema_ver": 2}
    logs.rows["r-other"] = {"round_id": "r-other", "conv_id": cid, "user_id": "someone-else", "exec_state": "completed"}
    got = client.get("/api/kb/rounds/r-stale/status").json()
    assert got["terminal"] is True and got["derived"] is True
    assert got["statuses"]["exec_state"] == "interrupted" and got["error_type"] == "service_interrupted"
    assert logs.rows["r-stale"]["exec_state"] == "running"
    assert client.get("/api/kb/rounds/r-other/status").status_code == 404
    assert client.get("/api/kb/rounds/nope/status").status_code == 404
    # 状态接口不走「问答明细」权限；详情接口仍要
    assert client.get("/api/kb/rounds/r-stale").status_code == 403
    client.post("/api/kb/auth/logout")
    assert client.get("/api/kb/rounds/r-stale/status").status_code == 401


def test_q10_c41_real_generate_failure_half_text_not_complete(env):
    """C41：服务端生成真失败时半段不算完整回答，不进 L1。"""
    client, models, pipe, msgs = env["client"], env["models"], env["pipe"], env["msgs"]
    cid = _new_conv(client)
    models.replies = [_router_json("knowledge_query", False)]
    pipe.head, pipe.stream_error = "VIP 保级线是三十", ModelError("gen_fail", "boom")
    err = _last(_ask(client, cid, "VIP 保级？", "c41"), "error")
    assert err["type"] == "gen_fail"
    saved = [r for r in msgs.effective_messages(cid) if r["role"] == "assistant"]
    assert saved[0]["completeness"] == "error_notice" and "保级线是三十" not in saved[0]["content"]
    pipe.head, pipe.stream_error = "", None
    models.replies = [_router_json("knowledge_query", True)]
    _ask(client, cid, "那 SVIP 呢？", "c41-2")
    # 下一问的 Rewrite 历史里没有这段半截正文
    assert "保级线是三十" not in json.dumps(pipe.calls[-4:], ensure_ascii=False)


@pytest.mark.anyio
async def test_q10_at40_timeout_then_late_result_does_not_change_terminal(env, monkeypatch):
    """AT-40：超过总截止 → 执行失败并说明超时；之后模型结果晚到也不改写终态。"""
    import asyncio

    client, pipe, msgs, logs = env["client"], env["pipe"], env["msgs"], env["logs"]
    monkeypatch.setattr(main, "RUN_LEASE_SEC", 0.3)
    cid = _new_conv(client)
    req = _req(client)
    pipe.gate = asyncio.Event()
    body = {"conversation_id": cid, "query": "VIP 保级？", "client_request_id": "at40", "round_id": "r-at40"}
    events = [_decode(chunk) async for chunk in main._ask_events(req, body)]
    last_event, last_data = events[-1]
    assert last_event == "error" and last_data["type"] == "exec_timeout"
    row = logs.rows["r-at40"]
    assert row["exec_state"] == "failed" and row["error_type"] == "exec_timeout"
    texts = [r["content"] for r in msgs.effective_messages(cid) if r["role"] == "assistant"]
    assert texts == [main.EXEC_TIMEOUT_MESSAGE]
    pipe.gate.set()
    await asyncio.sleep(0.05)
    await _drain_tasks()
    assert [r["content"] for r in msgs.effective_messages(cid) if r["role"] == "assistant"] == texts
    assert logs.rows["r-at40"]["exec_state"] == "failed"
    # 超时后执行权已释放，同会话可以继续提问
    monkeypatch.setattr(main, "RUN_LEASE_SEC", 300)
    pipe.gate = None
    done = [_decode(c) async for c in main._ask_events(req, dict(body, client_request_id="at40-2", round_id="r-at40b"))]
    assert done[-1][0] == "done"


def test_q10_frontend_draft_check_and_reconnect():
    """UD-01 与 AT-16 的前端落点：流式标草稿、收到 check 转正式或替换、EOF 无终态时轮询状态接口。"""
    for needle in ("草稿·核对中", 'event === "check"', "draft: true", "function settleFromServer",
                   "if (!terminalSeen)", '"/status"', "已按原文修正"):
        assert needle in QA_JS
    assert "is_disconnected" not in (ROOT / "site" / "kb-api" / "app" / "main.py").read_text(encoding="utf-8")
