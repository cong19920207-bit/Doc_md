# -*- coding: utf-8 -*-
"""kb-api：浏览器只打本服务；Session Cookie 鉴权。"""
from __future__ import annotations

import asyncio
import json
import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

from fastapi import FastAPI, Query, Request
from fastapi.responses import JSONResponse, Response, StreamingResponse

from . import settings
from .auth_store import PERM_CHECKBOX, AuthStore
from .conv_store import ConvStore, MAX_CONVS
from .config_store import ConfigStore
from .tls_store import TlsStore
from .indexer import Indexer
from .aliases import c20_display_name
from .logs import LogStore
from .models_ext import ModelClients, ModelError, key_status, missing_keys
from .pipeline import Pipeline, post_check_answer, public_c_gen
from .store import VectorStore
from .util import uid

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("kb-api")

store = VectorStore()
models = ModelClients()
config_store = ConfigStore()
logs = LogStore()
auth = AuthStore()
convs = ConvStore()
tls = TlsStore()
indexer = Indexer(store, models.embed)
pipeline = Pipeline(store, models, lambda: config_store.data)
index_lock = asyncio.Lock()
index_ready = False
startup_error = ""


async def _startup_index() -> None:
    global index_ready, startup_error
    try:
        store.ensure_collections()
        if missing_keys():
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
    logs.ensure_feedback_columns()
    auth.ensure_schema()
    auth.bootstrap_if_empty()
    convs.ensure_schema()
    asyncio.create_task(_startup_index())
    yield


app = FastAPI(title="Hayyo kb-api", lifespan=lifespan)


@app.middleware("http")
async def auth_guard(request: Request, call_next):
    """分档：登录/登出/me 白名单；OPS_READ_WRITE 要勾选；未登录 ask/heatmap 401。"""
    path = request.url.path
    method = request.method.upper()
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
        if not auth.has_perm(account, ops):
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
    return await call_next(request)


def _deny(status: int, message: str) -> JSONResponse:
    return JSONResponse({"ok": False, "message": message}, status_code=status)


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


def _ops_perm(method: str, path: str) -> str | None:
    if path == "/api/kb/config" and method in ("GET", "PUT"):
        return "配置"
    if path == "/api/kb/reindex" and method == "POST":
        return "重建"
    if method == "GET" and path == "/api/kb/rounds":
        return "问答明细"
    if method == "GET" and path.startswith("/api/kb/rounds/") and "/feedback" not in path:
        return "问答明细"
    if method == "GET" and path == "/api/kb/admin/conversations":
        return "对话审计"
    if method == "GET" and path == "/api/kb/admin/audits":
        return "操作审计"
    if method == "GET" and path == "/api/kb/admin/feedback-summary":
        return "反馈汇总"
    if method == "GET" and path == "/api/kb/admin/heatmap":
        return "功能热度"
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
    return {
        "id": row.get("id"),
        "actor_id": row.get("actor_id"),
        "actor_username": row.get("actor_username"),
        "action": row.get("action"),
        "object": row.get("object"),
        "ip": row.get("ip"),
        "created_at": str(row.get("created_at") or ""),
        "detail": detail,
    }


@app.get("/api/kb/auth/admin-gate")
async def admin_gate(request: Request):
    account = getattr(request.state, "account", None)
    if account is None:
        return _deny(401, "未登录")
    if auth.has_perm(account, "进管理模块"):
        return Response(status_code=204)
    return _deny(403, "没有权限")


@app.get("/api/kb/conversations")
async def list_conversations(request: Request):
    account, err = _require_account(request)
    if err:
        return err
    return {"items": convs.list_public(str(account["id"])), "max": MAX_CONVS}


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
        return JSONResponse({"message": "未找到该会话"}, status_code=404)
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
    row = convs.update(str(account["id"]), conv_id, body)
    if not row:
        return JSONResponse({"message": "未找到该会话"}, status_code=404)
    return row


@app.delete("/api/kb/conversations/{conv_id}")
async def delete_conversation(conv_id: str, request: Request):
    account, err = _require_account(request)
    if err:
        return err
    if not convs.delete(str(account["id"]), conv_id):
        return JSONResponse({"message": "未找到该会话"}, status_code=404)
    return {"ok": True}


@app.get("/api/kb/admin/conversations")
async def admin_conversations():
    names = _account_usernames()
    items = [_attach_username(r, "account_id", names) for r in convs.list_all_public()]
    return {"items": items}


@app.get("/api/kb/admin/audits")
async def admin_audits():
    return {"items": [_public_audit(r) for r in auth.list_audits()]}


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


@app.get("/api/kb/admin/heatmap")
async def admin_heatmap():
    data = logs.heatmap()
    items = []
    for item in data.get("items") or []:
        row = dict(item)
        row["display_name"] = c20_display_name(str(row.get("feature_id") or ""))
        items.append(row)
    return {"items": items, "unclassified": data.get("unclassified", 0)}


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
    return {"items": auth.list_accounts_public()}


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
    try:
        created = auth.create_user(
            str(body.get("username") or ""),
            str(body.get("password") or ""),
            str(body.get("role_id") or ""),
        )
    except ValueError as exc:
        return _deny(400, str(exc))
    auth.write_audit(
        "create_account",
        actor_id=str(account["id"]),
        actor_username=str(account.get("username") or ""),
        object_=str(created.get("id") or ""),
        ip=_client_ip(request),
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
    try:
        out = None
        if "enabled" in body:
            out = auth.set_account_enabled(account_id, bool(body.get("enabled")))
            auth.write_audit(
                "disable_account" if not bool(body.get("enabled")) else "enable_account",
                actor_id=str(account["id"]),
                actor_username=str(account.get("username") or ""),
                object_=account_id,
                ip=_client_ip(request),
                detail={"enabled": bool(body.get("enabled"))},
            )
        if "role_id" in body:
            out = auth.set_account_role(account_id, str(body.get("role_id") or ""))
            auth.write_audit(
                "change_role",
                actor_id=str(account["id"]),
                actor_username=str(account.get("username") or ""),
                object_=account_id,
                ip=_client_ip(request),
                detail={"role_id": str(body.get("role_id") or "")},
            )
    except KeyError as exc:
        return _deny(404, str(exc))
    except PermissionError as exc:
        return _deny(403, str(exc))
    except ValueError as exc:
        return _deny(400, str(exc))
    if out is None:
        return _deny(400, "没有可改字段")
    return out


@app.get("/api/kb/admin/roles")
async def admin_list_roles(request: Request):
    account, err = _require_super(request)
    if err:
        return err
    return {"items": auth.list_roles_public(), "checkboxes": list(PERM_CHECKBOX)}


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
    created = auth.create_custom_role(str(body.get("name") or ""), [str(p) for p in perms])
    auth.write_audit(
        "create_role",
        actor_id=str(account["id"]),
        actor_username=str(account.get("username") or ""),
        object_=str(created.get("id") or ""),
        ip=_client_ip(request),
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
    try:
        out = auth.set_custom_role_perms(role_id, [str(p) for p in perms])
    except KeyError as exc:
        return _deny(404, str(exc))
    except PermissionError as exc:
        return _deny(403, str(exc))
    auth.write_audit(
        "change_role_perms",
        actor_id=str(account["id"]),
        actor_username=str(account.get("username") or ""),
        object_=role_id,
        ip=_client_ip(request),
        detail={"permissions": out.get("permissions") or []},
    )
    return out


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
    auth.unlock_username(username)
    auth.write_audit(
        "unlock",
        actor_id=str(account["id"]),
        actor_username=str(account.get("username") or ""),
        object_=username,
        ip=_client_ip(request),
        detail={"username": username},
    )
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
    try:
        out = tls.save_upload(str(body.get("cert_pem") or ""), str(body.get("key_pem") or ""))
    except ValueError as exc:
        return _deny(400, str(exc))
    auth.write_audit(
        "tls_upload",
        actor_id=str(account["id"]),
        actor_username=str(account.get("username") or ""),
        object_="tls",
        ip=_client_ip(request),
        detail={"has_cert": True},
    )
    return out


@app.post("/api/kb/admin/tls/enable")
async def admin_tls_enable(request: Request):
    account, err = _require_super(request)
    if err:
        return err
    try:
        out = tls.enable()
    except ValueError as exc:
        return _deny(400, str(exc))
    auth.write_audit(
        "tls_enable",
        actor_id=str(account["id"]),
        actor_username=str(account.get("username") or ""),
        object_="tls",
        ip=_client_ip(request),
        detail={"enabled": True},
    )
    return out


@app.post("/api/kb/admin/tls/disable")
async def admin_tls_disable(request: Request):
    account, err = _require_super(request)
    if err:
        return err
    out = tls.disable()
    auth.write_audit(
        "tls_disable",
        actor_id=str(account["id"]),
        actor_username=str(account.get("username") or ""),
        object_="tls",
        ip=_client_ip(request),
        detail={"enabled": False},
    )
    return out


@app.get("/api/kb/config")
async def get_config():
    return config_store.snapshot()


@app.put("/api/kb/config")
async def put_config(request: Request, body: dict):
    writable = body.get("writable") if isinstance(body.get("writable"), dict) else body
    if not isinstance(writable, dict):
        writable = {}
    out = config_store.update_writable(writable)
    account = getattr(request.state, "account", None)
    if account:
        auth.write_audit(
            "config_update",
            actor_id=str(account["id"]),
            actor_username=str(account.get("username") or ""),
            object_=str(account["id"]),
            ip=_client_ip(request),
            detail={"fields": list(writable.keys())},
        )
    return out


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
    async with index_lock:
        try:
            result = await indexer.rebuild()
        except ModelError as exc:
            return JSONResponse(
                {"ok": False, "error_type": exc.code, "message": exc.message},
                status_code=exc.status_code,
            )
    global index_ready
    index_ready = result.get("chunk_count", 0) > 0
    if account:
        auth.write_audit(
            "reindex",
            actor_id=str(account["id"]),
            actor_username=str(account.get("username") or ""),
            object_=str(account["id"]),
            ip=_client_ip(request),
            detail={"ok": True},
        )
    return {"ok": True, **result}


@app.get("/api/kb/rounds")
async def list_rounds(
    q: str = "",
    feature_id: str = "",
    status: str = "",
    limit: int = Query(100, ge=1, le=500),
):
    names = _account_usernames()
    items = [_attach_username(r, "user_id", names) for r in logs.list_rounds(
        q=q, feature_id=feature_id, status=status, limit=limit
    )]
    return {"items": items}


@app.get("/api/kb/rounds/{round_id}")
async def get_round(round_id: str):
    row = logs.get_round(round_id)
    if not row:
        return JSONResponse({"message": "未找到该轮"}, status_code=404)
    return _attach_username(row, "user_id")


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
    return {"items": items, "unclassified": data.get("unclassified", 0)}


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


async def _ask_events(request: Request, body: dict) -> AsyncIterator[bytes]:
    health = _health()
    conv_id = str(body.get("conversation_id") or uid("c"))
    round_id = str(body.get("round_id") or uid("r"))
    original = str(body.get("query") or "").strip()
    history = body.get("history") or []
    prev_blocks = body.get("last_chunks") or []
    cfg = dict(config_store.data)
    models_snap = {
        "rewrite": settings.LLM_MODEL,
        "embedding": settings.EMBED_MODEL,
        "rerank": settings.RERANK_MODEL,
        "generate": settings.LLM_MODEL,
    }
    account = getattr(request.state, "account", None)
    session_uid = (account or {}).get("id")
    log_ok = logs.insert_running({
        "round_id": round_id,
        "conv_id": conv_id,
        "original_query": original,
        "models": models_snap,
        "user_id": session_uid,
        "owner_id": body.get("owner_id"),
        "tenant_id": body.get("tenant_id"),
        "role": body.get("role"),
    })
    if not log_ok:
        yield _sse("log", {"written": False, "message": "本轮日志未写入"}).encode("utf-8")

    async def finish(status: str, extra: dict | None = None) -> None:
        payload = {"status": status, "models": models_snap}
        if extra:
            payload.update(extra)
        if log_ok:
            logs.update_round(round_id, payload)

    fail = _fail_type(health)
    if fail:
        code, message = fail
        await finish("gen_fail")
        yield _sse("error", {
            "type": code,
            "message": message,
            "round_id": round_id,
            "log_written": log_ok,
        }).encode("utf-8")
        return
    if not original:
        await finish("gen_fail")
        yield _sse("error", {"type": "rewrite_fail", "message": "问句为空", "round_id": round_id}).encode("utf-8")
        return

    yield _sse("stage", {"stage": "rewrite", "round_id": round_id}).encode("utf-8")
    try:
        rw = await pipeline.rewrite(original, history, cfg)
    except ModelError as exc:
        kind = "missing_key" if exc.code == "missing_key" else "rewrite_fail"
        await finish("rewrite_fail")
        yield _sse("error", {
            "type": kind,
            "message": exc.message if kind == "missing_key" else "改写失败，本轮未检索、未生成。可重试。",
            "round_id": round_id,
            "log_written": log_ok,
        }).encode("utf-8")
        return
    except Exception as exc:  # noqa: BLE001
        log.exception("rewrite failed: %s", exc)
        await finish("rewrite_fail")
        yield _sse("error", {
            "type": "rewrite_fail",
            "message": "改写失败，本轮未检索、未生成。可重试。",
            "round_id": round_id,
            "log_written": log_ok,
        }).encode("utf-8")
        return

    if log_ok:
        logs.update_round(round_id, {
            "rewrite_query": rw["rewrite_query"],
            "same_topic": 1 if rw["same_topic"] else 0,
            "named_feature_ids": rw["named_feature_ids"],
        })
    yield _sse("rewrite", rw).encode("utf-8")

    yield _sse("stage", {"stage": "retrieve"}).encode("utf-8")
    try:
        retrieved = await pipeline.retrieve(original, rw["rewrite_query"], rw["named_feature_ids"], cfg)
    except ModelError as exc:
        kind = "missing_key" if exc.code == "missing_key" else (
            "index_not_ready" if "qdrant" in exc.message.lower() else "retrieve_fail"
        )
        if exc.status_code >= 500:
            kind = "retrieve_fail"
        await finish("gen_fail", {"named_feature_ids": rw["named_feature_ids"]})
        yield _sse("error", {
            "type": kind,
            "message": "索引未就绪" if kind == "index_not_ready" else exc.message,
            "round_id": round_id,
            "candidates": [],
            "log_written": log_ok,
        }).encode("utf-8")
        return
    except Exception as exc:  # noqa: BLE001
        log.exception("retrieve failed: %s", exc)
        await finish("gen_fail")
        yield _sse("error", {
            "type": "index_not_ready" if not store.ping() else "retrieve_fail",
            "message": "索引未就绪" if not store.ping() else "检索失败",
            "round_id": round_id,
            "candidates": [],
        }).encode("utf-8")
        return

    paths = sorted({c.get("path") or "" for c in retrieved["candidates"] if c.get("path")})
    yield _sse("retrieve", {
        "mode": retrieved["mode"],
        "lanes": retrieved["lanes"],
        "paths": paths,
        "count": len(retrieved["candidates"]),
    }).encode("utf-8")

    yield _sse("stage", {"stage": "rerank"}).encode("utf-8")
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
        await finish("gen_fail", {
            "named_feature_ids": rw["named_feature_ids"],
            "lanes": retrieved["lanes"],
        })
        yield _sse("error", {
            "type": "rerank_fail",
            "message": exc.message,
            "round_id": round_id,
            "c_gen": [],
        }).encode("utf-8")
        return

    pub = public_c_gen(c_gen)
    yield _sse("rerank", {"c_gen": pub}).encode("utf-8")
    if log_ok:
        logs.update_round(round_id, {
            "lanes": retrieved["lanes"],
            "c_gen": pub,
            "named_feature_ids": rw["named_feature_ids"],
        })

    if not c_gen:
        msg = "文档未写。重排后 0 块，系统拒答。"
        await finish("empty", {"answer": msg, "c_gen": []})
        yield _sse("refuse", {"text": msg, "c_gen": [], "status": "empty"}).encode("utf-8")
        yield _sse("done", {"status": "empty", "round_id": round_id, "log_written": log_ok}).encode("utf-8")
        return

    yield _sse("stage", {"stage": "generate"}).encode("utf-8")
    acc = []
    try:
        async for part in pipeline.stream_answer(original, rw, c_gen, cfg):
            if await request.is_disconnected():
                await finish("interrupted", {"answer": "", "c_gen": pub})
                yield _sse("done", {"status": "interrupted", "round_id": round_id, "log_written": log_ok}).encode("utf-8")
                return
            acc.append(part)
            yield _sse("token", {"text": part}).encode("utf-8")
    except ModelError as exc:
        await finish("gen_fail", {"answer": "", "c_gen": pub})
        yield _sse("error", {
            "type": "gen_fail",
            "message": "生成失败。半段正文已丢弃，不展示完整回答。",
            "round_id": round_id,
            "c_gen": pub,
        }).encode("utf-8")
        return
    except Exception as exc:  # noqa: BLE001
        log.exception("generate failed: %s", exc)
        await finish("gen_fail", {"answer": "", "c_gen": pub})
        yield _sse("error", {
            "type": "gen_fail",
            "message": "生成失败。半段正文已丢弃，不展示完整回答。",
            "round_id": round_id,
            "c_gen": pub,
        }).encode("utf-8")
        return

    checked = post_check_answer("".join(acc), c_gen, original)
    status = "refuse" if checked["refused"] else "success"
    await finish(status, {"answer": checked["text"], "c_gen": pub})
    yield _sse("citations", {"items": pub}).encode("utf-8")
    yield _sse("done", {
        "status": status,
        "round_id": round_id,
        "text": checked["text"],
        "refused": checked["refused"],
        "c_gen": pub,
        "log_written": log_ok,
    }).encode("utf-8")


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
