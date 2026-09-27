# -*- coding: utf-8 -*-
"""M1：空库引导、登录锁定、改密作废 Session、运维接口鉴权。"""
from __future__ import annotations

import json
from datetime import timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import main
from app.auth_store import (
    LOGIN_FAIL_MSG,
    LOGIN_LOCK_MSG,
    PERM_CHECKBOX,
    ROLE_USER_ID,
    AuthStore,
    MemoryAuthRepo,
)
from app.conv_store import ConvStore, MemoryConvRepo
from app import settings


ROOT = Path(__file__).resolve().parents[3]
INIT_SQL = (ROOT / "site" / "kb-api" / "sql" / "init.sql").read_text(encoding="utf-8")
COOKIE = settings.AUTH_COOKIE_NAME
OPS = [
    ("GET", "/api/kb/config"),
    ("PUT", "/api/kb/config"),
    ("POST", "/api/kb/reindex"),
    ("GET", "/api/kb/rounds"),
    ("GET", "/api/kb/rounds/sample-id"),
]


async def _noop_index():
    return None


@pytest.fixture
def harness(monkeypatch):
    store = AuthStore(MemoryAuthRepo())
    store.ensure_schema()
    store.bootstrap_if_empty("admin", "secret")
    convs = ConvStore(MemoryConvRepo())
    convs.ensure_schema()
    monkeypatch.setattr(main, "auth", store)
    monkeypatch.setattr(main, "convs", convs)
    monkeypatch.setattr(main, "_startup_index", _noop_index)
    monkeypatch.setattr(main.logs, "ensure_feedback_columns", lambda: True)
    with TestClient(main.app) as client:
        yield client, store


def _login(client: TestClient, username: str, password: str):
    return client.post("/api/kb/auth/login", json={"username": username, "password": password})


def _cookie_header(resp) -> str:
    return resp.headers.get("set-cookie") or ""


def test_init_sql_keeps_qa_rounds_and_adds_auth_tables():
    assert "CREATE TABLE IF NOT EXISTS qa_rounds" in INIT_SQL
    assert "DROP TABLE" not in INIT_SQL
    for name in (
        "kb_roles",
        "kb_role_permissions",
        "kb_accounts",
        "kb_sessions",
        "kb_login_locks",
        "kb_audit_logs",
        "tenant_id VARCHAR(64) NULL",
    ):
        assert name in INIT_SQL


def test_bootstrap_empty_db_and_no_reset():
    store = AuthStore(MemoryAuthRepo())
    store.ensure_schema()
    assert store.repo.count_accounts() == 0
    assert store.bootstrap_if_empty("admin", "p1") is True
    acc = store.hydrate_account(store.repo.get_account_by_username("admin"))
    assert acc is not None
    assert acc["enabled"] is True
    assert acc["is_super"] is True
    assert acc.get("tenant_id") is None
    assert store.role_perm_set(ROLE_USER_ID) == {"知识问答"}
    assert store.role_perm_set("role-super") == set(PERM_CHECKBOX)
    h1 = store.repo.get_account_by_username("admin")["password_hash"]
    assert "p1" not in str(h1)
    assert store.bootstrap_if_empty("admin", "changed-password") is False
    h2 = store.repo.get_account_by_username("admin")["password_hash"]
    assert h1 == h2


def test_no_self_register_route(harness):
    client, _store = harness
    paths = [getattr(r, "path", "") for r in main.app.routes]
    assert not any("register" in p or "signup" in p for p in paths)
    denied = client.post("/api/kb/auth/register", json={"username": "x", "password": "y"})
    assert denied.status_code in {401, 403, 404, 405}


def test_login_cookie_me_logout_and_audit(harness):
    client, store = harness
    login = _login(client, "admin", "secret")
    assert login.status_code == 200
    sc = _cookie_header(login).lower()
    assert "httponly" in sc
    assert COOKIE.lower() in sc
    assert "jwt" not in sc
    body = login.json()
    assert "jwt" not in json.dumps(body).lower()
    assert body["id"]
    me = client.get("/api/kb/auth/me")
    assert me.status_code == 200
    assert me.json()["id"] == body["id"]
    out = client.post("/api/kb/auth/logout")
    assert out.status_code == 200
    dead = client.get("/api/kb/auth/me")
    assert dead.status_code == 401
    actions = [a["action"] for a in store.list_audits()]
    assert "login_success" in actions
    dumped = json.dumps(store.list_audits(), ensure_ascii=False, default=str)
    assert "secret" not in dumped
    assert "password" not in dumped.lower() or "password_hash" not in dumped.lower()
    # 审计不得出现明文密码；允许字段名里没有 password
    assert "secret" not in dumped


def test_lock_rule_and_lock_leak(harness):
    client, store = harness
    missing = _login(client, "no-such-user", "x")
    assert missing.status_code == 401
    assert missing.json()["message"] == LOGIN_FAIL_MSG
    assert "用户不存在" not in missing.json()["message"]
    assert "密码错误" != missing.json()["message"]
    for _ in range(5):
        bad = _login(client, "admin", "wrong")
        assert bad.status_code == 401
        assert bad.json()["message"] == LOGIN_FAIL_MSG
        assert bad.json()["message"] == missing.json()["message"]
    sixth = _login(client, "admin", "secret")
    assert sixth.status_code == 401
    assert "稍后重试" in sixth.json()["message"]
    assert sixth.json()["message"] == LOGIN_LOCK_MSG
    dumped = json.dumps(store.list_audits(), ensure_ascii=False, default=str)
    assert "wrong" not in dumped
    assert "login_fail" in [a["action"] for a in store.list_audits()]


def test_session_dead_after_seven_days(harness):
    client, store = harness
    from datetime import datetime
    t0 = datetime(2026, 1, 1, 0, 0, 0)
    store.set_now(t0)
    login = _login(client, "admin", "secret")
    assert login.status_code == 200
    assert client.get("/api/kb/auth/me").status_code == 200
    store.set_now(t0 + timedelta(days=7, seconds=1))
    dead = client.get("/api/kb/auth/me")
    assert dead.status_code == 401


def test_change_password_revokes_all_sessions(harness):
    client, store = harness
    first = _login(client, "admin", "secret")
    assert first.status_code == 200
    sid1 = first.cookies.get(COOKIE) or client.cookies.get(COOKIE)
    second = _login(client, "admin", "secret")
    assert second.status_code == 200
    sid2 = second.cookies.get(COOKIE)
    assert sid1 and sid2 and sid1 != sid2
    client.cookies.set(COOKIE, sid2)
    wrong = client.post(
        "/api/kb/auth/password",
        json={"old_password": "nope", "new_password": "new-secret"},
    )
    assert wrong.status_code == 400
    still = client.get("/api/kb/auth/me")
    assert still.status_code == 200
    h_before = store.repo.get_account_by_username("admin")["password_hash"]
    ok = client.post(
        "/api/kb/auth/password",
        json={"old_password": "secret", "new_password": "new-secret"},
    )
    assert ok.status_code == 200
    h_after = store.repo.get_account_by_username("admin")["password_hash"]
    assert h_before != h_after
    client.cookies.set(COOKIE, sid1)
    assert client.get("/api/kb/auth/me").status_code == 401
    client.cookies.set(COOKIE, sid2)
    assert client.get("/api/kb/auth/me").status_code == 401
    dumped = json.dumps(store.list_audits(), ensure_ascii=False, default=str)
    assert "new-secret" not in dumped
    assert "secret" not in dumped
    relogin = _login(client, "admin", "new-secret")
    assert relogin.status_code == 200
    # 不强制首次改密：引导口令可直接登录已在其它用例覆盖


def test_ops_deny_anonymous_and_role_user(harness):
    client, store = harness
    for method, path in OPS:
        resp = client.request(method, path, json={} if method in {"PUT", "POST"} else None)
        assert resp.status_code in {401, 403}, (method, path, resp.status_code)
    ask = client.post("/api/kb/ask", json={"query": "hi"})
    assert ask.status_code == 401
    assert "event: done" not in ask.text
    heat = client.get("/api/kb/heatmap")
    assert heat.status_code == 401

    store.create_account("alice", "pw", ROLE_USER_ID)
    assert _login(client, "alice", "pw").status_code == 200
    for method, path in OPS:
        resp = client.request(method, path, json={} if method in {"PUT", "POST"} else None)
        assert resp.status_code == 403, (method, path, resp.status_code)

    client.post("/api/kb/auth/logout")
    assert _login(client, "admin", "secret").status_code == 200
    cfg = client.get("/api/kb/config")
    assert cfg.status_code == 200
    put = client.put("/api/kb/config", json={"writable": {}})
    assert put.status_code not in {401, 403}
    reindex = client.post("/api/kb/reindex")
    assert reindex.status_code not in {401, 403}
    rounds = client.get("/api/kb/rounds")
    assert rounds.status_code not in {401, 403}
    one = client.get("/api/kb/rounds/missing-round")
    assert one.status_code not in {401, 403}
