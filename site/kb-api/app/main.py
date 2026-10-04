# -*- coding: utf-8 -*-
"""kb-api：浏览器只打本服务；Session Cookie 鉴权。"""
from __future__ import annotations

import asyncio
from copy import deepcopy
import json
import logging
import re
import time
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator
from urllib.parse import urlsplit

from fastapi import FastAPI, Query, Request
from fastapi.responses import JSONResponse, Response, StreamingResponse

from . import listing, settings
from .answer_process import AnswerProcess, answer_history, process_for_row
from .auth_store import (
    AUDIT_FIELDS,
    NEW_PERMS,
    PENDING_PERMS,
    PERM_CHECKBOX,
    RETIRED_PERMS,
    AuditUnavailable,
    AuthStore,
)
from .index_tasks import IndexTaskBook
from .issues import IssueBook
from .purge import PurgeBook
from .conv_store import ADMIN_STATES, RUN_LEASE_SEC, ConvStore, clamp_page
from .config_store import ConfigConflict, ConfigStore, enabled_texts
from .tls_store import TlsStore
from .indexer import Indexer
from .aliases import c20_display_name
from .l1 import as_history, assemble_from_ids, assemble_l1, snapshot_meta
from .logs import RUNTIME_SCHEMA_VER, STATUS_KEYS, LogStore
from .msg_store import DuplicateRequest, MsgStore
from .migrate import migrate_legacy
from .memory_index import MemoryIndex, QdrantMemoryVec
from .memory_tool import MemoryScope, MemoryTool
from .prompts import router_text
from .recall import RecallWorkflow, apply_recall, budget_for, recall_gaps, unresolved_reason
from .test_runs import TestBook, TestError
from .recall import runtime_record as recall_record
from .conv_task import (
    NO_TARGET,
    RESTATE_FAIL_MESSAGE,
    RestateError,
    is_conversation_only,
    pick_versions,
    replay,
    replay_versions,
    restate_refs,
    restate_source,
    wants_version,
)
from .conv_task import restate as conv_restate
from .exec_view import build as build_exec_view
from .exec_view import referenced_msg_ids
from .models_ext import ModelClients, ModelError, key_status, missing_keys
from .pipeline import REWRITE_V3_VER, Pipeline, RewriteInvalid, post_check_answer, public_c_gen
from .router import ConversationRouter, RouterError, router_runtime
from .branches import (
    NON_KNOWLEDGE_ROUTES,
    ROUTE_BIZ_RESULT,
    BranchError,
    clarify,
    local_time_text,
    pick_reply,
    smalltalk_reply,
)
from .tasks import (
    HISTORY_UNSUPPORTED,
    TaskPreparer,
    TaskPrepError,
    carry_text,
    find_carry,
    pending_text,
    prep_record,
    settle,
    task_brief,
    unfinished_text,
)
from .evidence import (
    CHECK_FAIL_MESSAGE,
    CHECK_VER,
    NOT_RELIABLE_MESSAGE,
    REPAIR_MIN_REMAINING_SEC,
    CheckError,
    EvidenceChecker,
    draft_hash,
    evidence_items,
    number_issue,
)
from .store import VectorStore
from .util import excerpt, json_loads, uid
from .diag import DiagLog
from .overview import HEAT_SCAN_LIMIT, compose as compose_overview, compute_heat

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("kb-api")

store = VectorStore()
models = ModelClients()
config_store = ConfigStore()
logs = LogStore()
auth = AuthStore()
convs = ConvStore()
msgs = MsgStore()
diag = DiagLog()
purge_book = PurgeBook()
issues = IssueBook()
index_tasks = IndexTaskBook()
test_book = TestBook()
config_store.release_gate = test_book.gate
config_store.on_draft_saved = test_book.mark_stale
tls = TlsStore()
indexer = Indexer(store, models.embed)
pipeline = Pipeline(store, models, lambda: config_store.data)
router = ConversationRouter(models)
task_preparer = TaskPreparer(models)
evidence_checker = EvidenceChecker(models)
index_lock = asyncio.Lock()
index_ready = False
startup_error = ""


def _test_source(conv_id: str) -> dict | None:
    """测试带入只复制当时还能读到的消息。隐藏、清空、删除之后旧测试不能再拿出原文。"""
    row = convs.admin_get(conv_id)
    if not row:
        return None
    hidden = bool(row.get("hidden_at"))
    return {
        "owner": row.get("account_id"),
        "hidden": hidden,
        "hidden_at": str(row.get('hidden_at') or '') or None,
        "clear_seq": int(row.get("clear_seq") or 0),
        "messages": msgs.admin_messages(conv_id),
    }


test_book.bind_sources(_test_source)


async def _execute_admin_test(row):
    from .admin_test_runtime import execute
    return await execute(row, models, store, _ask_flow)


test_book.bind_executor(_execute_admin_test)


def _conv_owner(conv_id: str) -> str | None:
    row = convs.admin_get(conv_id) or {}
    return str(row.get("account_id") or "") or None


# STEP-Q14：对话记忆派生索引；消息保存成功后经 on_saved 交给后台写入
mem_index = MemoryIndex(None, QdrantMemoryVec(store.client), models.embed, _conv_owner)


def _msg_saved(row: dict) -> None:
    mem_index.note_saved(row)


msgs.on_saved = _msg_saved

# STEP-Q16：追溯工作流；Memory Tool 每次按当前全局组件现组，范围由服务端绑定
recall_workflow = RecallWorkflow(models)


async def _memory_rerank(query: str, docs: list[str], top_n: int) -> list[int]:
    return await models.rerank(query, docs, top_n)


def _memory_tool() -> MemoryTool:
    return MemoryTool(msgs, convs, mem_index, mem_index.embed, _memory_rerank)


async def _startup_memory() -> None:
    """知识索引启动之后再接记忆索引：确认可用后回填迁移消息与遗漏；不可用只标「未接入」。"""
    try:
        if not mem_index.connect():
            return
        ids = [str(r["id"]) for r in convs.repo.list_all()]
        result = await mem_index.backfill(msgs, ids)
        log.info("memory backfill: %s", result)
    except Exception:  # noqa: BLE001
        log.exception("memory startup failed")


async def _startup_all() -> None:
    await _startup_index()
    await _startup_memory()


async def _startup_index() -> None:
    global index_ready, startup_error
    try:
        if missing_keys():
            from .chunking import scan_briefs
            scan_briefs()
            store.ensure_collections()
            store.rebuild_bm25_from_qdrant()
            index_ready = store.chunk_count() > 0
            return
        await indexer.rebuild()
        index_ready = True
    except Exception as exc:  # noqa: BLE001
        startup_error = str(exc)
        log.exception("startup index failed")
        try:
            store.rebuild_bm25_from_qdrant()
            index_ready = store.chunk_count() > 0
        except Exception:  # noqa: BLE001
            index_ready = False


@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
    tls.migrate_legacy(settings.DATA_DIR)
    logs.ensure_feedback_columns()
    auth.ensure_schema()
    auth.bootstrap_if_empty()
    auth.sync_super_perms()
    convs.ensure_schema()
    msgs.ensure_schema()
    purge_book.ensure_schema()
    issues.ensure_schema()
    index_tasks.ensure_schema()
    # STEP-Q06：旧云端历史迁入消息表；失败只记报告，不阻断启动
    try:
        migrate_legacy(convs, msgs, logs)
    except Exception:  # noqa: BLE001
        log.exception("q06 migrate failed")
    mem_index.ensure_schema()
    asyncio.create_task(_startup_all())
    yield


app = FastAPI(title="Hayyo kb-api", lifespan=lifespan)


@app.middleware("http")
async def auth_guard(request: Request, call_next):
    """分档：登录/登出/me 白名单；OPS_READ_WRITE 要勾选；未登录 ask/heatmap 401。"""
    path = request.url.path
    method = request.method.upper()
    if method in _WRITE_METHODS and path.startswith("/api/kb/") and not _csrf_ok(request):
        return JSONResponse(
            {"ok": False, "code": "csrf_rejected", "message": "请求来源不可信"},
            status_code=403,
        )
    sid = request.cookies.get(settings.AUTH_COOKIE_NAME)
    account = auth.get_live_account(sid)
    request.state.account = account
    request.state.session_id = sid
    if _is_public(method, path):
        return await call_next(request)
    ops = _ops_perm(method, path)
    if ops:
        if account is None:
            return _deny(401, "未登录")
        # 元组表示具备其中任一权限即可进入，细分过滤在路由内做
        need = (ops,) if isinstance(ops, str) else ops
        if not any(auth.has_perm(account, p) for p in need):
            return _deny(403, "没有权限")
        return await call_next(request)
    if account is None:
        return _deny(401, "未登录")
    # STEP-005：已登录无「知识问答」不能提问
    if method == "POST" and path == "/api/kb/ask" and not auth.has_perm(account, "知识问答"):
        return _deny(403, "没有权限")
    # STEP-012：heatmap chips 要知识问答
    if method == "GET" and path == "/api/kb/heatmap" and not auth.has_perm(account, "知识问答"):
        return _deny(403, "没有权限")
    # STEP-Q18：知识引用复核与提问同一知识授权；STEP-Q10：本人执行状态同样要知识问答
    if method == "GET" and (path == "/api/kb/chunk" or _is_exec_status(path)) and not auth.has_perm(account, "知识问答"):
        return _deny(403, "没有权限")
    return await call_next(request)


def _is_exec_status(path: str) -> bool:
    return path.startswith("/api/kb/rounds/") and path.endswith("/status") and path.count("/") == 5


def _deny(status: int, message: str) -> JSONResponse:
    # G-ADM-E01：保留 {ok, message}，补 code 供前端区分报错与真空
    return JSONResponse(
        {"ok": False, "code": listing.ERROR_CODES.get(status, "error"), "message": message},
        status_code=status,
    )


_WRITE_METHODS = ("POST", "PUT", "PATCH", "DELETE")


def _host_of(value: str) -> str:
    raw = (value or "").strip().lower()
    if not raw:
        return ""
    if "://" not in raw:
        raw = "http://" + raw
    return (urlsplit(raw).hostname or "").lower()


def _csrf_ok(request: Request) -> bool:
    """写请求校验 Origin（缺省看 Referer）主机名与本站一致；两者都没有时放行（非浏览器调用）。"""
    source = request.headers.get("origin") or request.headers.get("referer") or ""
    if not source or source == "null":
        return not source
    got = _host_of(source)
    host = _host_of(request.headers.get("host") or "")
    if got and got == host:
        return True
    trusted = {_host_of(x) for x in settings.TRUSTED_ORIGINS}
    return bool(got) and got in trusted


def _client_ip(request: Request) -> str:
    fwd = (request.headers.get("x-forwarded-for") or "").strip()
    if fwd:
        return fwd.split(",")[0].strip()
    if request.client:
        return request.client.host or ""
    return ""


def _set_session_cookie(response: JSONResponse, session_id: str, request: Request) -> None:
    response.set_cookie(
        key=settings.AUTH_COOKIE_NAME,
        value=session_id,
        max_age=settings.AUTH_SESSION_SECONDS,
        httponly=True,
        samesite="lax",
        path="/",
        secure=request.url.scheme == "https",
    )


def _ops_perm(method: str, path: str) -> str | tuple[str, ...] | None:
    # G-ADM-E06：旧「配置」停用，查看与编辑分离
    if path == "/api/kb/config" and method == "GET":
        return ("配置查看", "Prompt查看")
    if path == "/api/kb/config" and method == "PUT":
        return ("配置编辑", "Prompt编辑")
    if path in ("/api/kb/config/publish", "/api/kb/config/rollback") and method == "POST":
        return "配置发布"
    if path in ('/api/kb/config/discard', '/api/kb/config/restore-draft'):
        return ('配置编辑', 'Prompt编辑')
    if path.startswith('/api/kb/config/ops/'):
        return '配置发布'
    if path == "/api/kb/reindex" and method == "POST":
        return "重建"
    if path == "/api/kb/admin/knowledge-sources" or path.startswith("/api/kb/admin/knowledge-sources/"):
        return "知识源查看"
    if path == "/api/kb/admin/memory-coverage" or path.startswith("/api/kb/admin/memory-coverage"):
        return "知识源查看" if method == "GET" else "重建"
    if path == "/api/kb/admin/memory-backfill" and method == "POST":
        return "重建"
    if path == "/api/kb/admin/index-tasks" or path.startswith("/api/kb/admin/index-tasks/"):
        return "重建" if method == "POST" else ("知识源查看", "重建")
    if method == "GET" and path == "/api/kb/rounds":
        return "问答明细"
    # STEP-A07：历史消息正文不因执行详情里有快照 id 就对「问答明细」开放
    if method == "GET" and path.startswith("/api/kb/rounds/") and "/context/" in path:
        return "对话审计"
    if method == "GET" and path.startswith("/api/kb/rounds/") and "/feedback" not in path and not _is_exec_status(path):
        return "问答明细"
    if method == "GET" and (path == "/api/kb/admin/conversations" or path.startswith("/api/kb/admin/conversations/")):
        return "对话审计"
    if path == "/api/kb/admin/issues" or path.startswith("/api/kb/admin/issues/"):
        return "问题处理"
    if method == "GET" and path == "/api/kb/admin/audits":
        return "操作审计"
    if method == "GET" and path == "/api/kb/admin/feedback-summary":
        return "反馈汇总"
    if method == "GET" and (path == "/api/kb/admin/feedback" or path.startswith("/api/kb/admin/feedback/")):
        return "反馈汇总"
    if method == "GET" and path == "/api/kb/admin/heatmap":
        return "功能热度"
    # STEP-A15：运行概览只给聚合，用「数据概览」
    if path == "/api/kb/admin/overview" and method == "GET":
        return "数据概览"
    # STEP-A18：诊断与异常只要「健康」；标记已查看也只改观察记录
    if path == "/api/kb/admin/diagnostics" and method == "GET":
        return "健康"
    if path == "/api/kb/admin/diag-events" or path.startswith("/api/kb/admin/diag-events/"):
        if method == "GET" or (method == "POST" and path.endswith("/ack")):
            return "健康"
    return None


def _is_public(method: str, path: str) -> bool:
    if method == "GET" and path == "/api/kb/health":
        return True
    if method == "POST" and path in ("/api/kb/auth/login", "/api/kb/auth/logout"):
        return True
    if method == "GET" and path == "/api/kb/auth/me":
        return True
    if method == "GET" and path == "/api/kb/auth/admin-gate":
        return True
    return False


def _health() -> dict:
    qdrant_ok = store.ping()
    keys = key_status()
    cfg_ok = True
    try:
        config_store.snapshot()
    except Exception:  # noqa: BLE001
        cfg_ok = False
    chunk_count = 0
    try:
        chunk_count = store.chunk_count()
    except Exception:  # noqa: BLE001
        chunk_count = 0
    return {
        "qdrant_ready": qdrant_ok,
        "config_ready": cfg_ok,
        "key_dashscope": keys["dashscope"],
        "key_deepseek": keys["deepseek"],
        "chunk_count": max(0, int(chunk_count)),
        "index_ready": bool(index_ready and qdrant_ok and chunk_count > 0),
        "startup_error": startup_error,
    }


@app.get("/api/kb/health")
async def health():
    return _health()


# ---------- STEP-A18：授权诊断与异常观测（只观察、定位、跳转） ----------

_DIAG_WINDOW_HOURS = 24
_DIAG_MODULE_LABEL = {
    "messages": "消息事实源", "runtime": "Runtime 存储", "knowledge": "Knowledge 检索",
    "model": "模型连接", "audit": "审计", "service": "服务",
}


def _diag_recent(events: list[dict], types: tuple[str, ...]) -> dict:
    """最近窗口内各类型次数与最近一次时间；时间用 UTC 文本比较。"""
    cutoff = (datetime.utcnow() - timedelta(hours=_DIAG_WINDOW_HOURS)).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    counts = {t: 0 for t in types}
    last = None
    for e in events:
        if e.get("type") in counts and str(e.get("ts") or "") >= cutoff:
            counts[e["type"]] += 1
            if last is None or e["ts"] > last:
                last = e["ts"]
    return {"counts": counts, "total": sum(counts.values()), "last_at": last, "window_hours": _DIAG_WINDOW_HOURS}


def _safe_ping(obj: Any) -> bool | None:
    try:
        return bool(obj.ping())
    except Exception:  # noqa: BLE001
        return None


@app.get("/api/kb/admin/diagnostics")
async def admin_diagnostics():
    """诊断快照：只做数据库与 Qdrant 的 ping，不调用模型、不重建索引、不写业务数据。"""
    events, broken = diag.events()
    dstate = diag.state()
    limited = bool(dstate["limited"] or broken)
    db_ok = _safe_ping(logs)
    h = _health()
    keys = key_status()
    msg_recent = _diag_recent(events, ("user_save_fail", "assistant_save_fail", "assistant_save_blocked", "retry_save_fail"))
    rt_recent = _diag_recent(events, ("runtime_insert_fail", "runtime_update_fail"))
    kn_recent = _diag_recent(events, ("retrieve_error",))
    md_recent = _diag_recent(events, ("model_error",))
    au_recent = _diag_recent(events, ("audit_write_fail",))

    def level(ping: bool | None, recent: dict) -> str:
        if ping is False:
            return "down"
        if recent["total"]:
            return "degraded"
        return "unknown" if ping is None else "ok"

    items = [
        {
            "key": "messages", "label": "消息事实源", "status": level(db_ok, msg_recent),
            "db_ping": db_ok, "recent": msg_recent,
            "note": "数据库可连通不代表所有消息已保存；保存失败按 User / Assistant 分开统计",
        },
        {
            "key": "runtime", "label": "Runtime 存储", "status": "limited" if limited else level(db_ok, rt_recent),
            "db_ping": db_ok, "recent": rt_recent,
            "note": ("旁路诊断记录写入或读取失败，观察受限；无记录不等于零失败" if limited
                     else "无记录不等于零失败；只统计已观察到的写入失败与不完整记录"),
        },
        {
            "key": "knowledge", "label": "Knowledge 检索",
            "status": "down" if not h["qdrant_ready"] else ("degraded" if (not h["index_ready"] or kn_recent["total"]) else "ok"),
            "qdrant_ready": h["qdrant_ready"], "index_ready": h["index_ready"], "chunk_count": h["chunk_count"],
            "recent": kn_recent,
            "impact": "影响需要知识检索的问答；不依赖知识检索的分支（如致谢、闲聊、越界说明）按实际依赖执行，不视为全部不可用",
            "note": "Qdrant 可达不等于所有知识任务都能完成",
        },
        {"key": "memory", "label": "Memory", "status": 'ok' if getattr(mem_index, 'connected', False) else 'not_connected',
         "note": '派生索引已连接；具体覆盖见索引页' if getattr(mem_index, 'connected', False) else ('未连接：' + str(getattr(mem_index, 'connect_error', None) or '尚未连接'))},
        {
            "key": "model", "label": "模型连接", "status": "degraded" if md_recent["total"] else "unknown",
            "keys": {"dashscope": keys.get("dashscope"), "deepseek": keys.get("deepseek")}, "recent": md_recent,
            "note": "Key 已配置不等于鉴权成功或额度充足；本页不发起模型调用，只看最近真实调用的失败记录",
        },
        {
            "key": "config", "label": "运行配置", "status": "ok" if h["config_ready"] else "down",
            "bound_version": config_store.package_id, "note": "当前发布包；草稿保存不会改变该版本",
        },
        {
            "key": "audit", "label": "审计", "status": "degraded" if au_recent["total"] else "unknown",
            "integrity": auth.audit_health(), "recent": au_recent,
            "note": "进程内计数重启清零；审计写失败另记诊断事件",
        },
    ]
    by_type: dict[str, int] = {}
    for e in events:
        by_type[e["type"]] = by_type.get(e["type"], 0) + 1
    return {
        "checked_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
        "stored_tz": "UTC",
        "tz": settings.DISPLAY_TZ,
        "items": items,
        "events_by_type": by_type,
        "observation": {"limited": limited, "fallback_count": dstate["fallback_count"], "read_incomplete": broken},
        "active_checks": ["mysql_ping", "qdrant_ping"],
    }


def _diag_public(e: dict) -> dict:
    out = {k: e.get(k) for k in ("id", "ts", "type", "module", "code", "conv_id", "exec_id", "msg_id", "op_id")}
    out["module_label"] = _DIAG_MODULE_LABEL.get(e.get("module"), e.get("module"))
    out["save_kind"] = e.get("save_kind")
    out["acked"] = bool(e.get("acked"))
    out["acks"] = e.get("acks") or []
    return out


@app.get("/api/kb/admin/diag-events")
async def admin_diag_events(
    module: str = "",
    type: str = "",  # noqa: A002
    since: str = "",
    until: str = "",
    acked: str = "",
    conv_id: str = "",
    exec_id: str = "",
    cursor: str = "",
    page_size: str = "",
):
    """异常列表：不含请求正文与凭据；观察受限时标覆盖不完整。"""
    if acked and acked not in ("yes", "no"):
        return listing.error(400, "acked 取值无效", "invalid_request")
    try:
        rng = listing.day_range(since, until)
    except listing.BadRange as exc:
        return listing.error(400, exc.message, exc.code)
    events, broken = diag.events()
    start = rng["start_utc"] if rng else None
    end = rng["end_utc"] if rng else None
    rows = [
        e for e in events
        if (not module or e.get("module") == module)
        and (not type or e.get("type") == type)
        and (not conv_id or e.get("conv_id") == conv_id)
        and (not exec_id or e.get("exec_id") == exec_id)
        and (not acked or bool(e.get("acked")) == (acked == "yes"))
        and (not start or start <= str(e.get("ts") or "") < end)
    ]
    try:
        page, nxt, has_more = listing.paginate(
            rows, ts_of=lambda r: r.get("ts"), id_of=lambda r: r.get("id"),
            cursor=cursor or None, size=listing.page_size(page_size),
        )
    except listing.BadCursor:
        return listing.error(400, "游标无效", "bad_cursor")
    limited = bool(diag.state()["limited"] or broken)
    return listing.envelope(
        [_diag_public(e) for e in page],
        next_cursor=nxt,
        has_more=has_more,
        time_field="ts（事件观察时间）",
        total=len(rows),
        complete=not limited,
        note="诊断记录写入或读取失败，观察受限；列表可能不全" if limited else "",
        range=listing.public_range(rng),
    )


def _diag_find(event_id: str) -> dict | None:
    events, _broken = diag.events()
    return next((e for e in events if e.get("id") == event_id), None)


@app.get("/api/kb/admin/diag-events/{event_id}")
async def admin_diag_event(event_id: str):
    """异常详情：关联对象的当前状态只读取、不修改；读不到时标未知。"""
    e = _diag_find(event_id)
    if not e:
        return listing.error(404, "未找到该异常记录", "not_found")
    current: dict = {}
    if e.get("exec_id"):
        row = logs.get_round(str(e["exec_id"]))
        current["exec"] = (
            {k: row.get(k) for k in ("status", "msg_save", "runtime_save", "exec_state", "error_type")}
            if row else None
        )
        current["exec_known"] = row is not None
    if e.get("conv_id"):
        try:
            crow = convs.admin_get(str(e["conv_id"]))
            current["conversation"] = convs.interaction(crow) if crow else None
        except Exception:  # noqa: BLE001
            current["conversation"] = None
        current["conversation_known"] = current.get("conversation") is not None
    retries = None
    if e.get("type") == "assistant_save_blocked":
        retries = f"后端已同步补写 {len(SAVE_RETRY_DELAYS)} 次（共 {len(SAVE_RETRY_DELAYS) + 1} 次）仍失败"
    return {
        **_diag_public(e),
        "current": current,
        "retries_note": retries,
        "issue_status": None,
        "note": "只观察与定位；标记已查看不解除阻塞、不重新生成。需要原文时到会话/执行页按其权限查看",
        "tz": settings.DISPLAY_TZ,
        "stored_tz": "UTC",
    }


@app.post("/api/kb/admin/diag-events/{event_id}/ack")
async def admin_diag_ack(event_id: str, request: Request):
    """标记已查看：追加一条 ack 事件；不改原事件、不解除会话阻塞、不重试任何操作。"""
    account = getattr(request.state, "account", None)
    if not _diag_find(event_id):
        return listing.error(404, "未找到该异常记录", "not_found")
    ack = diag.ack(event_id, account)
    auth.write_audit(
        "diag_ack",
        actor_id=str((account or {}).get("id") or "") or None,
        actor_username=str((account or {}).get("username") or "") or None,
        object_=event_id,
        ip=_client_ip(request),
        detail={},
        object_type="diag_event",
        result="success" if ack.get("written") else "failed",
    )
    return {"ok": True, "event_id": event_id, "written": bool(ack.get("written")),
            "note": "已记录查看；会话阻塞与执行状态不变"}


@app.post("/api/kb/auth/login")
async def auth_login(request: Request):
    try:
        body = await request.json()
    except Exception:  # noqa: BLE001
        return _deny(400, "请求体无效")
    if not isinstance(body, dict):
        return _deny(400, "请求体无效")
    result = auth.login(
        str(body.get("username") or ""),
        str(body.get("password") or ""),
        _client_ip(request),
    )
    if not result.get("ok"):
        return JSONResponse(
            {"ok": False, "message": result["message"]},
            status_code=int(result["status"]),
        )
    account = result["account"]
    resp = JSONResponse({
        "ok": True,
        "id": account["id"],
        "username": account["username"],
    })
    _set_session_cookie(resp, result["session_id"], request)
    return resp


@app.post("/api/kb/auth/logout")
async def auth_logout(request: Request):
    auth.logout(request.cookies.get(settings.AUTH_COOKIE_NAME))
    resp = JSONResponse({"ok": True})
    resp.delete_cookie(settings.AUTH_COOKIE_NAME, path="/")
    return resp


@app.get("/api/kb/auth/me")
async def auth_me(request: Request):
    account = getattr(request.state, "account", None)
    if not account:
        return _deny(401, "未登录")
    return {
        "id": account["id"],
        "username": account["username"],
        "role_name": account.get("role_name"),
        "is_super": bool(account.get("is_super")),
        "permissions": sorted(account.get("permissions") or []),
        "enabled": bool(account.get("enabled")),
    }


@app.post("/api/kb/auth/password")
async def auth_password(request: Request):
    account = getattr(request.state, "account", None)
    if not account:
        return _deny(401, "未登录")
    try:
        body = await request.json()
    except Exception:  # noqa: BLE001
        return _deny(400, "请求体无效")
    if not isinstance(body, dict):
        return _deny(400, "请求体无效")
    raw = auth.hydrate_account(auth.repo.get_account(str(account["id"])))
    if not raw:
        return _deny(401, "未登录")
    result = auth.change_password(
        raw,
        str(body.get("old_password") or ""),
        str(body.get("new_password") or ""),
        _client_ip(request),
    )
    if not result.get("ok"):
        return JSONResponse(
            {"ok": False, "message": result["message"]},
            status_code=int(result["status"]),
        )
    resp = JSONResponse({"ok": True})
    resp.delete_cookie(settings.AUTH_COOKIE_NAME, path="/")
    return resp


def _require_account(request: Request):
    account = getattr(request.state, "account", None)
    if not account:
        return None, _deny(401, "未登录")
    return account, None


def _require_super(request: Request):
    account, err = _require_account(request)
    if err:
        return None, err
    if not account.get("is_super"):
        return None, _deny(403, "没有权限")
    return account, None


def _account_usernames() -> dict[str, str]:
    """账号 id → 登录名，给明细/审计展示用。"""
    out: dict[str, str] = {}
    try:
        for acc in auth.repo.list_accounts():
            aid = str(acc.get("id") or "")
            name = str(acc.get("username") or "").strip()
            if aid and name:
                out[aid] = name
    except Exception:  # noqa: BLE001
        return out
    return out


def _attach_username(row: dict | None, id_key: str, names: dict[str, str] | None = None) -> dict | None:
    if not row:
        return row
    names = names if names is not None else _account_usernames()
    item = dict(row)
    item["username"] = names.get(str(item.get(id_key) or ""), "")
    return item


def _public_audit(row: dict) -> dict:
    detail = dict(row.get("detail") or {})
    for key in list(detail.keys()):
        low = str(key).lower()
        if "password" in low or "secret" in low or "private" in low or low in {"jwt", "token", "key"}:
            detail.pop(key, None)
    out = {
        "id": row.get("id"),
        "actor_id": row.get("actor_id"),
        "actor_username": row.get("actor_username"),
        "action": row.get("action"),
        "object": row.get("object"),
        "ip": row.get("ip"),
        "created_at": str(row.get("created_at") or ""),
        "detail": detail,
    }
    # G-ADM-E07 新列：旧记录没有这些值，标 legacy，不补造
    for name in AUDIT_FIELDS:
        out[name] = row.get(name)
    out["legacy"] = row.get("result") is None
    out["pending_check"] = row.get("result") == "accepted"
    return out


def _audit_unavailable() -> JSONResponse:
    return JSONResponse(
        {"ok": False, "code": "audit_unavailable", "message": "审计暂不可用，已拒绝本次操作"},
        status_code=503,
    )


def _hr_begin(request: Request, account: dict, action: str, object_type: str, object_: str, **kw):
    """高风险写前置：审计受理写不进去就拒绝，返回 (op_id, 错误响应)。"""
    try:
        op_id = auth.begin_audit(
            action,
            actor=account,
            object_=object_,
            ip=_client_ip(request),
            object_type=object_type,
            **kw,
        )
    except AuditUnavailable:
        diag.record("audit_write_fail", "audit_unavailable", op_id=action)
        return None, _audit_unavailable()
    return op_id, None


@app.get("/api/kb/auth/admin-gate")
async def admin_gate(request: Request):
    account = getattr(request.state, "account", None)
    if account is None:
        return _deny(401, "未登录")
    if auth.has_perm(account, "进管理模块"):
        return Response(status_code=204)
    return _deny(403, "没有权限")


@app.get("/api/kb/conversations")
async def list_conversations(request: Request, offset: int = 0, limit: int = 0):
    account, err = _require_account(request)
    if err:
        return err
    items, next_offset = convs.list_page(str(account["id"]), offset, limit or None)
    return {"items": items, "next_offset": next_offset}


@app.post("/api/kb/conversations")
async def create_conversation(request: Request):
    account, err = _require_account(request)
    if err:
        return err
    try:
        body = await request.json()
    except Exception:  # noqa: BLE001
        body = {}
    if not isinstance(body, dict):
        body = {}
    row = convs.create(str(account["id"]), body)
    return row


@app.get("/api/kb/conversations/{conv_id}")
async def get_conversation(conv_id: str, request: Request):
    account, err = _require_account(request)
    if err:
        return err
    row = convs.get_owned(str(account["id"]), conv_id)
    if not row:
        return _conv_not_found()
    return row


@app.put("/api/kb/conversations/{conv_id}")
async def put_conversation(conv_id: str, request: Request):
    account, err = _require_account(request)
    if err:
        return err
    try:
        body = await request.json()
    except Exception:  # noqa: BLE001
        return _deny(400, "请求体无效")
    if not isinstance(body, dict):
        return _deny(400, "请求体无效")
    # 已有服务端消息时，旧客户端整包 payload 不能覆盖这些原文
    if "messages" in body and msgs.has_messages(conv_id):
        body = {k: v for k, v in body.items() if k != "messages"}
    row = convs.update(str(account["id"]), conv_id, body)
    if not row:
        return _conv_not_found()
    return row


@app.delete("/api/kb/conversations/{conv_id}")
async def delete_conversation(conv_id: str, request: Request):
    account, err = _require_account(request)
    if err:
        return err
    if not convs.delete(str(account["id"]), conv_id):
        return _conv_not_found()
    return {"ok": True}


def _conv_not_found() -> JSONResponse:
    return JSONResponse(
        {"ok": False, "code": "conversation_not_found", "message": "未找到该会话"},
        status_code=404,
    )


@app.get("/api/kb/conversations/{conv_id}/answer-history")
async def get_answer_history(conv_id: str, request: Request):
    """服务端消息与各版本过程；旧记录不补造。沿用本人、隐藏、清空边界。"""
    account, err = _require_account(request)
    if err:
        return err
    if not convs.get_owned(str(account["id"]), conv_id):
        return _conv_not_found()
    rows = msgs.effective_messages(conv_id)
    return {"messages": answer_history(rows, lambda eid: logs.get_round(eid) if eid else None),
            "authoritative": msgs.has_messages(conv_id)}


@app.get("/api/kb/conversations/{conv_id}/messages")
async def list_conversation_messages(conv_id: str, request: Request, after_seq: int = 0, limit: int = 0):
    """STEP-Q04：只返回清空边界之后开始的回合，按服务端 seq 升序。"""
    account, err = _require_account(request)
    if err:
        return err
    if not convs.get_owned(str(account["id"]), conv_id):
        return _conv_not_found()
    _off, lim = clamp_page(0, limit or None)
    rows = msgs.effective_messages(conv_id, max(0, int(after_seq or 0)), lim + 1)
    more = len(rows) > lim
    rows = rows[:lim]
    return {
        "items": [MsgStore.public(r) for r in rows],
        "next_after_seq": int(rows[-1]["seq"]) if more and rows else None,
        "clear_seq": msgs.clear_seq(conv_id),
    }


@app.get("/api/kb/conversations/{conv_id}/messages/{msg_id}")
async def get_history_message(conv_id: str, msg_id: str, request: Request):
    """STEP-Q20（S01 §20.2）：点击历史引用时按当前可见性复核：本人、未隐藏、在清空边界之后才返回原文；
    否则统一 404，不借旧链接或缓存恢复内容。"""
    account, err = _require_account(request)
    if err:
        return err
    if not convs.get_owned(str(account["id"]), conv_id):
        return listing.error(404, "此前内容已不可查看", "message_not_found")
    try:
        rows = msgs.get_by_ids(conv_id, [msg_id])
        boundary = msgs.clear_seq(conv_id)
    except Exception as exc:  # noqa: BLE001
        log.warning("history message lookup failed: %s", exc)
        return listing.error(503, "此前内容暂时无法读取", "source_unavailable")
    if not rows or int(rows[0]["round_seq"]) <= int(boundary):
        return listing.error(404, "此前内容已不可查看", "message_not_found")
    return {"ok": True, "message": MsgStore.public(rows[0])}


@app.post("/api/kb/conversations/{conv_id}/clear")
async def clear_conversation(conv_id: str, request: Request):
    """STEP-Q04：记录清空边界；执行中也可清空，晚到结果落在边界外（G-E06-2）。"""
    account, err = _require_account(request)
    if err:
        return err
    if not convs.get_owned(str(account["id"]), conv_id):
        return _conv_not_found()
    try:
        boundary = msgs.clear(conv_id, str(account["id"]))
    except Exception as exc:  # noqa: BLE001
        log.warning("clear conversation failed: %s", exc)
        return JSONResponse(
            {"ok": False, "code": "clear_fail", "message": "清空未生效，请重试"},
            status_code=503,
        )
    convs.note_clear(conv_id, boundary)
    return {"ok": True, "clear_seq": boundary}


def _retry_save_fail(exec_id: str | None) -> JSONResponse:
    return JSONResponse(
        {"ok": False, "code": "retry_save_fail", "message": "仍未保存，请稍后再试", "exec_id": exec_id},
        status_code=503,
    )


@app.post("/api/kb/conversations/{conv_id}/retry-save")
async def retry_save_reply(conv_id: str, request: Request):
    """STEP-Q09：用户触发的重试保存。只写同一份已形成的结果，不重新生成；成功后解除该会话的保存阻塞。"""
    account, err = _require_account(request)
    if err:
        return err
    if not convs.get_owned(str(account["id"]), conv_id):
        return _conv_not_found()
    try:
        body = await request.json()
    except Exception:  # noqa: BLE001
        body = {}
    if not isinstance(body, dict):
        body = {}
    try:
        blocked = convs.save_block_of(conv_id)
    except Exception as exc:  # noqa: BLE001
        log.warning("read save block failed: %s", exc)
        return _retry_save_fail(None)
    if not blocked:
        return {"ok": True, "unblocked": True, "already": True}
    want = str(body.get("exec_id") or "")
    if want and want != blocked:
        return JSONResponse(
            {"ok": False, "code": "exec_mismatch", "message": "要保存的回答与当前待保存的不一致", "blocked_exec_id": blocked},
            status_code=409,
        )
    carrier = _PENDING_REPLIES.get(blocked) or (logs.get_round(blocked) or {}).get("pending_reply")
    user_row = None
    if isinstance(carrier, dict) and carrier.get("user_msg_id"):
        try:
            found = msgs.get_by_ids(conv_id, [str(carrier["user_msg_id"])])
        except Exception as exc:  # noqa: BLE001
            log.warning("retry save user lookup failed: %s", exc)
            return _retry_save_fail(blocked)
        user_row = found[0] if found else None
    if not isinstance(carrier, dict) or user_row is None:
        # 承载已丢失：不拿重新生成冒充补写；标明无法恢复并解除阻塞，避免会话永久锁死
        try:
            convs.clear_save_block(conv_id, blocked)
        except Exception as exc:  # noqa: BLE001
            log.warning("clear save block failed: %s", exc)
            return _retry_save_fail(blocked)
        _PENDING_REPLIES.pop(blocked, None)
        logs.update_round(blocked, {"msg_save": "failed", "error_type": "save_source_lost"})
        return {
            "ok": False,
            "code": "save_source_lost",
            "message": "保存失败，内容无法恢复",
            "unblocked": True,
            "exec_id": blocked,
        }
    try:
        row = _write_reply(conv_id, user_row, blocked, carrier)
    except Exception as exc:  # noqa: BLE001
        log.warning("retry save failed: %s", exc)
        diag.record("retry_save_fail", "retry_save_fail", conv_id=conv_id, exec_id=blocked)
        return _retry_save_fail(blocked)
    # 补写只更新保存状态，执行本身的业务结果与状态不变
    logs.update_round(blocked, {"msg_save": "saved", "assistant_msg_id": row["id"], "pending_reply": None})
    _PENDING_REPLIES.pop(blocked, None)
    try:
        convs.clear_save_block(conv_id, blocked)
    except Exception as exc:  # noqa: BLE001
        # 消息已写入；再次重试会命中已写行，不会重复落库
        log.warning("clear save block failed: %s", exc)
        return _retry_save_fail(blocked)
    return {
        "ok": True,
        "unblocked": True,
        "exec_id": blocked,
        "logical_round_id": row["round_id"],
        "assistant_msg_id": row["id"],
        "version_no": row.get("version_no"),
        "adopted": row.get("_adopted"),
    }


# STEP-A05：关键词在消息正文中最多取这么多条命中定位会话；超出时标覆盖不完整
_CONV_SEARCH_CAP = 5000
_CONV_HITS_PER_ITEM = 3
_CONV_FILTER_VALUES = {
    "visibility": {"visible", "hidden"},
    "cleared": {"yes", "no"},
    "state": set(ADMIN_STATES),
}


def _payload_messages(row: dict) -> list[dict]:
    payload = json_loads(row.get("payload"), {}) or {}
    msgs_ = payload.get("messages") if isinstance(payload, dict) else None
    return msgs_ if isinstance(msgs_, list) else []


def _admin_conv_item(row: dict, stat: dict | None, names: dict[str, str], hits: list[dict]) -> dict:
    """后台会话列表的一行：逻辑回合数、可见性、清空、交互状态分列给出。"""
    stat = stat or {}
    has_msgs = int(stat.get("msgs") or 0) > 0
    legacy = not has_msgs and bool(_payload_messages(row))
    return {
        "id": row["id"],
        "account_id": row.get("account_id"),
        "username": names.get(str(row.get("account_id") or "")),
        "title": row.get("title") or "",
        "created_at": str(row.get("created_at") or ""),
        "updated_at": str(row.get("updated_at") or ""),
        "last_message_at": str(stat["last_msg_at"]) if stat.get("last_msg_at") else None,
        # 旧会话只有展示缓存，回合数不可确定，不按缓存条数推算
        "round_count": None if legacy else int(stat.get("rounds") or 0),
        "legacy": legacy,
        "visibility": "hidden" if row.get("hidden_at") else "visible",
        "hidden_at": str(row["hidden_at"]) if row.get("hidden_at") else None,
        "cleared": int(row.get("clear_seq") or 0) > 0 or int(stat.get("clear_count") or 0) > 0,
        "clear_count": int(stat.get("clear_count") or 0),
        "last_clear_at": str(stat["last_clear_at"]) if stat.get("last_clear_at") else None,
        "interaction": convs.interaction(row),
        "hits": hits,
    }


@app.get("/api/kb/admin/conversations")
async def admin_conversations(
    account: str = "",
    conv_id: str = "",
    q: str = "",
    time_field: str = "updated_at",
    since: str = "",
    until: str = "",
    visibility: str = "",
    cleared: str = "",
    state: str = "",
    cursor: str = "",
    page_size: str = "",
):
    """STEP-A05：后台会话列表。服务端按真实匹配集筛选与游标分页，含用户已隐藏的会话。"""
    names = _account_usernames()
    filters: dict = {}
    for key, value in (("visibility", visibility), ("cleared", cleared), ("state", state)):
        if value:
            if value not in _CONV_FILTER_VALUES[key]:
                return listing.error(400, f"{key} 取值无效", "invalid_request")
            filters[key] = value
    who = str(account or "").strip()
    if who:
        by_name = {v: k for k, v in names.items()}
        filters["account_id"] = by_name.get(who, who)
    if conv_id.strip():
        filters["conv_id"] = conv_id.strip()
    filters["time_col"] = "created_at" if time_field == "created_at" else "updated_at"
    try:
        rng = listing.day_range(since, until)
    except listing.BadRange as exc:
        return listing.error(400, exc.message, exc.code)
    if rng:
        filters["range"] = rng
    try:
        before = listing.decode_cursor(cursor)
    except listing.BadCursor:
        return listing.error(400, "游标无效", "bad_cursor")
    size = listing.page_size(page_size)
    key = str(q or "").strip()
    capped = False
    hits_by_conv: dict[str, list[dict]] = {}
    try:
        if key:
            filters["q"] = key
            hit_rows, capped = msgs.admin_search(key, _CONV_SEARCH_CAP)
            for h in hit_rows:
                hits_by_conv.setdefault(h["conv_id"], []).append(h)
            filters["q_conv_ids"] = set(hits_by_conv)
        rows, has_more = convs.admin_page(filters, before, size)
        stats = msgs.admin_stats([r["id"] for r in rows])
    except Exception as exc:  # noqa: BLE001
        log.warning("admin conversations failed: %s", exc)
        return listing.error(503, "会话记录暂时无法读取", "list_unavailable")
    items = []
    for r in rows:
        hits = [
            {
                "msg_id": h["id"],
                "round_id": h["round_id"],
                "role": h["role"],
                "seq": int(h["seq"]),
                "version_no": h.get("version_no"),
                "is_current": bool(h.get("is_current", 1)),
                "excerpt": MsgStore.excerpt(h.get("content") or "", key),
            }
            for h in hits_by_conv.get(r["id"], [])[:_CONV_HITS_PER_ITEM]
        ]
        items.append(_admin_conv_item(r, stats.get(r["id"]), names, hits))
    nxt = listing.encode_cursor(rows[-1].get("updated_at"), rows[-1].get("id")) if has_more and rows else None
    return listing.envelope(
        items,
        next_cursor=nxt,
        has_more=has_more,
        time_field=("created_at（会话创建时间）" if filters["time_col"] == "created_at" else "updated_at（会话最近更新时间）"),
        complete=not capped,
        note=(f"关键词命中超过 {_CONV_SEARCH_CAP} 条消息，只按最近 {_CONV_SEARCH_CAP} 条定位会话" if capped else ""),
        range=listing.public_range(rng),
    )


def _clear_segment(round_seq: int, bounds: list[int]) -> int:
    """回合属于第几段：0..n-1 为第 i+1 次清空前，n 为当前用户可见范围。"""
    for i, b in enumerate(bounds):
        if round_seq <= b:
            return i
    return len(bounds)


@app.get("/api/kb/admin/conversations/{conv_id}")
async def admin_conversation_detail(conv_id: str, request: Request):
    """STEP-A05：会话详情，全部只读。按服务端顺序给出各回合与已保存回答版本、清空分界、隐藏与交互状态。
    打开详情不写该用户的消息、L1、Memory 或调试数据，只留一条敏感读取审计。"""
    try:
        row = convs.admin_get(conv_id)
        if not row:
            return listing.error(404, "未找到该会话", "conversation_not_found")
        rows = msgs.admin_messages(conv_id)
        clears = msgs.clears(conv_id)
    except Exception as exc:  # noqa: BLE001
        log.warning("admin conversation detail failed: %s", exc)
        return listing.error(503, "会话记录暂时无法读取", "list_unavailable")
    names = _account_usernames()
    if not auth.record_sensitive_read(
        actor=getattr(request.state, "account", None),
        object_type="conversation",
        object_id=conv_id,
        ip=_client_ip(request),
    ):
        diag.record("audit_write_fail", "sensitive_read", conv_id=conv_id)
    bounds = [int(c["boundary_seq"]) for c in clears]
    exec_cache: dict[str, dict | None] = {}

    def exec_row(eid: str | None) -> dict | None:
        if not eid:
            return None
        if eid not in exec_cache:
            exec_cache[eid] = logs.get_round(eid)
        return exec_cache[eid]

    by_id = {r["id"]: r for r in rows}
    rounds: dict[str, dict] = {}
    for r in rows:
        g = rounds.setdefault(r["round_id"], {
            "round_id": r["round_id"],
            "round_seq": int(r["round_seq"]),
            "segment": _clear_segment(int(r["round_seq"]), bounds),
            "user": None,
            "versions": [],
        })
        if r["role"] == "user":
            g["user"] = {
                "msg_id": r["id"],
                "seq": int(r["seq"]),
                "content": r.get("content") or "",
                "created_at": str(r.get("created_at") or ""),
                "exec_id": r.get("exec_id"),
                "source": r.get("source") or "live",
            }
            continue
        ex = exec_row(r.get("exec_id"))
        # 版本列表只收已保存的 Assistant 行；未保存的执行没有消息行，不出现在这里
        g["versions"].append({
            "msg_id": r["id"],
            "seq": int(r["seq"]),
            "version_no": r.get("version_no"),
            "is_current": bool(r.get("is_current", 1)),
            "exec_id": r.get("exec_id"),
            "op_type": r.get("op_type") or "send",
            "completeness": r.get("completeness") or "complete",
            "content": r.get("content") or "",
            "created_at": str(r.get("created_at") or ""),
            "feedback": (ex or {}).get("feedback") if ex else None,
            "exec_status": (ex or {}).get("status") if ex else None,
            "msg_save": (ex or {}).get("msg_save") if ex else None,
            "exec_known": ex is not None,
        })
    out_rounds = []
    for g in sorted(rounds.values(), key=lambda x: x["round_seq"]):
        g["versions"].sort(key=lambda v: (int(v["version_no"] or 0), v["seq"]))
        cur = [v["msg_id"] for v in g["versions"] if v["is_current"]]
        g["current_msg_id"] = cur[0] if cur else None
        # 本回合当时引用的其他回合旧版本（已不是当前版本），供查看「当时引用的旧版本」
        refs = []
        src = exec_row((g["user"] or {}).get("exec_id"))
        snap = (src or {}).get("snapshot") if src else None
        pairs = (snap or {}).get("l1_msg_ids") if isinstance(snap, dict) else None
        if isinstance(pairs, list):
            for pair in pairs:
                aid = pair[1] if isinstance(pair, (list, tuple)) and len(pair) == 2 else None
                ref = by_id.get(aid) if aid else None
                if ref is not None and not int(ref.get("is_current", 1) or 0):
                    refs.append({"msg_id": ref["id"], "round_id": ref["round_id"], "version_no": ref.get("version_no")})
        g["refs_old_versions"] = refs
        g["refs_known"] = isinstance(pairs, list)
        out_rounds.append(g)
    legacy = not rows and bool(_payload_messages(row))
    item = _admin_conv_item(row, {
        "msgs": len(rows),
        "rounds": sum(1 for g in out_rounds if g["user"]),
        "last_msg_at": max((r["created_at"] for r in rows), default=None),
        "clear_count": len(clears),
        "last_clear_at": max((c["created_at"] for c in clears), default=None),
    }, names, [])
    item.pop("hits", None)
    return {
        **item,
        "clears": [
            {
                "index": i + 1,
                "boundary_seq": int(c["boundary_seq"]),
                "created_at": str(c.get("created_at") or ""),
                "actor_id": c.get("actor_id"),
                "actor_username": names.get(str(c.get("actor_id") or "")),
            }
            for i, c in enumerate(clears)
        ],
        "rounds": out_rounds,
        # A05 旧会话：消息表无记录时只读展示 payload 缓存，并标明不是服务端事实
        "legacy_note": "旧会话，消息待迁移（Q06）；以下为展示缓存，非服务端事实" if legacy else None,
        "payload_messages": [
            {"role": str(m.get("role") or ""), "text": str(m.get("text") or "")}
            for m in _payload_messages(row) if isinstance(m, dict)
        ] if legacy else [],
        "tz": settings.DISPLAY_TZ,
        "stored_tz": "UTC",
    }


def _purge_public(op: dict) -> dict:
    return {
        "ok": True,
        "id": op["id"],
        "conv_id": op["conv_id"],
        "status": op["status"],
        "facts": op["facts"],
        "derived": op["derived"],
        "error": op.get("error"),
        "created_at": str(op.get("created_at") or ""),
    }


@app.post("/api/kb/admin/conversations/{conv_id}/purge")
async def admin_purge_conversation(conv_id: str, request: Request):
    """STEP-A06：仅超管。二次确认后先阻断读取，再删消息、执行记录和记忆索引。
    重复提交返回同一次操作，不重做。审计写不上则拒绝，不声称备份已删。"""
    account, err = _require_super(request)
    if err:
        return err
    try:
        body = await request.json()
    except Exception:  # noqa: BLE001
        body = {}
    if not isinstance(body, dict) or str(body.get("confirm") or "") != conv_id:
        return listing.error(400, "需要再次确认会话编号", "need_confirm")
    existing = purge_book.for_conv(conv_id)
    if existing:
        return _purge_public(existing)
    row = convs.repo.get(conv_id)
    if not row:
        return listing.error(404, "未找到该会话", "conversation_not_found")
    try:
        audit_id = auth.begin_audit(
            "purge_conversation",
            actor=account,
            object_=conv_id,
            ip=_client_ip(request),
            detail={"conv_id": conv_id},
        )
    except AuditUnavailable:
        return listing.error(503, "审计暂时不可用，已拒绝删除", "audit_unavailable")
    try:
        op = purge_book.run(conv_id, account["id"], convs, msgs, logs, mem_index, diag)
    except Exception:
        auth.finish_audit(audit_id, 'failed', error_code='purge_result_unknown')
        return listing.error(503, '删除结果暂时无法确认，请查询该会话的删除操作记录', 'purge_result_unknown')
    if op.get('error') == 'barrier_failed':
        auth.finish_audit(audit_id, 'failed', error_code='barrier_failed', detail={'purge_id': op['id']})
        return listing.error(503, '阻断会话读取失败，未继续删除正文', 'barrier_failed', operation=_purge_public(op))
    try:
        issues.invalidate_conv(conv_id)
        test_book.invalidate(conv_id)
    except Exception as exc:  # noqa: BLE001
        op.update(status='partial', derived='failed', error='managed_copies_failed')
        purge_book.repo.update(op['id'], {'status': 'partial', 'derived': 'failed', 'error': 'managed_copies_failed'})
        log.warning("issue invalidate %s failed: %s", conv_id, exc)
        diag.record("purge_cleanup", "issue_invalidate", conv_id=conv_id)
    auth.finish_audit(audit_id, "success" if op.get("status") == "done" else "failed", detail={
        "purge_id": op["id"], "facts": op.get("facts"), "derived": op.get("derived"),
    })
    return _purge_public(op)


@app.get("/api/kb/admin/purge-ops/{op_id}")
async def admin_purge_op(op_id: str, request: Request):
    """按操作号查看实际删除结果。不含原文。"""
    _account, err = _require_super(request)
    if err:
        return err
    op = purge_book.get(op_id)
    if not op:
        return listing.error(404, "未找到该操作", "purge_not_found")
    return _purge_public(op)


def _issue_assignee_ok(account_id: str) -> bool:
    acc = auth.hydrate_account(auth.repo.get_account(account_id))
    return bool(acc and acc.get("enabled", True) and auth.has_perm(acc, "问题处理"))


def _issue_view(row: dict) -> dict:
    if row.get('conv_id') and convs.is_purged(row['conv_id']):
        row = dict(row, source_deleted=1)
    return issues.public(row, _account_usernames())


@app.get("/api/kb/admin/issues")
async def admin_issues(cursor: str = '', page_size: str = '', status: str = ''):
    """问题列表。只有管理摘要和对象 id，不含对话原文。"""
    try:
        rows, nxt, more = issues.repo.page(cursor, listing.page_size(page_size), status)
    except listing.BadCursor:
        return listing.error(400, '游标无效', 'bad_cursor')
    except Exception as exc:  # noqa: BLE001
        log.warning("issue list failed: %s", exc)
        return listing.error(503, "问题记录暂时无法读取", "list_unavailable")
    names = _account_usernames()
    return listing.envelope([_issue_view(r) for r in rows], next_cursor=nxt, has_more=more, time_field='updated_at')


@app.post("/api/kb/admin/issues")
async def admin_issue_create(request: Request):
    account = getattr(request.state, "account", None)
    try:
        body = await request.json()
    except Exception:  # noqa: BLE001
        body = {}
    if not isinstance(body, dict):
        return listing.error(400, "请求体无效", "bad_request")
    source_type, source_id = str(body.get('source_type') or ''), str(body.get('source_id') or '')
    if source_type:
        permission = {'conv': '对话审计', 'version': '对话审计', 'exec': '问答明细', 'feedback': '反馈汇总', 'diag': '健康', 'index_task': '知识源查看'}.get(source_type)
        if not permission or not auth.has_perm(account, permission):
            return listing.error(403, '没有该来源的查看权限', 'forbidden')
        if source_type == 'conv':
            source = convs.admin_get(source_id)
            linked_conv = source_id
        elif source_type == 'version':
            source = msgs.repo.find_message(source_id)
            linked_conv = (source or {}).get('conv_id')
        elif source_type in ('exec', 'feedback'):
            source = logs.get_round(source_id)
            linked_conv = (source or {}).get('conv_id')
        elif source_type == 'index_task':
            source = index_tasks.get(source_id)
            linked_conv = (source or {}).get('scope') if (source or {}).get('grp') == 'memory' and (source or {}).get('scope') != 'all' else None
        else:
            source = next((e for e in diag.events()[0] if e['id'] == source_id), None)
            linked_conv = (source or {}).get('conv_id')
        if not source or (linked_conv and convs.is_purged(linked_conv)):
            return listing.error(404, '来源不存在或已删除', 'source_not_found')
        if body.get('conv_id') and body['conv_id'] != linked_conv:
            return listing.error(400, '来源与会话编号不一致', 'source_mismatch')
        body = dict(body, conv_id=linked_conv)
    try:
        row = issues.create(str(account["id"]), body)
    except ValueError as exc:
        return listing.error(400, str(exc), "bad_request")
    auth.write_audit(
        "issue_create",
        actor_id=account.get("id"),
        actor_username=account.get("username"),
        object_=row["id"],
        ip=_client_ip(request),
        detail={"source_type": row.get("source_type"), "source_id": row.get("source_id")},
    )
    return _issue_view(row)


@app.get("/api/kb/admin/issues/{issue_id}")
async def admin_issue_detail(issue_id: str):
    row = issues.get(issue_id)
    if not row:
        return listing.error(404, "未找到该问题", "issue_not_found")
    return _issue_view(row)


@app.post("/api/kb/admin/issues/{issue_id}")
async def admin_issue_update(issue_id: str, request: Request):
    account = getattr(request.state, "account", None)
    try:
        body = await request.json()
    except Exception:  # noqa: BLE001
        body = {}
    if not isinstance(body, dict):
        return listing.error(400, "请求体无效", "bad_request")
    try:
        row = issues.apply(issue_id, str(account["id"]), body, _issue_assignee_ok)
    except KeyError:
        return listing.error(404, "未找到该问题", "issue_not_found")
    except ValueError as exc:
        return listing.error(400, str(exc), "bad_request")
    auth.write_audit(
        "issue_update",
        actor_id=account.get("id"),
        actor_username=account.get("username"),
        object_=issue_id,
        ip=_client_ip(request),
        detail={"status": row.get("status")},
    )
    return _issue_view(row)


@app.post("/api/kb/admin/issues/{issue_id}/notes")
async def admin_issue_note(issue_id: str, request: Request):
    account = getattr(request.state, "account", None)
    try:
        body = await request.json()
    except Exception:  # noqa: BLE001
        body = {}
    if not isinstance(body, dict):
        return listing.error(400, "请求体无效", "bad_request")
    try:
        issues.add_note(issue_id, str(account["id"]), str(body.get("text") or ""))
    except KeyError:
        return listing.error(404, "未找到该问题", "issue_not_found")
    except ValueError as exc:
        return listing.error(400, str(exc), "bad_request")
    row = issues.get(issue_id)
    auth.write_audit('issue_note', actor_id=account['id'], actor_username=account.get('username'),
                     object_=issue_id, ip=_client_ip(request), detail={'result': 'success'})
    return _issue_view(row or {"id": issue_id})


@app.get("/api/kb/admin/audits")
async def admin_audits(
    action: str = "",
    actor: str = "",
    result: str = "",
    object: str = "",  # noqa: A002
    object_type: str = "",
    op_id: str = "",
    cursor: str = "",
    page_size: str = "",
):
    """G-ADM-E01：服务端筛选 + 游标分页；查询失败返回错误，不显示成「暂无记录」。"""
    try:
        before = listing.decode_cursor(cursor)
    except listing.BadCursor:
        return listing.error(400, "游标无效", "bad_cursor")
    size = listing.page_size(page_size)
    filters = {
        "action": action, "actor_username": actor, "result": result,
        "object": object, "object_type": object_type, "op_id": op_id,
    }
    try:
        rows, has_more = auth.repo.page_audits(filters, before, size)
    except Exception as exc:  # noqa: BLE001
        log.warning("page audits failed: %s", exc)
        return listing.error(503, "操作记录暂时无法读取", "list_unavailable")
    nxt = listing.encode_cursor(rows[-1].get("created_at"), rows[-1].get("id")) if has_more and rows else None
    return listing.envelope(
        [_public_audit(r) for r in rows],
        next_cursor=nxt,
        has_more=has_more,
        time_field="created_at（事件时间）",
        integrity=auth.audit_health(),
    )


@app.get("/api/kb/admin/feedback-summary")
async def admin_feedback_summary():
    items = logs.list_rounds(limit=500)
    down = []
    for row in items:
        if row.get("feedback") != "down":
            continue
        down.append({
            "round_id": row.get("round_id"),
            "original_query": row.get("original_query") or "",
            "created_at": row.get("created_at") or "",
            "status": row.get("status") or "",
        })
    return {"down": down}


_OVERVIEW_DEFAULT_DAYS = 7
_OVERVIEW_MAX_DAYS = 92


@app.get("/api/kb/admin/overview")
async def admin_overview(since: str = "", until: str = "", domain: str = "prod"):
    """STEP-A15：运行概览。按执行开始时间筛选（默认近 7 天、最长 92 天），SQL 实时聚合、不缓存；
    只返回聚合数字，不含账号与正文。"""
    if domain == "test":
        try:
            rng = listing.day_range(since, until, default_days=_OVERVIEW_DEFAULT_DAYS, max_days=_OVERVIEW_MAX_DAYS)
        except listing.BadRange as exc:
            return listing.error(400, exc.message, exc.code)
        rows = [r for r in test_book.runs.values() if str(r.get('created_at') or '').replace('T', ' ') >= str(rng['start'])
                and str(r.get('created_at') or '').replace('T', ' ') < str(rng['end'])]
        statuses = {s: sum(r.get('status') == s for r in rows) for s in ('queued', 'running', 'done', 'failed', 'interrupted')}
        def metric(key, label, value, unit):
            return {'key': key, 'label': label, 'value': value, 'unit': unit, 'source': '独立 test_run 持久记录', 'time_field': 'created_at', 'rule': '仅统计选定时间内已受理的隔离测试，不计生产执行'}
        return {'domain': 'test', 'status': 'recorded', 'range': listing.public_range(rng), 'tz': settings.DISPLAY_TZ,
                'sections': [{'key': 'test', 'label': '隔离测试', 'metrics': [metric('test_runs', '已受理测试', len(rows), '次'),
                             metric('test_status', '执行状态', statuses, '次'), metric('test_calls', '模型/工具调用', sum((r.get('usage') or {}).get('calls', 0) for r in rows), '次'),
                             metric('test_estimated_tokens', '已记录估算 token', sum((r.get('usage') or {}).get('estimated_tokens', 0) for r in rows), '估算 token')]}],
                'heat': {'items': [], 'rule': '测试域不计生产功能热度'}, 'note': '估算用量不代表供应商实际计费；未完成且缺用量的测试未计入用量合计'}
    if domain != "prod":
        return listing.error(400, "domain 取值无效", "invalid_request")
    try:
        rng = listing.day_range(since, until, default_days=_OVERVIEW_DEFAULT_DAYS, max_days=_OVERVIEW_MAX_DAYS)
    except listing.BadRange as exc:
        return listing.error(400, exc.message, exc.code)
    try:
        counts = logs.overview_counts(rng["start"], rng["end"])
        heat = compute_heat(logs.heat_rows(rng["start"], rng["end"], HEAT_SCAN_LIMIT), HEAT_SCAN_LIMIT)
    except Exception as exc:  # noqa: BLE001
        log.warning("admin overview failed: %s", exc)
        return listing.error(503, "运行概览暂时无法读取", "list_unavailable")
    return {
        "domain": "prod",
        "range": listing.public_range(rng),
        "data_cutoff": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
        "stored_tz": "UTC",
        "tz": settings.DISPLAY_TZ,
        "cache": "none",
        **compose_overview(counts, heat),
    }


_LEGACY_FEEDBACK_NOTE = "旧版轮次反馈，无法可靠关联回答版本"


def _rated_messages(rows: list[dict]) -> dict[str, dict]:
    """按会话批量取被评价的 Assistant 行（每个执行对应一个版本）。"""
    want: dict[str, list[str]] = {}
    for r in rows:
        if r.get("schema_ver") and r.get("assistant_msg_id") and r.get("conv_id"):
            want.setdefault(str(r["conv_id"]), []).append(str(r["assistant_msg_id"]))
    out: dict[str, dict] = {}
    for cid, ids in want.items():
        for m in msgs.get_by_ids(cid, ids):
            out[m["id"]] = m
    return out


def _feedback_item(row: dict, msg: dict | None, names: dict[str, str]) -> dict:
    """反馈列表一行。旧记录没有版本关联，标旧版轮次反馈，不挂到当前默认版本上。"""
    legacy = not row.get("schema_ver")
    text = (msg or {}).get("content") if msg else (row.get("answer") or "")
    linked = issues.repo.for_source('feedback', str(row.get('round_id') or ''))
    return {
        "exec_id": row.get("round_id"),
        "feedback": row.get("feedback"),
        "feedback_at": str(row["feedback_at"]) if row.get("feedback_at") else None,
        "user_id": row.get("user_id"),
        "username": names.get(str(row.get("user_id") or "")),
        "conv_id": row.get("conv_id"),
        "logical_round_id": row.get("logical_round_id"),
        "assistant_msg_id": row.get("assistant_msg_id") if not legacy else None,
        "version_no": msg.get("version_no") if msg else None,
        "is_current": bool(msg.get("is_current", 1)) if msg else None,
        "route": row.get("route"),
        "reply_created_at": str(msg["created_at"]) if msg and msg.get("created_at") else None,
        "exec_created_at": str(row.get("created_at") or ""),
        "status": row.get("status"),
        "excerpt": MsgStore.excerpt(text or "", ""),
        "original_query": row.get("original_query") or "",
        "legacy": legacy,
        "legacy_note": _LEGACY_FEEDBACK_NOTE if legacy else None,
        # 问题记录属 A17，接入前不给处理状态
        "issue_status": linked[0].get('status') if linked else None,
        "issue_ids": [r['id'] for r in linked],
    }


@app.get("/api/kb/admin/feedback")
async def admin_feedback_list(
    value: str = "down",
    time_field: str = "feedback_at",
    since: str = "",
    until: str = "",
    account: str = "",
    conv_id: str = "",
    exec_id: str = "",
    msg_id: str = "",
    route: str = "",
    handled: str = "",
    cursor: str = "",
    page_size: str = "",
):
    """STEP-A16：反馈事件列表（默认被踩），服务端筛选与游标分页；管理员只读。"""
    if value not in ("down", "up", "all"):
        return listing.error(400, "value 取值无效", "invalid_request")
    if handled and handled not in ('yes', 'no', 'open', 'doing', 'closed'):
        return listing.error(400, '处理状态取值无效', 'invalid_request')
    col = "created_at" if time_field == "created_at" else "feedback_at"
    try:
        rng = listing.day_range(since, until)
        before = listing.decode_cursor(cursor)
    except listing.BadRange as exc:
        return listing.error(400, exc.message, exc.code)
    except listing.BadCursor:
        return listing.error(400, "游标无效", "bad_cursor")
    names = _account_usernames()
    who = str(account or "").strip()
    user_id = {v: k for k, v in names.items()}.get(who, who) if who else ""
    size = listing.page_size(page_size)
    try:
        rows, has_more = logs.page_feedback(
            value=value, time_col=col, rng=rng, user_id=user_id, conv_id=conv_id.strip(),
            exec_id=exec_id.strip(), msg_id=msg_id.strip(), route=route.strip(), before=before, size=size,
            **({'handled': handled} if handled else {}),
        )
        rated = _rated_messages(rows)
    except Exception as exc:  # noqa: BLE001
        log.warning("admin feedback list failed: %s", exc)
        return listing.error(503, "反馈记录暂时无法读取", "list_unavailable")
    items = [_feedback_item(r, rated.get(str(r.get("assistant_msg_id") or "")), names) for r in rows]
    nxt = listing.encode_cursor(rows[-1].get(col), rows[-1].get("round_id")) if has_more and rows else None
    return listing.envelope(
        items,
        next_cursor=nxt,
        has_more=has_more,
        time_field="created_at（执行开始时间）" if col == "created_at" else "feedback_at（反馈时间）",
        range=listing.public_range(rng),
        issue_status="已接入",
    )


@app.get("/api/kb/admin/feedback/{exec_id}")
async def admin_feedback_detail(exec_id: str, request: Request):
    """STEP-A16：反馈详情。只展示用户实际评价的版本；刷新后默认版本变了也不把新答案当评价对象。"""
    row = logs.get_round(exec_id)
    if not row:
        if logs.last_error:
            return listing.error(503, "反馈记录暂时无法读取", "list_unavailable")
        return listing.error(404, "未找到该执行", "not_found")
    if not row.get("feedback"):
        return listing.error(404, "该执行没有反馈", "not_found")
    names = _account_usernames()
    item = _feedback_item(row, None, names)
    rated = user = None
    current = None
    versions: list[dict] = []
    if not item["legacy"] and row.get("conv_id"):
        try:
            cid = str(row["conv_id"])
            ids = [str(x) for x in (row.get("assistant_msg_id"), row.get("user_msg_id")) if x]
            found = {m["id"]: m for m in msgs.get_by_ids(cid, ids)}
            rated = found.get(str(row.get("assistant_msg_id") or ""))
            user = found.get(str(row.get("user_msg_id") or ""))
            if row.get("logical_round_id"):
                for m in msgs.round_rows(cid, str(row["logical_round_id"])):
                    if m["role"] != "assistant":
                        continue
                    versions.append({"msg_id": m["id"], "version_no": m.get("version_no"), "is_current": bool(m.get("is_current", 1))})
                    if int(m.get("is_current", 1) or 0):
                        current = m
        except Exception as exc:  # noqa: BLE001
            log.warning("admin feedback detail failed: %s", exc)
            return listing.error(503, "反馈记录暂时无法读取", "list_unavailable")
        item = _feedback_item(row, rated, names)
    if not auth.record_sensitive_read(
        actor=getattr(request.state, "account", None),
        object_type="feedback",
        object_id=exec_id,
        ip=_client_ip(request),
    ):
        diag.record("audit_write_fail", "sensitive_read", exec_id=exec_id)
    stale = bool(rated and current and current["id"] != rated["id"])
    return {
        **item,
        "question": (user or {}).get("content") if user else (row.get("original_query") or ""),
        # 只给被评价版本的正文；当前默认版本只给编号，不放进详情充当评价对象
        "rated_content": (rated or {}).get("content") if rated else (row.get("answer") or ""),
        "rated_completeness": (rated or {}).get("completeness") if rated else None,
        "stale": stale,
        "stale_note": (f"此反馈属于旧版（v{rated.get('version_no')}），当前默认为 v{current.get('version_no')}" if stale else None),
        "current_version": ({"msg_id": current["id"], "version_no": current.get("version_no")} if current else None),
        "versions": versions,
        "tz": settings.DISPLAY_TZ,
        "stored_tz": "UTC",
    }


@app.get("/api/kb/admin/heatmap")
async def admin_heatmap():
    data = logs.heatmap()
    items = []
    for item in data.get("items") or []:
        row = dict(item)
        row["display_name"] = c20_display_name(str(row.get("feature_id") or ""))
        items.append(row)
    return {
        "items": items,
        "unclassified": data.get("unclassified", 0),
        "unclassified_legacy": data.get("unclassified_legacy", 0),
        "legacy_rows": data.get("legacy_rows", 0),
    }


@app.get("/api/kb/admin/perms")
async def admin_perms(request: Request):
    account, err = _require_super(request)
    if err:
        return err
    return {"items": list(PERM_CHECKBOX)}


@app.get("/api/kb/admin/accounts")
async def admin_list_accounts(request: Request):
    account, err = _require_super(request)
    if err:
        return err
    qp = request.query_params
    q = str(qp.get("q") or "").strip().lower()
    role_id = str(qp.get("role_id") or "")
    enabled = str(qp.get("enabled") or "")
    rows = []
    for acc in auth.repo.list_accounts():
        if q and q not in str(acc.get("username") or "").lower():
            continue
        if role_id and str(acc.get("role_id") or "") != role_id:
            continue
        if enabled in ("0", "1") and int(bool(acc.get("enabled"))) != int(enabled):
            continue
        rows.append(acc)
    try:
        page, nxt, has_more = listing.paginate(
            rows,
            ts_of=lambda r: r.get("created_at"),
            id_of=lambda r: r.get("id"),
            cursor=str(qp.get("cursor") or ""),
            size=listing.page_size(qp.get("page_size")),
        )
    except listing.BadCursor:
        return listing.error(400, "游标无效", "bad_cursor")
    return listing.envelope(
        [auth.public_account(a) for a in page],
        next_cursor=nxt,
        has_more=has_more,
        total=len(rows),
        time_field="created_at（开户时间）",
    )


@app.post("/api/kb/admin/accounts")
async def admin_create_account(request: Request):
    account, err = _require_super(request)
    if err:
        return err
    try:
        body = await request.json()
    except Exception:  # noqa: BLE001
        return _deny(400, "请求体无效")
    if not isinstance(body, dict):
        return _deny(400, "请求体无效")
    uname = str(body.get("username") or "").strip()
    op_id, err = _hr_begin(
        request, account, "create_account", "account", uname,
        detail={"username": uname, "role_id": str(body.get("role_id") or "")},
    )
    if err:
        return err
    try:
        created = auth.create_user(
            str(body.get("username") or ""),
            str(body.get("password") or ""),
            str(body.get("role_id") or ""),
        )
    except ValueError as exc:
        auth.finish_audit(op_id, "failed", error_code="invalid_request")
        return _deny(400, str(exc))
    auth.finish_audit(
        op_id, "success",
        object=str(created.get("id") or ""),
        detail={"username": created.get("username"), "role_id": created.get("role_id")},
    )
    return created


@app.patch("/api/kb/admin/accounts/{account_id}")
async def admin_patch_account(account_id: str, request: Request):
    account, err = _require_super(request)
    if err:
        return err
    try:
        body = await request.json()
    except Exception:  # noqa: BLE001
        return _deny(400, "请求体无效")
    if not isinstance(body, dict):
        return _deny(400, "请求体无效")
    if "enabled" not in body and "role_id" not in body:
        return _deny(400, "没有可改字段")
    raw_before = auth.repo.get_account(account_id)
    before = auth.public_account(raw_before) if raw_before else None
    op_id = None
    try:
        out = None
        if "enabled" in body:
            op_id, err = _hr_begin(
                request, account,
                "disable_account" if not bool(body.get("enabled")) else "enable_account",
                "account", account_id,
                detail={"enabled": bool(body.get("enabled"))},
                changed_fields=["enabled"],
            )
            if err:
                return err
            out = auth.set_account_enabled(account_id, bool(body.get("enabled")))
            auth.finish_audit(op_id, "success", detail={
                "enabled": bool(body.get("enabled")),
                "before": {"enabled": (before or {}).get("enabled")},
                "after": {"enabled": out.get("enabled")},
            })
            op_id = None
        if "role_id" in body:
            op_id, err = _hr_begin(
                request, account, "change_role", "account", account_id,
                detail={"role_id": str(body.get("role_id") or "")},
                changed_fields=["role_id"],
            )
            if err:
                return err
            out = auth.set_account_role(account_id, str(body.get("role_id") or ""))
            auth.finish_audit(op_id, "success", detail={
                "role_id": str(body.get("role_id") or ""),
                "before": {"role_id": (before or {}).get("role_id"), "role_name": (before or {}).get("role_name")},
                "after": {"role_id": out.get("role_id"), "role_name": out.get("role_name")},
            })
            op_id = None
    except KeyError as exc:
        if op_id:
            auth.finish_audit(op_id, "failed", error_code="not_found")
        return _deny(404, str(exc))
    except PermissionError as exc:
        if op_id:
            auth.finish_audit(op_id, "failed", error_code="last_super")
        return _deny(403, str(exc))
    except ValueError as exc:
        if op_id:
            auth.finish_audit(op_id, "failed", error_code="invalid_request")
        return _deny(400, str(exc))
    return out


@app.get("/api/kb/admin/roles")
async def admin_list_roles(request: Request):
    account, err = _require_super(request)
    if err:
        return err
    return {
        "items": auth.list_roles_public(),
        "checkboxes": list(PERM_CHECKBOX),
        "pending": list(PENDING_PERMS),
    }


@app.get("/api/kb/admin/perm-migration")
async def admin_perm_migration(request: Request):
    """G-ADM-E06 迁移报告：持有已停用旧码的角色，新权限不自动附加。"""
    account, err = _require_super(request)
    if err:
        return err
    return {
        "items": auth.perm_migration_report(),
        "new_permissions": list(NEW_PERMS),
        "retired": [{"code": k, **v} for k, v in RETIRED_PERMS.items()],
    }


@app.post("/api/kb/admin/roles")
async def admin_create_role(request: Request):
    account, err = _require_super(request)
    if err:
        return err
    try:
        body = await request.json()
    except Exception:  # noqa: BLE001
        return _deny(400, "请求体无效")
    if not isinstance(body, dict):
        return _deny(400, "请求体无效")
    perms = body.get("permissions") if isinstance(body.get("permissions"), list) else []
    op_id, err = _hr_begin(request, account, "create_role", "role", str(body.get("name") or ""))
    if err:
        return err
    created = auth.create_custom_role(str(body.get("name") or ""), [str(p) for p in perms])
    auth.finish_audit(
        op_id, "success",
        object=str(created.get("id") or ""),
        detail={"permissions": created.get("permissions") or []},
    )
    return created


@app.put("/api/kb/admin/roles/{role_id}/permissions")
async def admin_set_role_perms(role_id: str, request: Request):
    account, err = _require_super(request)
    if err:
        return err
    try:
        body = await request.json()
    except Exception:  # noqa: BLE001
        return _deny(400, "请求体无效")
    if not isinstance(body, dict):
        return _deny(400, "请求体无效")
    perms = body.get("permissions") if isinstance(body.get("permissions"), list) else []
    before = sorted(auth.repo.get_role_perms(role_id)) if auth.repo.get_role(role_id) else []
    op_id, err = _hr_begin(
        request, account, "change_role_perms", "role", role_id, changed_fields=["permissions"],
    )
    if err:
        return err
    try:
        out = auth.set_custom_role_perms(role_id, [str(p) for p in perms])
    except KeyError as exc:
        auth.finish_audit(op_id, "failed", error_code="not_found")
        return _deny(404, str(exc))
    except PermissionError as exc:
        auth.finish_audit(op_id, "failed", error_code="super_role_locked")
        return _deny(403, str(exc))
    after = out.get("permissions") or []
    auth.finish_audit(op_id, "success", detail={
        "permissions": after,
        "before": {"permissions": before},
        "after": {"permissions": after},
        "added": sorted(set(after) - set(before)),
        "removed": sorted(set(before) - set(after)),
    })
    return out


@app.get("/api/kb/admin/login-lock")
async def admin_login_lock(request: Request, username: str = ""):
    """按用户名查看登录失败锁定状态（仅超管）。"""
    account, err = _require_super(request)
    if err:
        return err
    if not username.strip():
        return _deny(400, "用户名必填")
    return auth.lock_status(username)


@app.post("/api/kb/admin/unlock")
async def admin_unlock(request: Request):
    account, err = _require_super(request)
    if err:
        return err
    try:
        body = await request.json()
    except Exception:  # noqa: BLE001
        return _deny(400, "请求体无效")
    if not isinstance(body, dict):
        return _deny(400, "请求体无效")
    username = str(body.get("username") or "").strip()
    if not username:
        return _deny(400, "用户名必填")
    op_id, err = _hr_begin(request, account, "unlock", "login_lock", username, detail={"username": username})
    if err:
        return err
    auth.unlock_username(username)
    auth.finish_audit(op_id, "success")
    return {"ok": True}


@app.get("/api/kb/admin/tls")
async def admin_tls_status(request: Request):
    account, err = _require_super(request)
    if err:
        return err
    return tls.status()


@app.post("/api/kb/admin/tls")
async def admin_tls_upload(request: Request):
    account, err = _require_super(request)
    if err:
        return err
    try:
        body = await request.json()
    except Exception:  # noqa: BLE001
        return _deny(400, "请求体无效")
    if not isinstance(body, dict):
        return _deny(400, "请求体无效")
    op_id, err = _hr_begin(request, account, "tls_upload", "tls", "tls")
    if err:
        return err
    try:
        out = tls.save_upload(str(body.get("cert_pem") or ""), str(body.get("key_pem") or ""))
    except ValueError as exc:
        auth.finish_audit(op_id, "failed", error_code="invalid_cert")
        return _deny(400, str(exc))
    auth.finish_audit(op_id, "success", detail={"has_cert": True})
    return out


@app.post("/api/kb/admin/tls/enable")
async def admin_tls_enable(request: Request):
    account, err = _require_super(request)
    if err:
        return err
    op_id, err = _hr_begin(request, account, "tls_enable", "tls", "tls")
    if err:
        return err
    try:
        out = tls.enable()
    except ValueError as exc:
        auth.finish_audit(op_id, "failed", error_code="invalid_cert")
        return _deny(400, str(exc))
    auth.finish_audit(op_id, "success", detail={"enabled": True})
    return out


@app.post("/api/kb/admin/tls/disable")
async def admin_tls_disable(request: Request):
    account, err = _require_super(request)
    if err:
        return err
    op_id, err = _hr_begin(request, account, "tls_disable", "tls", "tls")
    if err:
        return err
    out = tls.disable()
    auth.finish_audit(op_id, "success", detail={"enabled": False})
    return out


_PROMPT_KEYS = ("system_prompt", "rewrite_prompt")
_PROMPT_INPUT_KEYS = ("系统 Prompt", "改写 Prompt", "system_prompt", "rewrite_prompt")
_PROMPT_FIELD_NAMES = ("系统 Prompt", "改写 Prompt")


def _config_view(snap: dict, account: dict | None) -> dict:
    """按查看人权限过滤配置：无 Prompt查看不给 Prompt 正文，无配置查看不给参数与只读项。"""
    can_cfg = auth.has_perm(account, "配置查看")
    can_prompt = auth.has_perm(account, "Prompt查看")
    writable = {}
    for key, value in (snap.get("writable") or {}).items():
        is_prompt = key in _PROMPT_KEYS or key == 'prompts'
        if (is_prompt and can_prompt) or (not is_prompt and can_cfg):
            writable[key] = value
    fields = [
        f for f in (snap.get("writable_fields") or [])
        if (f in _PROMPT_FIELD_NAMES and can_prompt) or (f not in _PROMPT_FIELD_NAMES and can_cfg)
    ]
    return {
        "writable": writable,
        "readonly": snap.get("readonly") if can_cfg else {},
        "readonly_fields": snap.get("readonly_fields") if can_cfg else [],
        "writable_fields": fields,
        "visible": {"config": can_cfg, "prompt": can_prompt},
        "editable": {
            "config": can_cfg and auth.has_perm(account, "配置编辑"),
            "prompt": can_prompt and auth.has_perm(account, "Prompt编辑"),
        },
        "package_id": snap.get("package_id"),
        "draft_rev": snap.get("draft_rev") or 0,
        "draft": _filter_writable(snap.get("draft") or {}, can_cfg, can_prompt) if snap.get("draft") else None,
        "fixed_rules": snap.get("fixed_rules") if can_cfg else [],
        "pools": snap.get("pools") if can_cfg else {},
        "history_recovery": snap.get("history_recovery", True) if can_cfg else None,
        "recall_budget": snap.get("recall_budget") if can_cfg else None,
        "test_budget": snap.get('test_budget') if can_cfg else None,
        "unconnected": snap.get("unconnected") if can_cfg else [],
        "key_note": snap.get("key_note") if can_cfg else "",
        "prompts": snap.get("prompts") if can_prompt else [],
        'published_prompts': snap.get('published_prompts') if can_prompt else [],
        "published": _filter_writable(snap.get('published') or {}, can_cfg, can_prompt),
        "history": [{**{k: v for k, v in x.items() if k != 'data'},
                     'data': _filter_writable(x.get('data') or {}, can_cfg, can_prompt)} for x in snap.get('history') or []],
    }


def _filter_writable(raw: dict, can_cfg: bool, can_prompt: bool) -> dict:
    out = {}
    for key, value in raw.items():
        is_prompt = key in _PROMPT_KEYS or key == 'prompts'
        if (is_prompt and can_prompt) or (not is_prompt and can_cfg):
            out[key] = value
    return out


def _can_review_package(account, data, extra) -> bool:
    """发布者可以独立于编辑者；但必须能阅读拟发布的整包内容。"""
    return auth.has_perm(account, '配置查看') and auth.has_perm(account, 'Prompt查看')


@app.get("/api/kb/config")
async def get_config(request: Request):
    return _config_view(config_store.snapshot(), getattr(request.state, "account", None))


@app.put("/api/kb/config")
async def put_config(request: Request, body: dict):
    writable = body.get("writable") if isinstance(body.get("writable"), dict) else body
    if not isinstance(writable, dict):
        writable = {}
    account = getattr(request.state, "account", None)
    touches_prompt = any(k in writable and writable[k] is not None for k in _PROMPT_INPUT_KEYS) or "prompts" in writable
    touches_config = any(k not in (*_PROMPT_INPUT_KEYS, 'prompts', 'rev') for k in writable)
    if touches_config and not (auth.has_perm(account, '配置查看') and auth.has_perm(account, '配置编辑')):
        return listing.error(403, '没有修改配置的权限', 'forbidden')
    if touches_prompt and not (auth.has_perm(account, "Prompt编辑") and auth.has_perm(account, "Prompt查看")):
        return JSONResponse(
            {"ok": False, "code": "forbidden", "message": "没有修改 Prompt 的权限"},
            status_code=403,
        )
    # 保存只写草稿，不改当前生效包
    op_id, err = _hr_begin(
        request, account, "config_update", "config", "config",
        detail={"fields": list(writable.keys())},
        changed_fields=list(writable.keys()),
    )
    if err:
        return err
    try:
        out = _config_view(config_store.update_writable(writable), account)
    except ConfigConflict as exc:
        auth.finish_audit(op_id, "failed", error_code="draft_conflict")
        diff = dict(exc.diff)
        if 'draft' in diff:
            diff['draft'] = _filter_writable(diff['draft'] or {}, auth.has_perm(account, '配置查看'), auth.has_perm(account, 'Prompt查看'))
        return listing.error(409, str(exc), "draft_conflict", diff=diff)
    except ValueError as exc:
        auth.finish_audit(op_id, "failed", error_code="config_invalid")
        return listing.error(400, str(exc), "config_invalid")
    except Exception:
        auth.finish_audit(op_id, "failed", error_code="config_write_failed")
        raise
    auth.finish_audit(op_id, "success")
    return out


@app.post("/api/kb/config/publish")
async def publish_config(request: Request):
    """把当前草稿切成生效包。同一操作号再提交不重复切换。"""
    account = getattr(request.state, "account", None)
    try:
        body = await request.json()
    except Exception:  # noqa: BLE001
        body = {}
    if not isinstance(body, dict):
        body = {}
    if not _can_review_package(account, config_store.draft, config_store.draft_extra):
        return listing.error(403, '需要查看本次发布内容的权限', 'forbidden')
    if 'rev' not in body:
        return listing.error(400, '需要已审阅的精确草稿修订', 'bad_request')
    client_op = str(body.get("op_id") or "").strip() or None
    repeated = bool(client_op and client_op in config_store.publish_ops)
    op_id, err = _hr_begin(request, account, "config_publish", "config", client_op or "config")
    if err:
        return err
    try:
        result = config_store.publish(body.get("rev"), client_op, str(body.get('reason') or ''))
    except ConfigConflict as exc:
        auth.finish_audit(op_id, "failed", error_code="publish_conflict")
        return listing.error(409, str(exc), "publish_conflict")
    except ValueError as exc:
        text = str(exc)
        code = "release_blocked" if "关键用例" in text else "incompatible"
        auth.finish_audit(op_id, "failed", error_code=code)
        return listing.error(400, text, code)
    except Exception:
        auth.finish_audit(op_id, 'failed', error_code='config_write_failed')
        return listing.error(503, '配置写入失败，生效包未切换', 'config_write_failed')
    auth.finish_audit(op_id, "success", detail={"package_id": result.get("package_id")})
    return {"ok": True, "repeated": repeated, **result}


@app.post("/api/kb/config/rollback")
async def rollback_config(request: Request):
    """回退到一个兼容的历史包，本身也是一次新发布。"""
    account = getattr(request.state, "account", None)
    try:
        body = await request.json()
    except Exception:  # noqa: BLE001
        body = {}
    if not isinstance(body, dict):
        body = {}
    target = str(body.get("package_id") or "").strip()
    if not target:
        return listing.error(400, "需要历史版本号", "bad_request")
    package = config_store.packages.get(target) or next((x.get('data') for x in config_store.history if x.get('id') == target), None)
    if not _can_review_package(account, package, package):
        return listing.error(403, '需要查看回退内容的权限', 'forbidden')
    op_id, err = _hr_begin(request, account, "config_rollback", "config", target)
    if err:
        return err
    try:
        result = config_store.rollback(target, str(body.get("op_id") or "").strip() or None)
    except KeyError:
        auth.finish_audit(op_id, "failed", error_code="not_found")
        return listing.error(404, "未找到该版本", "not_found")
    except ConfigConflict as exc:
        auth.finish_audit(op_id, "failed", error_code="publish_conflict")
        return listing.error(409, str(exc), "publish_conflict")
    except ValueError as exc:
        auth.finish_audit(op_id, "failed", error_code="incompatible")
        return listing.error(400, str(exc), "incompatible")
    except Exception:
        auth.finish_audit(op_id, 'failed', error_code='config_write_failed')
        return listing.error(503, '配置写入失败，生效包未切换', 'config_write_failed')
    auth.finish_audit(op_id, "success", detail={"package_id": result.get("package_id"), "rolled_back_to": target})
    return {"ok": True, **result}


@app.post('/api/kb/config/discard')
@app.post('/api/kb/config/restore-draft')
async def change_config_draft(request: Request, body: dict):
    account = getattr(request.state, 'account', None)
    # 整包替换/丢弃会同时改变参数和 Prompt，必须具备双方查看与编辑权限。
    if not all(auth.has_perm(account, p) for p in ('配置查看', '配置编辑', 'Prompt查看', 'Prompt编辑')):
        return listing.error(403, '整包操作需要配置与 Prompt 的查看、编辑权限', 'forbidden')
    op_id, err = _hr_begin(request, account, 'draft_replace', 'config', str(body.get('package_id') or 'draft'))
    if err:
        return err
    try:
        rev = int(body['rev'])
        if request.url.path.endswith('/discard'):
            out = config_store.discard(rev)
        else:
            out = config_store.restore_draft(str(body.get('package_id') or ''), rev)
    except ConfigConflict as exc:
        auth.finish_audit(op_id, 'failed', error_code='draft_conflict')
        return listing.error(409, str(exc), 'draft_conflict')
    except (ValueError, KeyError, TypeError) as exc:
        auth.finish_audit(op_id, 'failed', error_code='bad_request')
        return listing.error(400, str(exc), 'bad_request')
    except Exception:
        auth.finish_audit(op_id, 'failed', error_code='config_write_failed')
        return listing.error(503, '草稿未写入', 'config_write_failed')
    auth.finish_audit(op_id, 'success')
    return _config_view(out, account)


@app.get('/api/kb/config/ops/{op_id}')
async def config_operation(op_id: str):
    result = config_store.publish_ops.get(op_id)
    return {'ok': True, 'status': 'done', **result} if result else listing.error(404, '未找到已完成的发布操作', 'not_found')


def _require_debug(request: Request):
    """调试要 Prompt调试，并且能看对话或消息。登录本身不算调试授权。"""
    account = getattr(request.state, "account", None)
    if not account:
        return None, _deny(401, "未登录")
    if not auth.has_perm(account, "Prompt调试"):
        return None, listing.error(403, "没有 Prompt调试权限", "forbidden")
    if not (auth.has_perm(account, 'Prompt查看') and auth.has_perm(account, '配置查看')):
        return None, listing.error(403, '还需要 Prompt 与配置查看权限', 'forbidden')
    return account, None


@app.post("/api/kb/admin/test-runs")
async def start_test_run(request: Request):
    """隔离测试：不写生产消息、版本、反馈和记忆索引。"""
    account, err = _require_debug(request)
    if err:
        return err
    try:
        body = await request.json()
    except Exception:  # noqa: BLE001
        body = {}
    if not isinstance(body, dict):
        body = {}
    if body.get('exec_id'):
        if not auth.has_perm(account, '问答明细'):
            return listing.error(403, '带入执行消息需要问答明细权限', 'forbidden')
        execution = logs.get_round(str(body['exec_id']))
        if not execution:
            return listing.error(404, '未找到该执行', 'not_found')
        cid = str(execution.get('conv_id') or '')
        allowed = {str(execution.get(k)) for k in ('user_msg_id', 'assistant_msg_id') if execution.get(k)}
        selected = body.get('message_ids')
        if not isinstance(selected, list) or not selected or not set(selected).issubset(allowed):
            return listing.error(403, '只能带入该执行已授权的提问和回答，历史上下文需要对话审计权限', 'forbidden')
        if body.get('conv_id') and body['conv_id'] != cid:
            return listing.error(400, '执行与会话编号不一致', 'source_mismatch')
        body = dict(body, conv_id=cid)
    elif body.get('conv_id') and not auth.has_perm(account, '对话审计'):
        return listing.error(403, '带入会话原文需要对话审计权限', 'forbidden')
    if body.get('real_knowledge') and not (auth.has_perm(account, '知识问答') or auth.has_perm(account, '知识源查看')):
        return listing.error(403, '真实知识调用需要知识读取权限', 'forbidden')
    cfg = config_store.test_config()
    op_id, err = _hr_begin(request, account, 'test_start', 'test_run', 'new')
    if err:
        return err
    try:
        row = test_book.start(body, str(account["id"]), cfg)
        auth.finish_audit(op_id, 'success', detail={'test_run_id': row['id']})
        return JSONResponse(row, status_code=202)
    except TestError as exc:
        auth.finish_audit(op_id, 'failed', error_code='test_rejected')
        return listing.error(400, exc.message, "test_rejected")


@app.get("/api/kb/admin/test-runs/compare")
async def compare_test_runs(request: Request, a: str = "", b: str = ""):
    account, err = _require_debug(request)
    if err:
        return err
    for run_id in (a, b):
        denied = _test_read_denial(account, test_book.get(run_id))
        if denied:
            return denied
    try:
        return test_book.compare(a, b)
    except TestError as exc:
        return listing.error(404, exc.message, "not_found")


@app.get('/api/kb/admin/test-runs')
async def list_test_runs(request: Request, cursor: str = '', page_size: str = ''):
    account, err = _require_debug(request)
    if err:
        return err
    rows = [r for r in test_book.runs.values() if not _test_read_denial(account, r)]
    try:
        rows, nxt, more = listing.paginate(rows, ts_of=lambda r: r['created_at'], id_of=lambda r: r['id'],
                                         cursor=cursor, size=listing.page_size(page_size))
    except listing.BadCursor:
        return listing.error(400, '游标无效', 'bad_cursor')
    return listing.envelope([test_book.get(r['id']) for r in rows], next_cursor=nxt, has_more=more, time_field='created_at')


@app.get('/api/kb/admin/test-cases')
async def list_test_cases(request: Request):
    account, err = _require_debug(request)
    if err:
        return err
    return {'items': list(test_book.cases.values())}


@app.get("/api/kb/admin/test-runs/{run_id}")
async def get_test_run(run_id: str, request: Request):
    account, err = _require_debug(request)
    if err:
        return err
    row = test_book.get(run_id)
    if not row:
        return listing.error(404, "未找到该测试", "not_found")
    denied = _test_read_denial(account, row)
    if denied:
        return denied
    return row


def _test_read_denial(account, row):
    if not row:
        return listing.error(404, '未找到该测试', 'not_found')
    if row.get('actor') != str(account['id']) and not account.get('is_super'):
        return listing.error(403, '没有该测试的查看权限', 'forbidden')
    if row.get('source_exec') and not auth.has_perm(account, '问答明细'):
        return listing.error(403, '消息查看权限已不足', 'forbidden')
    if row.get('source_conv') and not row.get('source_exec') and not auth.has_perm(account, '对话审计'):
        return listing.error(403, '原文查看权限已不足', 'forbidden')
    if row.get('real_knowledge') and not (auth.has_perm(account, '知识问答') or auth.has_perm(account, '知识源查看')):
        return listing.error(403, '知识读取权限已不足', 'forbidden')
    return None


@app.post("/api/kb/admin/test-cases")
async def add_test_case(request: Request):
    """发布必过项。非关键未覆盖只在发布结果里警告。"""
    account = getattr(request.state, "account", None)
    if not account or not auth.has_perm(account, "配置发布"):
        return listing.error(403, "没有配置发布权限", "forbidden")
    try:
        body = await request.json()
    except Exception:  # noqa: BLE001
        body = {}
    if not isinstance(body, dict):
        return listing.error(400, "请求体无效", "bad_request")
    op_id, err = _hr_begin(request, account, 'test_case_create', 'test_case', str(body.get('id') or 'new'))
    if err:
        return err
    try:
        row = test_book.add_case(body)
    except TestError as exc:
        auth.finish_audit(op_id, 'failed', error_code='case_invalid')
        return listing.error(400, exc.message, 'case_invalid')
    auth.finish_audit(op_id, 'success', detail={'case_id': row['id']})
    return row


def _task_conflict(existing: dict):
    return listing.error(
        409,
        f"已有进行中的任务 {existing['id']}",
        "task_overlap",
        task_id=existing["id"],
    )


def _controlled_source(chunk) -> dict:
    return {
        "path": chunk.path,
        "feature_id": chunk.feature_id,
        "chunk_id": chunk.chunk_id,
        "heading": chunk.heading or "缺失",
        "anchor": chunk.anchor or "缺失",
        "collection": chunk.collection,
        "content_hash": chunk.content_hash,
        "hash_note": "这是正文哈希，不是生效日期或业务版本",
        "source_version": "未提供",
        "integrity": "切片",
        "integrity_note": "chunk:default 只覆盖这段切片，不是整份文档",
        "oversized": bool(chunk.oversized),
        "readable": "不可读" if chunk.oversized else "正常",
    }


@app.get("/api/kb/admin/knowledge-sources")
async def knowledge_sources(path: str = "", feature_id: str = "", cursor: str = '', page_size: str = ''):
    """受控来源只读。不接受任意服务器路径。"""
    if path and (path.startswith("/") or path.startswith("\\") or ".." in path):
        return listing.error(400, "不能指定任意路径", "source_rejected")
    from .chunking import scan_briefs

    chunks = scan_briefs()
    known = {c.path for c in chunks}
    if path and path not in known:
        return listing.error(400, "只能查看受控来源", "source_rejected")
    items = [
        _controlled_source(c) for c in chunks
        if (not path or c.path == path) and (not feature_id or c.feature_id == feature_id)
    ]
    try:
        items, nxt, more = listing.paginate(items, ts_of=lambda r: r['path'], id_of=lambda r: r['chunk_id'], cursor=cursor, size=listing.page_size(page_size))
    except listing.BadCursor:
        return listing.error(400, '游标无效', 'bad_cursor')
    return listing.envelope(items, next_cursor=nxt, has_more=more, time_field='来源 path / chunk_id 排序', note='只读。不能在这里新增来源。')


@app.get('/api/kb/admin/knowledge-sources/detail')
async def knowledge_source_detail(request: Request, path: str = '', chunk_id: str = ''):
    from .chunking import scan_briefs
    source = next((c for c in scan_briefs() if c.path == path and c.chunk_id == chunk_id), None)
    if not source:
        return listing.error(404, '未找到受控来源切片', 'source_not_found')
    try:
        indexed = store.lookup_payload(path, chunk_id)
    except Exception:
        indexed = None
    auth.record_sensitive_read(actor=getattr(request.state, 'account', None), object_type='knowledge_source', object_id=chunk_id, ip=_client_ip(request))
    return {**_controlled_source(source), 'content': source.content,
            'indexed_hash': (indexed or {}).get('content_hash'),
            'index_consistent': (indexed or {}).get('content_hash') == source.content_hash if indexed else None,
            'index_generation': (indexed or {}).get('generation'), 'indexed_at': (indexed or {}).get('indexed_at')}


@app.post("/api/kb/admin/knowledge-sources")
async def knowledge_sources_reject():
    return listing.error(400, "不能新增任意来源", "source_rejected")


@app.get("/api/kb/admin/index-tasks")
async def list_index_tasks(group: str = "", cursor: str = '', page_size: str = ''):
    try:
        rows, nxt, more = index_tasks.repo.page(group, cursor, listing.page_size(page_size))
    except listing.BadCursor:
        return listing.error(400, '游标无效', 'bad_cursor')
    except Exception:
        return listing.error(503, '索引任务暂时无法读取', 'list_unavailable')
    return listing.envelope([index_tasks.public(r) for r in rows], next_cursor=nxt, has_more=more, time_field='created_at')


@app.get("/api/kb/admin/index-tasks/{task_id}")
async def get_index_task(task_id: str):
    row = index_tasks.get(task_id)
    if not row:
        return listing.error(404, "未找到该任务", "task_not_found")
    return index_tasks.public(row)


def _finish_knowledge(task_id: str, result: dict) -> dict:
    failed = list(result.get("failed") or [])
    changed = list(result.get("changed") or [])
    status = "partial" if failed else "done"
    index_tasks.finish(
        task_id, status,
        scanned=int(result.get("scanned") or 0),
        changed=len(changed),
        failed=len(failed),
        detail={"changed": changed, "failed": failed},
    )
    integrity = "partial" if failed else "complete"
    return {
        "ok": not failed,
        "task_id": task_id,
        "integrity": integrity,
        "complete": not failed,
        **result,
    }


async def _run_knowledge(actor_id: str, parent_id: str | None = None):
    task, existing = index_tasks.accept("knowledge", "rebuild", "all", actor_id, parent_id)
    if existing:
        return None, existing
    try:
        result = await indexer.rebuild()
    except ModelError as exc:
        index_tasks.finish(task["id"], "failed", error=str(exc.code or "rebuild_failed"))
        raise
    except Exception as exc:  # noqa: BLE001
        index_tasks.finish(task["id"], "failed", error=str(exc)[:200])
        raise
    return _finish_knowledge(task["id"], result), None


@app.post("/api/kb/reindex")
async def reindex(request: Request):
    account = getattr(request.state, "account", None)
    miss = missing_keys()
    if "DASHSCOPE_API_KEY" in miss:
        return JSONResponse(
            {"ok": False, "error_type": "missing_key", "message": "缺 Key：未配置 DASHSCOPE_API_KEY"},
            status_code=400,
        )
    if not store.ping():
        return JSONResponse(
            {"ok": False, "error_type": "index_not_ready", "message": "索引未就绪：Qdrant 不可用"},
            status_code=503,
        )
    # 重叠先拒绝，避免再派发一次重建
    if index_tasks._overlap("knowledge", "all"):
        existing = index_tasks._overlap("knowledge", "all")
        return _task_conflict(existing)
    op_id, err = _hr_begin(request, account, "reindex", "index", str(account["id"]))
    if err:
        return err
    async with index_lock:
        try:
            body, existing = await _run_knowledge(str(account["id"]))
        except ModelError as exc:
            auth.finish_audit(op_id, "failed", error_code=str(exc.code or "rebuild_failed"))
            return JSONResponse(
                {"ok": False, "error_type": exc.code, "message": exc.message},
                status_code=exc.status_code,
            )
    if existing:
        auth.finish_audit(op_id, "failed", error_code="task_overlap", detail={"task_id": existing["id"]})
        return _task_conflict(existing)
    global index_ready
    index_ready = body.get("chunk_count", 0) > 0
    auth.finish_audit(op_id, "success" if body.get("complete") else "failed", detail={
        "task_id": body.get("task_id"), "integrity": body.get("integrity"),
    })
    return body


@app.post("/api/kb/admin/index-tasks/{task_id}/retry")
async def retry_index_task(task_id: str, request: Request):
    """重试另起一条，保留父任务。父任务还在跑则不重复派发。"""
    account = getattr(request.state, "account", None)
    parent = index_tasks.get(task_id)
    if not parent:
        return listing.error(404, "未找到该任务", "task_not_found")
    if parent.get("status") == "running":
        return _task_conflict(parent)
    if parent.get("grp") == "memory":
        return await _memory_backfill(request, account, str(parent.get("scope") or ""), parent_id=parent["id"])
    miss = missing_keys()
    if "DASHSCOPE_API_KEY" in miss:
        return JSONResponse({"ok": False, "message": "缺 Key：未配置 DASHSCOPE_API_KEY"}, status_code=400)
    if not store.ping():
        return JSONResponse({"ok": False, "message": "索引未就绪：Qdrant 不可用"}, status_code=503)
    op_id, err = _hr_begin(request, account, "reindex", "index", str(account["id"]))
    if err:
        return err
    async with index_lock:
        try:
            body, existing = await _run_knowledge(str(account["id"]), parent_id=parent["id"])
        except ModelError as exc:
            auth.finish_audit(op_id, "failed", error_code=str(exc.code or "rebuild_failed"))
            return JSONResponse({"ok": False, "message": exc.message}, status_code=exc.status_code)
    if existing:
        auth.finish_audit(op_id, "failed", error_code="task_overlap")
        return _task_conflict(existing)
    auth.finish_audit(op_id, "success" if body.get("complete") else "failed", detail={"task_id": body["task_id"], "parent_id": parent["id"]})
    saved = index_tasks.get(parent["id"])
    return {"ok": True, "task": index_tasks.public(index_tasks.get(body["task_id"])), "parent": index_tasks.public(saved)}


_MEM_STATE = {
    "normal": "正常", "partial": "部分覆盖", "lagging": "落后", "failed": "失败",
    "unknown": "未知", "not_connected": "未接入",
}


@app.get("/api/kb/admin/memory-coverage")
async def memory_coverage(conv_id: str = ""):
    """覆盖只给状态和空洞，不给消息正文，也不能改成完整。"""
    if not conv_id:
        return listing.error(400, "需要会话编号", "bad_request")
    from .memory_index import indexable

    rows = []
    try:
        rows = msgs.admin_messages(conv_id)
        cov = mem_index.coverage(conv_id, rows)
    except Exception as exc:  # noqa: BLE001
        log.warning("memory coverage failed: %s", exc)
        return listing.error(503, "覆盖暂时无法计算", "list_unavailable")
    known_counts = cov.get("state") not in ("not_connected", "unknown")
    limited = [
        m["id"] for m in rows
        if indexable(m) and (not m.get("created_at") or (m.get("role") == "assistant" and not m.get("version_no")))
    ]
    stale = []
    if getattr(mem_index, "connected", False):
        known = {m["id"] for m in rows}
        try:
            for rec in mem_index.records.list_conv(conv_id):
                if rec.get("msg_id") not in known:
                    stale.append(rec["msg_id"])
        except Exception:  # noqa: BLE001
            stale = []
    def _num(key):
        return cov.get(key) if known_counts else None

    return {
        "ok": True,
        "conv_id": conv_id,
        "state": cov.get("state"),
        "state_label": _MEM_STATE.get(cov.get("state") or "", "未知"),
        "holes": cov.get("holes") or [],
        "expected": _num("expected"),
        "indexed": _num("indexed"),
        "pending": _num("pending"),
        "failed": _num("failed"),
        "backlog": _num("pending"),
        "gen": cov.get("gen"),
        "quality": "受限" if limited else "可核对",
        "quality_note": "旧记录缺时间或版本，不能当作完整原文" if limited else "",
        "stale_ids": stale,
        "manual_complete": False,
        "note": "不返回消息正文。不能手工改成完整。回填不恢复隐藏或清空后的用户可见性。",
    }


@app.post("/api/kb/admin/memory-coverage/complete")
async def memory_coverage_complete_rejected():
    return listing.error(400, "不能手工把覆盖改成完整", "manual_complete_forbidden")


async def _memory_backfill(request: Request, account: dict, conv_id: str, parent_id: str | None = None):
    scope = conv_id or "all"
    task, existing = index_tasks.accept("memory", "backfill", scope, str(account["id"]), parent_id)
    if existing:
        return _task_conflict(existing)
    op_id, err = _hr_begin(request, account, "index_backfill", "memory", scope or "all")
    if err:
        index_tasks.finish(task["id"], "failed", error="audit_unavailable")
        return err
    if conv_id:
        ids = [conv_id]
    else:
        ids = [str(r.get("id")) for r in convs.list_all() if r.get("id")]
    try:
        result = await mem_index.backfill(msgs, ids)
    except Exception as exc:  # noqa: BLE001
        index_tasks.finish(task["id"], "failed", error=str(exc)[:200])
        auth.finish_audit(op_id, "failed", error_code="backfill_failed")
        return listing.error(503, "回填失败", "backfill_failed")
    failed = int(result.get("failed") or 0)
    err_code = result.get("error")
    status = "failed" if err_code else ("partial" if failed else "done")
    index_tasks.finish(
        task["id"], status, scanned=int(result.get("convs") or 0),
        changed=int(result.get("indexed") or 0), failed=failed, error=err_code,
        detail={"skipped": result.get("skipped"), "note": "不恢复已隐藏或已清空内容的用户可见性"},
    )
    auth.finish_audit(op_id, "success" if status == "done" else "failed", detail={"task_id": task["id"]})
    saved = index_tasks.get(task["id"])
    return {
        "ok": status == "done",
        "task": index_tasks.public(saved),
        "note": "回填不恢复已隐藏或已清空内容的用户可见性",
    }


@app.post("/api/kb/admin/memory-backfill")
async def memory_backfill(request: Request):
    account = getattr(request.state, "account", None)
    try:
        body = await request.json()
    except Exception:  # noqa: BLE001
        body = {}
    if not isinstance(body, dict):
        body = {}
    return await _memory_backfill(request, account, str(body.get("conv_id") or "").strip())


@app.get("/api/kb/rounds")
async def list_rounds(
    q: str = "",
    feature_id: str = "",
    status: str = "",
    limit: int = Query(100, ge=1, le=500),
    feedback: str = "",
    pending: str = "",
    cursor: str = "",
    page_size: str = "",
    op_type: str = "",
    route: str = "",
    biz_result: str = "",
    exec_state: str = "",
    check_status: str = "",
    msg_save: str = "",
    requires_history: str = "",
    used_knowledge_rag: str = "",
):
    names = _account_usernames()
    # 按功能筛选仍走旧路径：取回后过滤，覆盖标为不完整
    if feature_id:
        items = [_attach_username(r, "user_id", names) for r in logs.list_rounds(
            q=q, feature_id=feature_id, status=status, limit=limit
        )]
        return listing.envelope(
            items, next_cursor=None, has_more=False, time_field="created_at（执行开始时间）",
            complete=False, note=f"按功能筛选只在最近 {limit} 条内过滤，结果可能不全",
        )
    try:
        before = listing.decode_cursor(cursor)
    except listing.BadCursor:
        return listing.error(400, "游标无效", "bad_cursor")
    # 旧调用只传 limit：沿用其值作页大小（上限 500 保持兼容）
    size = listing.page_size(page_size) if page_size else int(limit)
    try:
        rows, has_more = logs.page_rounds(
            q=q, status=status, feedback=feedback, pending=pending in ("1", "true"),
            before=before, size=size, op_type=op_type, route=route, biz_result=biz_result,
            exec_state=exec_state, check_status=check_status, msg_save=msg_save,
            requires_history=requires_history, used_knowledge_rag=used_knowledge_rag,
        )
    except Exception as exc:  # noqa: BLE001
        log.warning("page rounds failed: %s", exc)
        return listing.error(503, "问答记录暂时无法读取", "list_unavailable")
    nxt = listing.encode_cursor(rows[-1].get("created_at"), rows[-1].get("round_id")) if has_more and rows else None
    return listing.envelope(
        [_attach_username(r, "user_id", names) for r in rows],
        next_cursor=nxt,
        has_more=has_more,
        time_field="created_at（执行开始时间）",
    )


@app.get("/api/kb/rounds/{round_id}")
async def get_round(round_id: str, request: Request):
    row = logs.get_round(round_id)
    if not row:
        return JSONResponse({"message": "未找到该轮"}, status_code=404)
    # 敏感正文读取：尽力留痕，失败不影响返回
    if not auth.record_sensitive_read(
        actor=getattr(request.state, "account", None),
        object_type="exec",
        object_id=round_id,
        ip=_client_ip(request),
    ):
        diag.record("audit_write_fail", "sensitive_read", exec_id=round_id)
    shown = _attach_username(row, "user_id")
    shown["view"] = build_exec_view(row)
    return shown


@app.get("/api/kb/rounds/{round_id}/context/{msg_id}")
async def round_context_message(round_id: str, msg_id: str):
    """STEP-A07（T73）：展开本执行快照指向的历史正文。权限是「对话审计」，不是「问答明细」。"""
    row = logs.get_round(round_id)
    if not row or msg_id not in referenced_msg_ids(row):
        return listing.error(404, "没有这条历史正文", "message_not_found")
    try:
        found = msgs.get_by_ids(str(row.get("conv_id") or ""), [msg_id])
    except Exception as exc:  # noqa: BLE001
        log.warning("exec context lookup failed: %s", exc)
        return listing.error(503, "历史正文暂时无法读取", "source_unavailable")
    if not found:
        return listing.error(404, "没有这条历史正文", "message_not_found")
    return {"ok": True, "message": MsgStore.public(found[0])}


@app.post("/api/kb/rounds/{round_id}/feedback")
async def set_round_feedback(round_id: str, request: Request):
    """写入一轮反馈：仅提问人可改。库内空 / up / down。无此轮返回 404。"""
    account = getattr(request.state, "account", None)
    if not account:
        return _deny(401, "未登录")
    try:
        body = await request.json()
    except Exception:  # noqa: BLE001
        return JSONResponse({"message": "请求体无效"}, status_code=400)
    if not isinstance(body, dict) or "feedback" not in body:
        return JSONResponse({"message": "缺少 feedback"}, status_code=400)
    raw = body.get("feedback")
    if raw is None or raw == "":
        value = None
    elif raw in ("up", "down"):
        value = raw
    else:
        return JSONResponse({"message": "非法反馈值"}, status_code=400)
    row = logs.get_round(round_id)
    if not row:
        return JSONResponse({"message": "未找到该轮"}, status_code=404)
    if str(row.get("user_id") or "") != str(account.get("id") or ""):
        return _deny(403, "没有权限")
    sent_msg = str(body.get("assistant_msg_id") or "")
    bound_msg = str(row.get("assistant_msg_id") or "")
    if sent_msg and bound_msg and sent_msg != bound_msg:
        return JSONResponse(
            {"ok": False, "code": "feedback_target", "message": "不能把反馈改到别的回复上"},
            status_code=409,
        )
    # STEP-Q21：一版本一执行，反馈即绑定该版本；新记录只允许已保存且正常完成的回复，旧记录沿用原规则
    if row.get("schema_ver") and not (
        row.get("msg_save") == "saved"
        and row.get("assistant_msg_id")
        and row.get("status") in _DELIVERED_STATUS
    ):
        return JSONResponse(
            {"ok": False, "code": "feedback_not_allowed", "message": "该回复不支持赞踩"},
            status_code=409,
        )
    result = logs.set_feedback(round_id, value)
    if result == "not_found":
        return JSONResponse({"message": "未找到该轮"}, status_code=404)
    if result == "invalid":
        return JSONResponse({"message": "非法反馈值"}, status_code=400)
    if result != "ok":
        return JSONResponse({"message": "反馈写入失败"}, status_code=500)
    row = logs.get_round(round_id)
    if not row:
        return JSONResponse({"message": "未找到该轮"}, status_code=404)
    return row


@app.get("/api/kb/heatmap")
async def heatmap():
    data = logs.heatmap()
    items = []
    for item in data.get("items") or []:
        row = dict(item)
        row["display_name"] = c20_display_name(str(row.get("feature_id") or ""))
        items.append(row)
    return {
        "items": items,
        "unclassified": data.get("unclassified", 0),
        "unclassified_legacy": data.get("unclassified_legacy", 0),
        "legacy_rows": data.get("legacy_rows", 0),
    }


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def _fail_type(health: dict, before_retrieve: bool = True) -> tuple[str, str] | None:
    miss = missing_keys()
    if miss:
        label = "、".join(miss)
        return "missing_key", f"缺 Key：未配置 {label}"
    if not health["qdrant_ready"] or (before_retrieve and not health["index_ready"]):
        return "index_not_ready", "索引未就绪"
    return None


# 旧 status → (业务结果, 执行状态, 文本完整性)；失败时业务结果为未知，不写成已回答
_LEGACY_STATUS_MAP: dict[str, tuple[str | None, str, str]] = {
    "success": ("answered", "completed", "complete"),
    "refuse": ("refused", "completed", "complete"),
    "empty": ("insufficient", "completed", "complete"),
    "interrupted": (None, "interrupted", "truncated"),
    "rewrite_fail": (None, "failed", "empty"),
    "gen_fail": (None, "failed", "empty"),
}

# STEP-Q09：首写失败后的自动补写间隔（秒），共 1 + len 次；耗尽即停，不无限重试
SAVE_RETRY_DELAYS: tuple[float, ...] = (0.5, 1.0)
# STEP-Q09：补写承载的进程内备份（按 exec_id）；主承载为 qa_rounds.pending_reply
_PENDING_REPLIES: dict[str, dict] = {}
# Q19 接入证据检查前，「通过交付」按旧 status 判断；只有这些结果的刷新版本可被采用、可赞踩
_DELIVERED_STATUS = {"success", "refuse", "empty"}


_AVOID_REPEAT_RE = re.compile(r"(不要|不|别|避免|勿)\s*重复")
RECOVERED_HEAD = "已恢复的此前对话原文（服务端按本对话有效范围读取；只用于理解指代与约束，不是知识证据）："


def _brief_with_history(brief: str, recovered: str) -> str:
    """STEP-Q16：追溯恢复的原文随任务说明交给改写（与 Generate 交接同源）。"""
    return f"{brief}\n{RECOVERED_HEAD}\n{recovered}" if recovered else brief


def _generate_handoff(
    l1_turns: list[dict], requires_history: bool, ready_tasks: list[dict], settled: dict, rw: dict,
    time_base: str | None, recovered: str = "",
) -> tuple[dict, str | None]:
    """STEP-Q18：组装 Generate 需要实际收到的历史回答、核验目标与时间；返回 (handoff, 合同缺口说明)。
    历史只在相关时提供：需要历史、要求不重复、或核验旧回答。"""
    constraint_text = " ".join(
        [str(rw.get("response_constraint") or ""), str(settled.get("response_constraint") or "")]
        + [c for t in ready_tasks for c in t.get("constraints") or []]
    )
    avoid_repeat = bool(_AVOID_REPEAT_RE.search(constraint_text))
    verify = any(t.get("mode") == "核验" for t in ready_tasks)
    history: list[str] = []
    if requires_history or avoid_repeat or verify:
        history = [
            f"[回合{i}] User: {t.get('user') or ''}\nAssistant: {t.get('assistant') or ''}"
            for i, t in enumerate(l1_turns or [], 1)
        ]
    if recovered:
        # STEP-Q16：L1 之外恢复的原文带来源一并交接；与 L1 分开标注
        history = history + [f"{RECOVERED_HEAD}\n{recovered}"]
    target = (l1_turns[-1].get("assistant") or None) if (verify and l1_turns) else None
    gap = None
    if avoid_repeat and not history:
        gap = "此前回答原文（要求不重复）"
    elif verify and not target:
        gap = "被核验的此前回答原文"
    handoff = {
        "time_text": local_time_text(time_base),
        "history": history,
        "verification_target": target,
        "avoid_repeat": avoid_repeat,
        "verify": verify,
    }
    return handoff, gap


def _write_reply(conv_id: str, user_row: dict, exec_id: str, carrier: dict, runtime: dict | None = None) -> dict:
    """把同一份结果写成 Assistant 消息。本执行已写过则直接返回原行（补写可重复调用）。
    刷新写新版本（is_current=0），满足采用条件才切换为当前版本。
    会话已被实际删除时不再写回，避免晚到结果把原文写回来。"""
    convs = (runtime or {}).get('convs', globals()['convs'])
    msgs = (runtime or {}).get('msgs', globals()['msgs'])
    if convs.is_purged(conv_id):
        return {"id": None, "_purged": True, "_adopted": False, "content": ""}
    round_id = user_row["round_id"]
    existing = next(
        (r for r in msgs.round_rows(conv_id, round_id) if r["role"] == "assistant" and r.get("exec_id") == exec_id),
        None,
    )
    if existing is not None:
        row = dict(existing)
    elif carrier.get("op_type") == "refresh":
        row = msgs.append_assistant(
            conv_id, user_row, exec_id, carrier.get("content") or "", carrier.get("completeness") or "complete",
            "refresh", version_no=msgs.next_version_no(conv_id, round_id), is_current=0,
        )
    else:
        row = msgs.append_assistant(
            conv_id, user_row, exec_id, carrier.get("content") or "", carrier.get("completeness") or "complete", "send",
        )
    adopted = bool(row.get("is_current"))
    if carrier.get("adopt") and not adopted:
        try:
            msgs.adopt_version(conv_id, round_id, row["id"])
            adopted = True
        except Exception as exc:  # noqa: BLE001
            # 采用失败：新版本已保存但不替换原默认版本
            log.warning("adopt version failed: %s", exc)
    row["_adopted"] = adopted
    return row


def _refresh_l1(conv_id: str, user_row: dict) -> tuple[dict, dict]:
    """STEP-Q08：刷新按原问题首次执行的快照组装 L1，不读原问题之后的对话。"""
    src_exec = str(user_row.get("exec_id") or "")
    snap = ((logs.get_round(src_exec) if src_exec else None) or {}).get("snapshot") or {}
    pairs = snap.get("l1_msg_ids")
    extra: dict = {"snapshot_source": src_exec or None}
    if isinstance(pairs, list):
        ids = [i for p in pairs if isinstance(p, (list, tuple)) for i in p]
        l1 = assemble_from_ids(msgs.get_by_ids(conv_id, ids), pairs)
        if l1["missing"]:
            extra["snapshot_limited"] = "missing_messages"
            extra["l1_missing"] = l1["missing"]
        return l1, extra
    # 旧快照（Q08 前）没有消息 id：退化为原问题之前的当前版本，并标明限制
    before = [m for m in msgs.effective_messages(conv_id) if int(m["round_seq"]) < int(user_row["round_seq"])]
    extra["snapshot_limited"] = "legacy_snapshot"
    return assemble_l1(before), extra


# STEP-Q10：已接受的执行在服务端后台跑完，SSE 只是订阅；持有引用防止任务被回收
_EXEC_TASKS: set = set()
# 本进程内仍在运行的执行（状态接口据此区分「运行中」与「服务重启后遗留」）
_LIVE_EXECS: set = set()
EXEC_TIMEOUT_MESSAGE = "处理超时，本轮未完成。可重试。"


def _close_timed_out(run: dict) -> dict | None:
    """执行超过总截止仍未收尾：如实写执行失败与超时说明；之后晚到的结果不再改写终态。"""
    conv_id, exec_id = run.get("conv_id"), run.get("exec_id")
    if not conv_id or not exec_id:
        return None
    user_row = run.get("user_row")
    msg_id = None
    msg_save = "not_applicable"
    if user_row is not None:
        try:
            row = _write_reply(conv_id, user_row, exec_id, {
                "conv_id": conv_id, "logical_round_id": user_row["round_id"], "user_msg_id": user_row["id"],
                "content": EXEC_TIMEOUT_MESSAGE, "completeness": "error_notice",
                "op_type": run.get("op_type") or "send", "adopt": False,
            })
            msg_id, msg_save = row["id"], "saved"
        except Exception as exc:  # noqa: BLE001
            log.warning("timeout notice save failed: %s", exc)
            msg_save = "failed"
    if run.get("log_ok"):
        logs.update_round(exec_id, {
            "status": "gen_fail", "exec_state": "failed", "error_type": "exec_timeout",
            "text_integrity": "empty", "msg_save": msg_save, "runtime_save": "saved",
            "assistant_msg_id": msg_id,
            "finished_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
        })
    process = run.get("process")
    if process:
        process.finish("failed", "处理超时，本轮未完成")
        if run.get("log_ok"):
            logs.update_round(exec_id, {"answer_process": process.snapshot()})
    diag.record("model_error", "exec_timeout", conv_id=conv_id, exec_id=exec_id)
    return {"type": "exec_timeout", "message": EXEC_TIMEOUT_MESSAGE, "round_id": exec_id, "exec_id": exec_id,
            "assistant_msg_id": msg_id, "msg_save": msg_save,
            "process": process.snapshot() if process else None}


async def _ask_events(request: Request, body: dict) -> AsyncIterator[bytes]:
    run: dict = {}
    queue: asyncio.Queue = asyncio.Queue()

    async def consume() -> None:
        async for chunk in _ask_flow(request, body, run):
            queue.put_nowait(chunk)

    async def worker() -> None:
        exec_id = str(body.get("round_id") or "")
        try:
            try:
                # 总截止：超时后取消仍在进行的调用，晚到结果不改写终态（AT-40）
                await asyncio.wait_for(consume(), timeout=RUN_LEASE_SEC)
            except asyncio.TimeoutError:
                if not run.get("finished"):
                    payload = _close_timed_out(run)
                    if payload:
                        queue.put_nowait(_sse("error", payload).encode("utf-8"))
            except Exception as exc:  # noqa: BLE001
                log.exception("ask flow crashed: %s", exc)
        finally:
            # 执行结束（含超时）按本执行条件释放，不会放掉别人的执行权
            if run.get("conv_id"):
                convs.release_run(run["conv_id"], run["exec_id"])
            _LIVE_EXECS.discard(exec_id)
            queue.put_nowait(None)

    exec_id = str(body.get("round_id") or "")
    if not exec_id:
        body = dict(body, round_id=uid("r"))
        exec_id = body["round_id"]
    _LIVE_EXECS.add(exec_id)
    task = asyncio.create_task(worker())
    _EXEC_TASKS.add(task)
    task.add_done_callback(_EXEC_TASKS.discard)
    # 客户端断开只结束这个订阅，不取消后台执行（RQ-09）
    while True:
        chunk = await queue.get()
        if chunk is None:
            break
        yield chunk


async def _ask_flow(request: Request, body: dict, run: dict, runtime: dict | None = None) -> AsyncIterator[bytes]:
    # 同版编排器可注入独立测试载体；每次调用有独立依赖，不切换任何生产全局对象。
    deps = runtime or {}
    convs = deps.get('convs', globals()['convs'])
    msgs = deps.get('msgs', globals()['msgs'])
    logs = deps.get('logs', globals()['logs'])
    models = deps.get('models', globals()['models'])
    router = deps.get('router', globals()['router'])
    task_preparer = deps.get('task_preparer', globals()['task_preparer'])
    evidence_checker = deps.get('evidence_checker', globals()['evidence_checker'])
    recall_workflow = deps.get('recall_workflow', globals()['recall_workflow'])
    pipeline = deps.get('pipeline', globals()['pipeline'])
    diag = deps.get('diag', globals()['diag'])
    _memory_tool = deps.get('memory_tool', globals()['_memory_tool'])
    _PENDING_REPLIES = deps.get('pending_replies', globals()['_PENDING_REPLIES'])
    # STEP-Q19（G-E02）：执行总截止从接受时起算，沿用执行权租期时长；续租不延长它
    deadline = time.monotonic() + RUN_LEASE_SEC
    conv_id = str(body.get("conversation_id") or uid("c"))
    round_id = str(body.get("round_id") or uid("r"))
    original = str(body.get("query") or "").strip()
    accepted = deps.get('config') or config_store.accept_config()
    cfg = {k: accepted.get(k) for k in ("recall_k", "rerank_n", "history_turns", "temperature", "system_prompt", "rewrite_prompt")}
    cfg["prompts"] = accepted.get("prompts") or {}
    cfg["pools"] = accepted.get("pools")
    cfg["history_recovery"] = accepted.get("history_recovery", True)
    models_snap = {
        "rewrite": settings.LLM_MODEL,
        "embedding": settings.EMBED_MODEL,
        "rerank": settings.RERANK_MODEL,
        "generate": settings.LLM_MODEL,
    }
    account = getattr(request.state, "account", None)
    session_uid = (account or {}).get("id")
    # STEP-Q01：刷新不伪造 User；逻辑回合与版本由 Q08 接入，此前刷新不写消息表
    op_type = "refresh" if str(body.get("op_type") or "") == "refresh" else "send"
    client_request_id = str(body.get("client_request_id") or "").strip()[:64] or None
    # STEP-Q08：刷新指向的逻辑回合；未带时按旧客户端刷新处理（不写消息、不出新版本）
    target_round_id = (str(body.get("logical_round_id") or "").strip()[:64] or None) if op_type == "refresh" else None
    log_ok = logs.insert_running({
        "round_id": round_id,
        "conv_id": conv_id,
        "original_query": original,
        "models": models_snap,
        "user_id": session_uid,
        "owner_id": body.get("owner_id"),
        "tenant_id": body.get("tenant_id"),
        "role": body.get("role"),
        # STEP-Q02：初始状态；runtime_save 先记 partial，最终更新成功才改 saved
        "schema_ver": RUNTIME_SCHEMA_VER,
        "op_type": op_type,
        "exec_state": "running",
        "check_status": "not_run",
        "msg_save": "pending",
        "runtime_save": "partial",
        "config_package_id": accepted.get("_package_id"),
    })
    run["log_ok"] = log_ok
    run["op_type"] = op_type
    process = AnswerProcess(round_id)
    run["process"] = process

    def emit(event: str, data: dict) -> str:
        changed = process.observe(event, data)
        if changed and log_ok and not convs.is_purged(conv_id):
            logs.update_round(round_id, {"answer_process": process.snapshot()})
        if event == "process":
            return _sse("process", {"exec_id": round_id, "process": process.snapshot()})
        if event in ("done", "error", "refuse"):
            data = dict(data, exec_id=round_id, process=process.snapshot())
        encoded = _sse(event, data)
        if changed and event not in ("done", "error", "refuse"):
            encoded += _sse("process", {"exec_id": round_id, "process": process.snapshot()})
        return encoded
    if not log_ok:
        diag.record("runtime_insert_fail", "insert_running", conv_id=conv_id, exec_id=round_id)
        yield emit("log", {"written": False, "message": "本轮日志未写入"}).encode("utf-8")

    user_row: dict | None = None
    reply_info: dict = {
        "assistant_msg_id": None,
        "msg_save": "not_applicable",
        "version_no": None,
        "adopted": None,
        "save_blocked": False,
    }
    exec_info: dict = {
        "used_knowledge_rag": False,
        "error_type": None,
        "statuses": {k: None for k in STATUS_KEYS},
    }
    # STEP-Q17：本执行的模型调用计数，后端维护；needs_context、修正等任何分支都不归零
    call_usage: dict = {k: 0 for k in (
        "router", "task_prep", "rewrite", "smalltalk", "clarify", "generate", "check", "repair", "recall", "memory",
    )}
    # STEP-Q16：本执行共享的追溯预算（次数、步数、并行、历史 tokens、截止前预留），只建一次
    # 停用历史恢复或预算空白时，这一轮不查找更早对话；当前 L1 仍按原样组装
    recall_budget = budget_for(accepted, deadline)
    if accepted.get("history_recovery") is False:
        cfg["history_note"] = "历史恢复已停用，本轮只使用当前有效上下文，不查找更早对话"

    def renew() -> None:
        if run.get("conv_id"):
            convs.renew_run(conv_id, round_id)

    def release() -> None:
        if run.get("conv_id"):
            convs.release_run(conv_id, round_id)
            run.clear()

    async def save_reply(text: str, completeness: str, delivered: bool) -> None:
        """实际展示给用户的 Assistant 内容一律落库，不按结果类型筛选。
        STEP-Q09：首写失败先存承载，再同文补写；全部失败则该会话进入保存阻塞。"""
        if user_row is None:
            return
        carrier = {
            "conv_id": conv_id,
            "logical_round_id": user_row["round_id"],
            "user_msg_id": user_row["id"],
            "content": text,
            "completeness": completeness,
            "op_type": op_type,
            "adopt": bool(op_type == "refresh" and delivered and completeness == "complete"),
        }
        for attempt, delay in enumerate((0.0, *SAVE_RETRY_DELAYS)):
            if delay:
                await asyncio.sleep(delay)
            try:
                row = _write_reply(conv_id, user_row, round_id, carrier, runtime)
            except Exception as exc:  # noqa: BLE001
                log.warning("assistant message save failed (attempt %s): %s", attempt + 1, exc)
                if attempt == 0:
                    diag.record("assistant_save_fail", "first_write", conv_id=conv_id, exec_id=round_id)
                    _PENDING_REPLIES[round_id] = carrier
                    if log_ok:
                        logs.update_round(round_id, {"pending_reply": carrier})
                continue
            reply_info.update({
                "assistant_msg_id": row["id"],
                "msg_save": "saved",
                "version_no": row.get("version_no"),
                "adopted": row.get("_adopted"),
            })
            if attempt:
                _PENDING_REPLIES.pop(round_id, None)
                if log_ok:
                    logs.update_round(round_id, {"pending_reply": None})
            return
        reply_info["msg_save"] = "failed"
        reply_info["save_blocked"] = True
        convs.set_save_block(conv_id, round_id)
        diag.record("assistant_save_blocked", "retries_exhausted", conv_id=conv_id, exec_id=round_id)

    async def finish(
        status: str,
        extra: dict | None = None,
        reply: str | None = None,
        completeness: str = "complete",
        error_type: str | None = None,
        biz_result: str | None = None,
        check_status: str = "not_run",
        delivered: bool | None = None,
    ) -> None:
        # STEP-Q19：未通过交付检查的结果不能替换原有效版本（delivered=False 覆盖旧 status 判断）
        if convs.is_purged(conv_id):
            return
        if reply is not None:
            await save_reply(reply, completeness, status in _DELIVERED_STATUS if delivered is None else delivered)
        biz, state, integrity = _LEGACY_STATUS_MAP.get(status, (None, "failed", "empty"))
        if status == "interrupted" and not (reply or "").strip():
            integrity = "empty"
        # STEP-Q12：非知识分支按实际分支填业务结果；旧 status 仍按原映射兼容
        if biz_result is not None:
            biz = biz_result
        statuses = {
            "biz_result": biz,
            "exec_state": state,
            # STEP-Q19：知识回答按检查实际结果；其余分支如实记未运行
            "check_status": check_status,
            "text_integrity": integrity,
            "msg_save": reply_info["msg_save"],
            "runtime_save": "failed",
        }
        summary = {
            "partial": "已完成本轮处理，部分问题仍缺少依据或条件",
            "conflict": "已完成核对，参考资料存在冲突",
            "clarify": "需要补充信息", "insufficient": "本次未取得充分依据",
            "missing_context": "缺少必要上下文", "refused": "已返回范围说明",
        }.get(biz, "已完成" if state == "completed" else "本轮未完成")
        process.finish(state, summary)
        exec_info["error_type"] = error_type
        payload = {"status": status, "models": models_snap}
        if extra:
            payload.update(extra)
        payload.update({k: v for k, v in statuses.items() if k != "runtime_save"})
        payload.update({
            "runtime_save": "saved",
            "error_type": error_type,
            "used_knowledge_rag": exec_info["used_knowledge_rag"],
            "assistant_msg_id": reply_info["assistant_msg_id"],
            "call_usage": dict(call_usage),
            "answer_process": process.snapshot(),
            # STEP-A15：终态时间与终态同句写入，供执行耗时统计
            "finished_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
        })
        if log_ok:
            # 这句失败时库里仍是 insert 时的 partial，上报也如实给 partial
            statuses["runtime_save"] = "saved" if logs.update_round(round_id, payload) else "partial"
            if statuses["runtime_save"] == "partial":
                diag.record("runtime_update_fail", "final_update", conv_id=conv_id, exec_id=round_id)
        exec_info["statuses"] = statuses
        # 终态已落定才放执行权：保存阻塞已先写入，另一设备不会趁隙抢发
        release()
        # STEP-Q10：已收尾，超时兜底不再改写终态
        run["finished"] = True

    def ids() -> dict:
        return {
            "logical_round_id": (user_row or {}).get("round_id"),
            "exec_id": round_id,
            "op_type": op_type,
            "user_msg_id": (user_row or {}).get("id"),
            "assistant_msg_id": reply_info["assistant_msg_id"],
            "msg_save": reply_info["msg_save"],
            "version_no": reply_info["version_no"],
            "adopted": reply_info["adopted"],
            "save_blocked": reply_info["save_blocked"],
            "statuses": dict(exec_info["statuses"]),
            "error_type": exec_info["error_type"],
        }

    if original or target_round_id:
        err: tuple[str, str] | None = None
        dup: dict | None = None
        err_extra: dict = {}
        refresh_user: dict | None = None
        try:
            owned = convs.get_owned(str(session_uid or ""), conv_id)
        except Exception as exc:  # noqa: BLE001
            log.warning("conversation lookup failed: %s", exc)
            owned = None
            err = ("user_save_fail", "提问未保存，本轮未开始。请重试。")
        if owned is None and err is None:
            err = ("conversation_not_found", "未找到该会话")
        # STEP-Q08：刷新定位原问题；清空边界之前的回合不可刷新
        if err is None and target_round_id:
            try:
                rows = msgs.visible_round(conv_id, target_round_id)
                refresh_user = next((r for r in rows if r["role"] == "user"), None)
                if refresh_user is None:
                    err = ("round_not_found", "未找到要刷新的问题")
            except Exception as exc:  # noqa: BLE001
                log.warning("refresh round lookup failed: %s", exc)
                err = ("refresh_fail", "刷新未开始，请重试。")
        # STEP-Q07：已被接受过的同一请求不再执行（查重在抢占之前，重传不会被误判为忙碌）
        if err is None and client_request_id:
            try:
                if op_type == "send":
                    prior = msgs.find_request(conv_id, client_request_id)
                    if prior:
                        dup = prior
                elif target_round_id:
                    prior = logs.find_by_request(conv_id, client_request_id)
                    if prior:
                        dup = {
                            "round_id": prior.get("logical_round_id"),
                            "id": prior.get("user_msg_id"),
                            "exec_id": prior.get("round_id"),
                        }
            except Exception as exc:  # noqa: BLE001
                # 查不到时不阻断：普通发送另有唯一约束兜底，刷新靠会话互斥兜底
                log.warning("request dedupe lookup failed: %s", exc)
            if dup:
                err = ("duplicate_request", "这条提问已提交过，不会重复处理。")
        # STEP-Q07：同会话执行权，普通发送与刷新共用
        if err is None:
            try:
                state, other = convs.acquire_run(conv_id, round_id)
            except Exception as exc:  # noqa: BLE001
                log.warning("acquire run failed: %s", exc)
                state, other = "error", None
                err = ("user_save_fail", "提问未保存，本轮未开始。请重试。")
            if state == "ok":
                run.update({"conv_id": conv_id, "exec_id": round_id})
            elif state == "busy":
                err = ("conversation_busy", "该会话正在处理中，请稍后再发。")
                err_extra = {"running_exec_id": other}
            elif state == "blocked":
                err = ("save_blocked", "上一条回答未保存，请先重试保存。")
                err_extra = {"blocked_exec_id": other}
        if err is None and refresh_user is not None:
            user_row = refresh_user
            original = str(refresh_user.get("content") or "")
            if log_ok and client_request_id:
                logs.update_round(round_id, {"client_request_id": client_request_id})
        if err is None and op_type == "send":
            try:
                user_row = msgs.append_user(conv_id, original, client_request_id, round_id, op_type)
            except DuplicateRequest as exc:
                dup = exc.existing
                err = ("duplicate_request", "这条提问已提交过，不会重复处理。")
            except Exception as exc:  # noqa: BLE001
                log.warning("user message save failed: %s", exc)
                diag.record("user_save_fail", "append_user", conv_id=conv_id, exec_id=round_id)
                err = ("user_save_fail", "提问未保存，本轮未开始。请重试。")
        if err:
            code, message = err
            if code == "user_save_fail" and op_type == "send":
                reply_info["msg_save"] = "failed"
            await finish("gen_fail", error_type=code)
            payload = {
                "type": code, "message": message, "round_id": round_id, "log_written": log_ok,
                **ids(), **err_extra,
            }
            if dup:
                payload["existing"] = {
                    "logical_round_id": dup.get("round_id"),
                    "user_msg_id": dup.get("id"),
                    "exec_id": dup.get("exec_id"),
                }
            yield emit("error", payload).encode("utf-8")
            return
        if user_row is not None:
            run["user_row"] = user_row
            if log_ok:
                logs.update_round(round_id, {
                    "logical_round_id": user_row["round_id"],
                    "user_msg_id": user_row["id"],
                })
            yield emit("accepted", {
                "conversation_id": conv_id,
                "logical_round_id": user_row["round_id"],
                "exec_id": round_id,
                "op_type": op_type,
                "user_msg_id": user_row["id"],
                "seq": int(user_row["seq"]),
            }).encode("utf-8")

    # STEP-Q05：L1 只从服务端消息事实源组装；请求体 history / last_chunks 不再采信
    # STEP-Q08：带逻辑回合的刷新改按原问题快照组装
    history: list[dict] = []
    prev_blocks: list[dict] = []
    l1_turns: list[dict] = []
    time_base: str | None = None
    if original:
        snap_extra: dict = {}
        try:
            if target_round_id and user_row is not None:
                l1, snap_extra = _refresh_l1(conv_id, user_row)
            else:
                l1 = assemble_l1(
                    msgs.effective_messages(conv_id),
                    exclude_round_id=(user_row or {}).get("round_id"),
                )
        except Exception as exc:  # noqa: BLE001
            log.warning("assemble L1 failed: %s", exc)
            l1 = None
        if l1 is not None:
            history = as_history(l1)
            l1_turns = list(l1["turns"])
            snap = snapshot_meta(l1)
            if snap["prev_exec_id"]:
                prev_blocks = (logs.get_round(snap["prev_exec_id"]) or {}).get("c_gen") or []
        else:
            snap = {"l1_round_ids": [], "l1_tokens": 0, "l1_reason": "read_fail"}
        snap.update(snap_extra)
        if user_row is not None:
            # 时间基准固定为原问题的提问时间；刷新沿用，不改成刷新当天
            snap["cut_seq"] = int(user_row["seq"])
            snap["time_base"] = deps.get('time_base') or str(user_row.get("created_at") or "")
            time_base = snap["time_base"] or None
        if log_ok:
            logs.update_round(round_id, {"snapshot": snap})

    if not original:
        await finish("gen_fail", error_type="rewrite_fail")
        yield emit("error", {"type": "rewrite_fail", "message": "问句为空", "round_id": round_id}).encode("utf-8")
        return

    # STEP-Q11：Router v3 只分类；原始 route 只在这一步写入 Runtime，后续步骤不改写。
    # 非法输出或调用失败是分类执行异常，不当 unclear；不重试（E02 未定）。
    # G-E03：低置信度兜底未启用，confidence 只校验与记录，不影响分支。
    # STEP-Q13：跨轮承接只看清空边界之后、本问之前最近一个逻辑回合（澄清或部分完成），不受 L1 窗口限制；
    # 读失败按无承接处理
    carry: dict | None = None
    if user_row is not None:
        try:
            carry = find_carry(msgs.effective_messages(conv_id), int(user_row["seq"]), logs.get_round)
        except Exception as exc:  # noqa: BLE001
            log.warning("carry lookup failed: %s", exc)
            carry = None
    carry_prompt = carry_text(carry) if carry else None

    renew()
    yield emit("stage", {"stage": "route", "round_id": round_id}).encode("utf-8")
    call_usage["router"] += 1
    try:
        routed = await router.route(original, l1_turns, cfg, carry=carry_prompt)
    except RouterError as exc:
        if log_ok:
            logs.update_round(round_id, router_runtime(None, exc))
        await finish("gen_fail", reply=exc.message, completeness="error_notice", error_type=exc.code)
        yield emit("error", {
            "type": exc.code,
            "message": exc.message,
            "round_id": round_id,
            "log_written": log_ok,
            **ids(),
        }).encode("utf-8")
        return
    if log_ok:
        logs.update_round(round_id, router_runtime(routed))
    route = routed["route"]
    yield emit("process", dict(routed, kind="route")).encode("utf-8")

    # STEP-Q12：非知识分支只依赖自身用到的模型/配置，不调用 Memory / Knowledge，知识索引故障不挡（CSTR-Q06）
    if route in NON_KNOWLEDGE_ROUTES:
        renew()
        try:
            if route == "ack":
                text = pick_reply(enabled_texts(accepted, "ack"))
            elif route == "out_of_scope":
                text = pick_reply(enabled_texts(accepted, "scope"))
            elif route == "smalltalk":
                yield emit("stage", {"stage": "smalltalk", "round_id": round_id}).encode("utf-8")
                call_usage["smalltalk"] += 1
                text = await smalltalk_reply(models, original, l1_turns, cfg)
            else:
                yield emit("stage", {"stage": "clarify", "round_id": round_id}).encode("utf-8")
                call_usage["clarify"] += 1
                text = await clarify(models, original, l1_turns, cfg, "router_unclear", time_base)
        except BranchError as exc:
            if route in ("smalltalk", "unclear"):
                diag.record("model_error", f"{route}:{exc.code}", conv_id=conv_id, exec_id=round_id)
            await finish("gen_fail", reply=exc.message, completeness="error_notice", error_type=exc.code)
            yield emit("error", {
                "type": exc.code,
                "message": exc.message,
                "round_id": round_id,
                "log_written": log_ok,
                **ids(),
            }).encode("utf-8")
            return
        await finish(
            "success", {"answer": text, "c_gen": []}, reply=text, biz_result=ROUTE_BIZ_RESULT[route],
        )
        yield emit("done", {
            "status": "success",
            "round_id": round_id,
            "text": text,
            "refused": False,
            "c_gen": [],
            "log_written": log_ok,
            **ids(),
        }).encode("utf-8")
        return

    # STEP-Q13：knowledge_query / conversation_task 先做最小任务准备；失败为执行异常，不降级为单任务、不重试
    renew()
    yield emit("stage", {"stage": "task_prep", "round_id": round_id}).encode("utf-8")
    call_usage["task_prep"] += 1
    try:
        prep = await task_preparer.prepare(
            original, l1_turns, route, bool(routed.get("requires_history")), cfg, carry_prompt,
        )
    except TaskPrepError as exc:
        if log_ok:
            logs.update_round(round_id, {"task_prep": prep_record(None, carry, exc)})
        diag.record("model_error", f"task_prep:{exc.code}", conv_id=conv_id, exec_id=round_id)
        await finish("gen_fail", reply=exc.message, completeness="error_notice", error_type=exc.code)
        yield emit("error", {
            "type": exc.code,
            "message": exc.message,
            "round_id": round_id,
            "log_written": log_ok,
            **ids(),
        }).encode("utf-8")
        return
    settled = settle(prep)
    yield emit("process", dict(settled, kind="tasks")).encode("utf-8")
    if log_ok:
        logs.update_round(round_id, {"task_prep": prep_record(settled, carry)})

    # STEP-Q16：只有任务准备判定缺较早历史（L1 与承接都没有）才进入追溯；L1 足够时不调用 Memory（C02）。
    # 预算未配置时不启用，保持「暂不支持查找」说明。结果只落回任务，不改写已写入的 task_prep。
    scope = None
    recovered_text = ""
    recall_result: dict | None = None
    if user_row is not None:
        scope = MemoryScope(str(session_uid or ""), conv_id, int(user_row["seq"]), user_row["round_id"], time_base)

    def count_call(kind: str) -> None:
        call_usage[kind] = call_usage.get(kind, 0) + 1

    async def run_recall(gaps: list[dict], seed: list[dict] | None = None) -> dict:
        result = await recall_workflow.run(
            original, l1_turns, gaps, _memory_tool(), scope, recall_budget, on_call=count_call, seed=seed, cfg=cfg,
        )
        process.observe("process", dict(result, kind="recall"))
        if log_ok:
            logs.update_round(round_id, {"recall": recall_record(result)})
        if result["stop_reason"] in ("tool_error", "invalid_action"):
            diag.record("model_error", f"recall:{result.get('invalid') or result.get('error') or 'error'}",
                        conv_id=conv_id, exec_id=round_id)
        return result

    hist_gaps = recall_gaps(settled)
    if hist_gaps and scope is not None and recall_budget.enabled:
        renew()
        yield emit("stage", {"stage": "recall", "round_id": round_id}).encode("utf-8")
        recall_result = await run_recall(hist_gaps)
        settled = apply_recall(prep, hist_gaps, recall_result, settle)
        recovered_text = recall_result["recovered_text"]

    # 没有可执行任务：澄清 / 如实说明未完成 / 越界话术；都不检索，也不检查知识索引
    if settled["outcome"] != "run":
        renew()
        try:
            if settled["outcome"] == "clarify":
                yield emit("stage", {"stage": "clarify", "round_id": round_id}).encode("utf-8")
                first = next(t for t in settled["tasks"] if t["check"] in ("needs_user_input", "ambiguous"))
                call_usage["clarify"] += 1
                text = await clarify(
                    models, original, l1_turns, cfg, f"task_{first['check']}", time_base,
                    pending=pending_text(settled),
                    recovered="\n\n".join(x for x in (carry_prompt, recovered_text) if x) or None,
                )
                biz = "clarify"
            elif settled["outcome"] == "unfinished":
                text, biz = unfinished_text(settled), "insufficient"
            else:
                text, biz = pick_reply(enabled_texts(accepted, "scope")), "refused"
        except BranchError as exc:
            if settled["outcome"] == "clarify":
                diag.record("model_error", f"task_clarify:{exc.code}", conv_id=conv_id, exec_id=round_id)
            await finish("gen_fail", reply=exc.message, completeness="error_notice", error_type=exc.code)
            yield emit("error", {
                "type": exc.code,
                "message": exc.message,
                "round_id": round_id,
                "log_written": log_ok,
                **ids(),
            }).encode("utf-8")
            return
        await finish("success", {"answer": text, "c_gen": []}, reply=text, biz_result=biz)
        yield emit("done", {
            "status": "success",
            "round_id": round_id,
            "text": text,
            "refused": False,
            "c_gen": [],
            "log_written": log_ok,
            **ids(),
        }).encode("utf-8")
        return
    # 就绪任务合并跑一次现有知识链路；任务说明经本请求的 cfg 交给 Rewrite / Generate
    ready_tasks = [t for t in settled["tasks"] if t["check"] == "ready"]
    cfg = dict(cfg, _task_brief=_brief_with_history(task_brief(settled), recovered_text),
               _task_ids=[t["task_id"] for t in ready_tasks])
    partial_tasks = settled["partial"]

    # STEP-Q20：conversation_task 且就绪任务全是回看/重述 → 返回已保存原文或只做表达变换，不调用 Knowledge RAG、
    # 不检查知识索引；找回旧版本只读、不改默认版本。夹杂查询/核验的仍走下面的知识链路。
    if is_conversation_only(route, ready_tasks) and scope is not None:
        renew()
        yield emit("stage", {"stage": "conversation", "round_id": round_id}).encode("utf-8")
        tool = _memory_tool()
        target_ids = [r for rids in ((recall_result or {}).get("resolved") or {}).values() for r in rids]
        l1_ids = [t["round_id"] for t in l1_turns]
        modes = {t["mode"] for t in ready_tasks}
        text, refs, biz = None, [], "answered"
        why = NO_TARGET
        try:
            if modes == {"重述"}:
                if not target_ids and len(l1_ids) == 1:
                    # 只有一轮时无需再判断，直接重述那一轮
                    target_ids = list(l1_ids)
                elif not target_ids and len(l1_ids) > 1 and recall_budget.enabled:
                    # 多于一轮时不猜最后一轮：只让工作流从 L1 回合中指认，不调 Memory
                    seed = tool.round_views(scope, l1_ids)
                    picked = await run_recall([
                        {"gap_id": f"V{i}", "task_ids": [t["task_id"]], "goal": t["goal"], "clue": t["goal"],
                         "depends_on": []}
                        for i, t in enumerate(ready_tasks, 1)
                    ], seed=seed)
                    if picked["stop_reason"] == "ready":
                        target_ids = [r for rids in picked["resolved"].values() for r in rids]
                    elif picked["stop_reason"] == "needs_clarification":
                        yield emit("stage", {"stage": "clarify", "round_id": round_id}).encode("utf-8")
                        call_usage["clarify"] += 1
                        text = await clarify(
                            models, original, l1_turns, cfg, "history_ambiguous", time_base,
                            pending=f"- {picked.get('question') or '需要确认所指的此前内容'}；候选："
                                    + "、".join(picked.get("candidates") or []),
                        )
                        biz = "clarify"
                    else:
                        why = unresolved_reason(picked)
                if text is None:
                    views = tool.round_views(scope, target_ids)
                    answers = restate_source(views)
                    if answers:
                        call_usage["restate"] = call_usage.get("restate", 0) + 1
                        text = await conv_restate(models, original, answers, cfg)
                        refs = restate_refs(conv_id, views)
            else:
                if not target_ids and wants_version(original):
                    target_ids = l1_ids[-1:]
                elif not target_ids and l1_ids and recall_budget.enabled:
                    # 回看的目标在 L1 里：只让工作流从 L1 回合中指认，不调 Memory（除非它确实需要再找）
                    seed = tool.round_views(scope, l1_ids)
                    picked = await run_recall([
                        {"gap_id": f"V{i}", "task_ids": [t["task_id"]], "goal": t["goal"], "clue": t["goal"],
                         "depends_on": []}
                        for i, t in enumerate(ready_tasks, 1)
                    ], seed=seed)
                    if picked["stop_reason"] == "ready":
                        target_ids = [r for rids in picked["resolved"].values() for r in rids]
                    elif picked["stop_reason"] == "needs_clarification":
                        yield emit("stage", {"stage": "clarify", "round_id": round_id}).encode("utf-8")
                        call_usage["clarify"] += 1
                        text = await clarify(
                            models, original, l1_turns, cfg, "history_ambiguous", time_base,
                            pending=f"- {picked.get('question') or '需要确认所指的此前内容'}；候选："
                                    + "、".join(picked.get("candidates") or []),
                        )
                        biz = "clarify"
                    else:
                        why = unresolved_reason(picked)
                if text is None:
                    views = tool.round_views(scope, target_ids)
                    if views and wants_version(original):
                        versions = tool.versions(scope, views[-1]["round_id"])
                        chosen = pick_versions(original, versions)
                        if chosen:
                            text, refs = replay_versions(conv_id, views[-1], chosen, versions)
                        else:
                            why = "没有找到所说的那个回答版本"
                    elif views:
                        text, refs = replay(conv_id, views)
        except (RestateError, BranchError) as exc:
            code = exc.code
            message = RESTATE_FAIL_MESSAGE if isinstance(exc, RestateError) else exc.message
            diag.record("model_error", f"conversation:{code}", conv_id=conv_id, exec_id=round_id)
            await finish("gen_fail", reply=message, completeness="error_notice", error_type=code)
            yield emit("error", {
                "type": code, "message": message, "round_id": round_id, "log_written": log_ok, **ids(),
            }).encode("utf-8")
            return
        if text is None:
            text, biz = f"本轮未能完成：{why}。", "insufficient"
        else:
            rest = [f"- {t['goal']}：{t['reason']}" for t in settled["tasks"] if t["check"] != "ready"]
            rest += [f"- {e['text']}：{e['reason']}" for e in settled["excluded"]]
            if rest and biz == "answered":
                text += "\n\n以下未完成：\n" + "\n".join(rest)
                biz = "partial"
        if log_ok:
            logs.update_round(round_id, {"history_refs": refs})
        await finish("success", {"answer": text, "c_gen": []}, reply=text, biz_result=biz)
        yield emit("done", {
            "status": "success",
            "round_id": round_id,
            "text": text,
            "refused": False,
            "c_gen": [],
            "history_refs": refs,
            "log_written": log_ok,
            **ids(),
        }).encode("utf-8")
        return

    # 知识分支才检查 Key 与知识索引；非知识分支与 conversation_task 的回看/重述不 ping Qdrant
    health = deps.get('health', _health)()
    fail = deps.get('fail_type', _fail_type)(health)
    if fail:
        code, message = fail
        await finish("gen_fail", reply=message, completeness="error_notice", error_type=code)
        yield emit("error", {
            "type": code,
            "message": message,
            "round_id": round_id,
            "log_written": log_ok,
            **ids(),
        }).encode("utf-8")
        return

    renew()
    yield emit("stage", {"stage": "rewrite", "round_id": round_id}).encode("utf-8")
    call_usage["rewrite"] += 1
    try:
        rw = await pipeline.rewrite(original, history, cfg)
    except RewriteInvalid as exc:
        # STEP-Q17：输出不合 Schema 按改写失败处理，只记截断原文，不猜 Query
        if log_ok:
            logs.update_round(round_id, {"rewrite": {
                "valid": False, "detail": exc.detail, "raw": excerpt(exc.raw), "prompt_ver": REWRITE_V3_VER,
            }})
        diag.record("model_error", "rewrite:invalid", conv_id=conv_id, exec_id=round_id)
        message = "改写失败，本轮未检索、未生成。可重试。"
        await finish("rewrite_fail", reply=message, completeness="error_notice", error_type="rewrite_fail")
        yield emit("error", {
            "type": "rewrite_fail",
            "message": message,
            "round_id": round_id,
            "log_written": log_ok,
            **ids(),
        }).encode("utf-8")
        return
    except ModelError as exc:
        kind = "missing_key" if exc.code == "missing_key" else "rewrite_fail"
        diag.record("model_error", f"rewrite:{exc.code}", conv_id=conv_id, exec_id=round_id)
        message = exc.message if kind == "missing_key" else "改写失败，本轮未检索、未生成。可重试。"
        await finish("rewrite_fail", reply=message, completeness="error_notice", error_type=kind)
        yield emit("error", {
            "type": kind,
            "message": message,
            "round_id": round_id,
            "log_written": log_ok,
            **ids(),
        }).encode("utf-8")
        return
    except Exception as exc:  # noqa: BLE001
        log.exception("rewrite failed: %s", exc)
        diag.record("model_error", "rewrite:exception", conv_id=conv_id, exec_id=round_id)
        message = "改写失败，本轮未检索、未生成。可重试。"
        await finish("rewrite_fail", reply=message, completeness="error_notice", error_type="rewrite_fail")
        yield emit("error", {
            "type": "rewrite_fail",
            "message": message,
            "round_id": round_id,
            "log_written": log_ok,
            **ids(),
        }).encode("utf-8")
        return

    rw_status = rw.get("status") or "ready"
    if log_ok:
        fields = {
            "rewrite_query": rw["rewrite_query"],
            "same_topic": 1 if rw["same_topic"] else 0,
            "named_feature_ids": rw["named_feature_ids"],
        }
        if "status" in rw:
            fields["rewrite"] = {
                "valid": True,
                "status": rw_status,
                "response_constraint": rw.get("response_constraint") or "",
                "missing_context": rw.get("missing_context") or [],
                "confidence": rw.get("confidence"),
                "extra_keys": rw.get("extra_keys") or [],
                "prompt_ver": rw.get("prompt_ver"),
            }
        logs.update_round(round_id, fields)
    yield emit("rewrite", rw).encode("utf-8")

    # STEP-Q16（AT-03）：改写只缺历史对象时，在同一执行、同一预算内进入恢复；找齐后按恢复原文再改写一次
    # （这次往返计入共享步数，不重跑 Router、不新建执行）。缺用户条件仍直接澄清。
    missing0 = rw.get("missing_context") or [] if rw_status == "needs_context" else []
    if (missing0 and scope is not None and recall_budget.enabled
            and all(m["type"] == "history_object" for m in missing0)):
        goals0 = {t["task_id"]: t["goal"] for t in settled["tasks"]}
        gaps0 = [
            {"gap_id": f"R{i}", "task_ids": [m["task_id"]], "goal": goals0.get(m["task_id"], original),
             "clue": m["clue"], "depends_on": []}
            for i, m in enumerate(missing0, 1)
        ]
        renew()
        yield emit("stage", {"stage": "recall", "round_id": round_id}).encode("utf-8")
        recall_result = await run_recall(gaps0)
        if (recall_result["stop_reason"] == "ready" and recall_result["recovered_text"]
                and recall_budget.take_step()):
            recovered_text = "\n\n".join(x for x in (recovered_text, recall_result["recovered_text"]) if x)
            cfg = dict(cfg, _task_brief=_brief_with_history(task_brief(settled), recovered_text))
            if log_ok:
                # 再改写这次往返已计入共享步数，Runtime 里的预算用量同步到最新
                logs.update_round(round_id, {"recall": dict(recall_record(recall_result),
                                                            budget=recall_budget.snapshot())})
            renew()
            yield emit("stage", {"stage": "rewrite", "round_id": round_id}).encode("utf-8")
            call_usage["rewrite"] += 1
            try:
                rw2 = await pipeline.rewrite(original, history, cfg)
            except Exception as exc:  # noqa: BLE001
                # 再改写失败：保持原 needs_context 出口如实说明，不猜 Query
                log.warning("rewrite after recall failed: %s", exc)
                diag.record("model_error", "rewrite:after_recall", conv_id=conv_id, exec_id=round_id)
                rw2 = None
            if rw2 is not None:
                rw = rw2
                rw_status = rw.get("status") or "ready"
                if log_ok:
                    logs.update_round(round_id, {
                        "rewrite_query": rw["rewrite_query"],
                        "same_topic": 1 if rw["same_topic"] else 0,
                        "named_feature_ids": rw["named_feature_ids"],
                        "rewrite": {
                            "valid": True, "status": rw_status, "after_recall": True,
                            "response_constraint": rw.get("response_constraint") or "",
                            "missing_context": rw.get("missing_context") or [],
                            "confidence": rw.get("confidence"), "extra_keys": rw.get("extra_keys") or [],
                            "prompt_ver": rw.get("prompt_ver"),
                        },
                    })
                yield emit("rewrite", rw).encode("utf-8")

    # STEP-Q17：needs_context 本轮不检索、不重跑 Router；Q16 恢复后仍缺时在这里如实收口
    if rw_status == "needs_context":
        goals = {t["task_id"]: t["goal"] for t in settled["tasks"]}
        missing = rw.get("missing_context") or []
        renew()
        if any(m["type"] == "user_condition" for m in missing):
            yield emit("stage", {"stage": "clarify", "round_id": round_id}).encode("utf-8")
            pending = "\n".join(f"- {goals.get(m['task_id'], original)}：{m['clue']}" for m in missing)
            call_usage["clarify"] += 1
            try:
                text = await clarify(
                    models, original, l1_turns, cfg, "rewrite_needs_context", time_base,
                    pending=pending, recovered=carry_prompt,
                )
            except BranchError as exc:
                diag.record("model_error", f"task_clarify:{exc.code}", conv_id=conv_id, exec_id=round_id)
                await finish("gen_fail", reply=exc.message, completeness="error_notice", error_type=exc.code)
                yield emit("error", {
                    "type": exc.code,
                    "message": exc.message,
                    "round_id": round_id,
                    "log_written": log_ok,
                    **ids(),
                }).encode("utf-8")
                return
            biz = "clarify"
        else:
            if recall_result is None:
                why = HISTORY_UNSUPPORTED
            elif recall_result["stop_reason"] == "ready":
                why = "已查阅此前对话，但仍不足以确定所指内容"
            else:
                why = unresolved_reason(recall_result)
            lines = ["本轮未能完成："]
            for m in missing:
                lines.append(f"- {goals.get(m['task_id'], original)}：{why}（缺：{m['clue']}）")
            others = [t["goal"] for t in ready_tasks if t["task_id"] not in {m["task_id"] for m in missing}]
            if others:
                lines.append("同一轮的其他问题本轮也未执行，补充上述内容后可一并处理：" + "；".join(others))
            text, biz = "\n".join(lines), "missing_context"
        await finish("success", {"answer": text, "c_gen": []}, reply=text, biz_result=biz)
        yield emit("done", {
            "status": "success",
            "round_id": round_id,
            "text": text,
            "refused": False,
            "c_gen": [],
            "log_written": log_ok,
            **ids(),
        }).encode("utf-8")
        return

    # STEP-Q18：Generate 交接与合同校验。要求「不重复」或核验旧回答时必须带上对应历史原文，缺了不当正常通过
    handoff, contract_gap = _generate_handoff(
        l1_turns, bool(routed.get("requires_history")), ready_tasks, settled, rw, time_base, recovered_text,
    )
    if contract_gap:
        message = f"缺少{contract_gap}，无法按要求作答，本轮未检索、未生成。可重试。"
        await finish("gen_fail", reply=message, completeness="error_notice", error_type="generate_contract_fail")
        yield emit("error", {
            "type": "generate_contract_fail",
            "message": message,
            "round_id": round_id,
            "log_written": log_ok,
            **ids(),
        }).encode("utf-8")
        return
    cfg = dict(cfg, _handoff=handoff)

    renew()
    yield emit("stage", {"stage": "retrieve"}).encode("utf-8")
    exec_info["used_knowledge_rag"] = True
    try:
        retrieved = await pipeline.retrieve(original, rw["rewrite_query"], rw["named_feature_ids"], cfg)
    except ModelError as exc:
        kind = "missing_key" if exc.code == "missing_key" else (
            "index_not_ready" if "qdrant" in exc.message.lower() else "retrieve_fail"
        )
        if exc.status_code >= 500:
            kind = "retrieve_fail"
        diag.record("retrieve_error", kind, conv_id=conv_id, exec_id=round_id)
        message = "索引未就绪" if kind == "index_not_ready" else exc.message
        await finish(
            "gen_fail",
            {"named_feature_ids": rw["named_feature_ids"]},
            reply=message,
            completeness="error_notice",
            error_type=kind,
        )
        yield emit("error", {
            "type": kind,
            "message": message,
            "round_id": round_id,
            "candidates": [],
            "log_written": log_ok,
            **ids(),
        }).encode("utf-8")
        return
    except Exception as exc:  # noqa: BLE001
        log.exception("retrieve failed: %s", exc)
        ping_ok = store.ping()
        diag.record("retrieve_error", "retrieve_fail" if ping_ok else "index_not_ready", conv_id=conv_id, exec_id=round_id)
        message = "检索失败" if ping_ok else "索引未就绪"
        await finish(
            "gen_fail",
            reply=message,
            completeness="error_notice",
            error_type="retrieve_fail" if ping_ok else "index_not_ready",
        )
        yield emit("error", {
            "type": "retrieve_fail" if ping_ok else "index_not_ready",
            "message": message,
            "round_id": round_id,
            "candidates": [],
            **ids(),
        }).encode("utf-8")
        return

    paths = sorted({c.get("path") or "" for c in retrieved["candidates"] if c.get("path")})
    yield emit("retrieve", {
        "mode": retrieved["mode"],
        "lanes": retrieved["lanes"],
        "paths": paths,
        "count": len(retrieved["candidates"]),
    }).encode("utf-8")

    renew()
    yield emit("stage", {"stage": "rerank"}).encode("utf-8")
    try:
        c_gen = await pipeline.rerank(
            rw["rewrite_query"],
            retrieved["candidates"],
            rw["named_feature_ids"],
            prev_blocks if rw["same_topic"] else [],
            rw["same_topic"],
            cfg,
        )
    except ModelError as exc:
        diag.record("model_error", f"rerank:{exc.code}", conv_id=conv_id, exec_id=round_id)
        await finish("gen_fail", {
            "named_feature_ids": rw["named_feature_ids"],
            "lanes": retrieved["lanes"],
        }, reply=exc.message, completeness="error_notice", error_type="rerank_fail")
        yield emit("error", {
            "type": "rerank_fail",
            "message": exc.message,
            "round_id": round_id,
            "c_gen": [],
            **ids(),
        }).encode("utf-8")
        return

    pub = public_c_gen(c_gen)
    yield emit("rerank", {"c_gen": pub}).encode("utf-8")
    if log_ok:
        logs.update_round(round_id, {
            "lanes": retrieved["lanes"],
            "c_gen": pub,
            "named_feature_ids": rw["named_feature_ids"],
        })

    if not c_gen:
        msg = "文档未写。重排后 0 块，系统拒答。"
        await finish("empty", {"answer": msg, "c_gen": []}, reply=msg)
        yield emit("refuse", {"text": msg, "c_gen": [], "status": "empty"}).encode("utf-8")
        yield emit("done", {
            "status": "empty",
            "round_id": round_id,
            "log_written": log_ok,
            **ids(),
        }).encode("utf-8")
        return

    # STEP-Q18（AT-17）：点名多个功能而部分功能本轮无块 → 业务结果为部分有证据
    named_ids = rw["named_feature_ids"]
    present = {b.get("feature_id") for b in c_gen}
    knowledge_partial = len(named_ids) >= 2 and any(fid not in present for fid in named_ids)

    gen_fail_msg = "生成失败。半段正文已丢弃，不展示完整回答。"
    renew()
    yield emit("stage", {"stage": "generate"}).encode("utf-8")
    acc = []
    call_usage["generate"] += 1
    try:
        # STEP-Q10：客户端断开不再终止生成（RQ-09）；执行在后台按原预算跑完并保存
        async for part in pipeline.stream_answer(original, rw, c_gen, cfg):
            acc.append(part)
            yield emit("token", {"text": part}).encode("utf-8")
    except ModelError as exc:
        diag.record("model_error", f"generate:{exc.code}", conv_id=conv_id, exec_id=round_id)
        await finish(
            "gen_fail", {"answer": "", "c_gen": pub},
            reply=gen_fail_msg, completeness="error_notice", error_type="gen_fail",
        )
        yield emit("error", {
            "type": "gen_fail",
            "message": gen_fail_msg,
            "round_id": round_id,
            "c_gen": pub,
            **ids(),
        }).encode("utf-8")
        return
    except Exception as exc:  # noqa: BLE001
        log.exception("generate failed: %s", exc)
        diag.record("model_error", "generate:exception", conv_id=conv_id, exec_id=round_id)
        await finish(
            "gen_fail", {"answer": "", "c_gen": pub},
            reply=gen_fail_msg, completeness="error_notice", error_type="gen_fail",
        )
        yield emit("error", {
            "type": "gen_fail",
            "message": gen_fail_msg,
            "round_id": round_id,
            "c_gen": pub,
            **ids(),
        }).encode("utf-8")
        return

    # STEP-Q19：草稿用同一份 c_gen 检查；失败且预算允许最多修正一次再复查；异常不放行
    draft = "".join(acc)
    evidence = evidence_items(c_gen)
    constraint = "；".join(x for x in (rw.get("response_constraint"), settled.get("response_constraint")) if x)
    brief = cfg.get("_task_brief")
    check_rec: dict = {
        "ver": CHECK_VER,
        "evidence": [{k: e[k] for k in ("evidence_id", "path", "chunk_id", "content_hash", "content_scope")}
                     for e in evidence],
        "rounds": [],
        "repair_count": 0,
    }

    async def run_check(text: str) -> dict:
        call_usage["check"] += 1
        got = await evidence_checker.check(original, brief, rw["rewrite_query"], constraint, text, evidence, cfg)
        # 旧数字规则并入：数字不在证据中即为一条问题
        extra = number_issue(text, c_gen, original)
        if extra:
            got = dict(got, check_status="fail", issues=[*got["issues"], extra])
        process.observe("process", {"kind": "check", "check_status": got["check_status"],
                                     "issue_count": len(got["issues"]), "conflict": got["conflict"]})
        check_rec["rounds"].append({
            "draft_hash": draft_hash(text), "check_status": got["check_status"],
            "issues": got["issues"], "conflict": got["conflict"],
        })
        return got

    renew()
    yield emit("stage", {"stage": "check", "round_id": round_id}).encode("utf-8")
    final_text: str | None = None
    verdict: dict | None = None
    check_error: CheckError | None = None
    try:
        verdict = await run_check(draft)
        if verdict["check_status"] == "pass":
            final_text = draft
        elif check_rec["repair_count"] == 0 and deadline - time.monotonic() >= REPAIR_MIN_REMAINING_SEC:
            # 修正派发即占用这次机会；不重跑 Router、不查历史、不追加检索
            check_rec["repair_count"] = 1
            call_usage["repair"] += 1
            renew()
            yield emit("stage", {"stage": "repair", "round_id": round_id}).encode("utf-8")
            repaired = await evidence_checker.repair(
                original, brief, rw["rewrite_query"], constraint, draft, verdict["issues"], evidence, cfg,
            )
            yield emit("stage", {"stage": "check"}).encode("utf-8")
            verdict = await run_check(repaired)
            if verdict["check_status"] == "pass":
                final_text = repaired
        else:
            check_rec["budget_stop"] = True
    except CheckError as exc:
        check_error = exc
        check_rec["error"] = {"code": exc.code, "detail": exc.detail[:200]}
        diag.record("model_error", f"check:{exc.code}", conv_id=conv_id, exec_id=round_id)
    check_rec["final_hash"] = draft_hash(final_text) if final_text is not None else None
    if log_ok:
        logs.update_round(round_id, {"evidence_check": check_rec})

    if check_error is not None:
        yield emit("check", {
            "check_status": "error", "replaced": True, "text": CHECK_FAIL_MESSAGE, "round_id": round_id,
        }).encode("utf-8")
        await finish(
            "gen_fail", {"answer": "", "c_gen": pub}, reply=CHECK_FAIL_MESSAGE, completeness="error_notice",
            error_type=check_error.code, check_status="error",
        )
        yield emit("error", {
            "type": check_error.code,
            "message": CHECK_FAIL_MESSAGE,
            "round_id": round_id,
            "c_gen": pub,
            **ids(),
        }).encode("utf-8")
        return

    if final_text is None:
        # 被否决的草稿不成为正式回答版本；只保存失败说明，且不替换原有效版本
        suffix = "，已修正一次仍未通过" if check_rec["repair_count"] else "，剩余时间不足以修正" if check_rec.get("budget_stop") else ""
        notice = NOT_RELIABLE_MESSAGE.format(suffix=suffix)
        yield emit("check", {
            "check_status": "fail", "replaced": True, "text": notice, "round_id": round_id,
        }).encode("utf-8")
        await finish(
            "empty", {"answer": notice, "c_gen": pub}, reply=notice,
            biz_result="insufficient", check_status="fail", delivered=False,
        )
        yield emit("citations", {"items": pub}).encode("utf-8")
        yield emit("done", {
            "status": "empty",
            "round_id": round_id,
            "text": notice,
            "refused": True,
            "c_gen": pub,
            "log_written": log_ok,
            **ids(),
        }).encode("utf-8")
        return

    checked = post_check_answer(final_text, c_gen, original)
    status = "refuse" if checked["refused"] else "success"
    yield emit("check", {
        "check_status": "pass", "replaced": final_text != draft, "text": checked["text"], "round_id": round_id,
    }).encode("utf-8")
    # STEP-Q13：有未完成或不执行项时业务结果记部分完成，不写成已回答；STEP-Q19：原文互相冲突记 conflict
    biz = None
    if status == "success":
        if verdict and verdict.get("conflict"):
            biz = "conflict"
        elif partial_tasks or knowledge_partial:
            biz = "partial"
    await finish(
        status, {"answer": checked["text"], "c_gen": pub}, reply=checked["text"],
        biz_result=biz, check_status="pass",
    )
    yield emit("citations", {"items": pub}).encode("utf-8")
    yield emit("done", {
        "status": status,
        "round_id": round_id,
        "text": checked["text"],
        "refused": checked["refused"],
        "c_gen": pub,
        "log_written": log_ok,
        **ids(),
    }).encode("utf-8")


_TERMINAL_EXEC = ("completed", "failed", "interrupted")


@app.get("/api/kb/rounds/{exec_id}/status")
async def exec_status(exec_id: str, request: Request):
    """STEP-Q10：按执行只读查询状态与最终结果；前端断线或 EOF 未收到 done 时轮询，不重发 ask。
    只返回本人的执行；不存在、非本人、会话已隐藏统一 404。"""
    account = getattr(request.state, "account", None) or {}
    row = logs.get_round(exec_id)
    if not row or str(row.get("user_id") or "") != str(account.get("id") or ""):
        return listing.error(404, "未找到该执行", "round_not_found")
    conv_id = str(row.get("conv_id") or "")
    conv = convs.get_owned(str(account.get("id") or ""), conv_id) if conv_id else None
    if conv is None:
        return listing.error(404, "未找到该执行", "round_not_found")
    if row.get("logical_round_id") and not msgs.visible_round(conv_id, row["logical_round_id"]):
        return listing.error(404, "未找到该执行", "round_not_found")
    state = row.get("exec_state")
    derived = False
    if state not in _TERMINAL_EXEC:
        live = exec_id in _LIVE_EXECS
        inter = convs.interaction(convs.admin_get(conv_id) or {"id": conv_id})
        holding = inter.get("running_exec_id") == exec_id
        if not live and not holding:
            # 本进程没有在跑、租期也已不属于它：服务重启或崩溃遗留，只读地按中断报告，不写库
            state, derived = "interrupted", True
    terminal = state in _TERMINAL_EXEC
    text, completeness, version_no, is_current = None, None, None, None
    msg_id = row.get("assistant_msg_id")
    if msg_id:
        found = msgs.get_by_ids(conv_id, [str(msg_id)])
        if found:
            text = found[0].get("content")
            completeness = found[0].get("completeness")
            version_no = found[0].get("version_no")
            is_current = bool(found[0].get("is_current"))
    elif row.get("pending_reply") or _PENDING_REPLIES.get(exec_id):
        carrier = row.get("pending_reply") or _PENDING_REPLIES.get(exec_id) or {}
        text, completeness = carrier.get("content"), carrier.get("completeness")
    inter = convs.interaction(convs.admin_get(conv_id) or {"id": conv_id})
    statuses = {k: row.get(k) for k in STATUS_KEYS}
    if derived:
        statuses["exec_state"] = "interrupted"
    return {
        "ok": True,
        "exec_id": exec_id,
        "conversation_id": conv_id,
        "logical_round_id": row.get("logical_round_id"),
        "op_type": row.get("op_type"),
        "terminal": terminal,
        "derived": derived,
        "status": row.get("status"),
        "statuses": statuses,
        "error_type": row.get("error_type") or ("service_interrupted" if derived else None),
        "text": text,
        "completeness": completeness,
        "assistant_msg_id": msg_id,
        "version_no": version_no,
        "adopted": is_current,
        "save_blocked": inter.get("blocked_exec_id") == exec_id,
        "c_gen": row.get("c_gen") or [],
        "process": process_for_row(dict(row, exec_state=state)),
    }


@app.get("/api/kb/chunk")
async def chunk_source(path: str = "", chunk_id: str = "", content_hash: str = ""):
    """STEP-Q18（S01 §20.2）：点击知识引用时按当前可读性复核。hash 对不上或读不到时不返回正文，
    不把新正文配到旧 hash 上。"""
    path, chunk_id, content_hash = path.strip(), chunk_id.strip(), content_hash.strip()
    if not path or not chunk_id:
        return listing.error(400, "缺少 path 或 chunk_id", "invalid_request")
    try:
        payload = store.lookup_payload(path, chunk_id)
    except Exception as exc:  # noqa: BLE001
        log.warning("chunk lookup failed: %s", exc)
        return listing.error(503, "来源暂时无法读取", "source_unavailable")
    content = str((payload or {}).get("content") or "").strip()
    if not payload or not content:
        return listing.error(404, "来源已不存在或不可读", "source_not_found")
    current_hash = str(payload.get("content_hash") or "")
    if content_hash and current_hash != content_hash:
        return listing.error(409, "来源已更新，原引用对应的正文已不可用", "source_changed")
    return {
        "ok": True,
        "path": path,
        "chunk_id": chunk_id,
        "heading": payload.get("heading") or "",
        "anchor": payload.get("anchor") or "",
        "feature_id": payload.get("feature_id") or "",
        "content_hash": current_hash,
        "content": content,
    }


@app.post("/api/kb/ask")
async def ask(request: Request):
    body = await request.json()
    return StreamingResponse(
        _ask_events(request, body),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
