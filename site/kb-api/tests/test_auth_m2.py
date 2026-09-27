# -*- coding: utf-8 -*-
"""M2：登录墙、提问身份、云端会话隔离。"""
from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app import main
from app.auth_store import ROLE_USER_ID
from tests.test_auth_m1 import _login, harness  # noqa: F401


ROOT = Path(__file__).resolve().parents[3]
QA_HTML = (ROOT / "site" / "feature-interaction" / "index.html").read_text(encoding="utf-8")
QA_JS = (ROOT / "site" / "feature-interaction" / "qa.js").read_text(encoding="utf-8")
APP_JS = (ROOT / "site" / "feature-interaction" / "app.js").read_text(encoding="utf-8")
KB_JS = (ROOT / "site" / "feature-interaction" / "kb.js").read_text(encoding="utf-8")
LOGIN_HTML = (ROOT / "site" / "login" / "index.html").read_text(encoding="utf-8")
LOGIN_JS = (ROOT / "site" / "login" / "login.js").read_text(encoding="utf-8")
INIT_SQL = (ROOT / "site" / "kb-api" / "sql" / "init.sql").read_text(encoding="utf-8")


def test_login_wall_and_graph_views_static():
    assert 'id="loginUser"' in LOGIN_HTML
    assert 'id="loginPass"' in LOGIN_HTML
    assert 'id="loginSubmit"' in LOGIN_HTML
    assert "请先登录" in LOGIN_HTML
    assert "function safeNext" in LOGIN_JS
    assert 'id="qaLoginUser"' not in QA_HTML
    assert 'id="qaLoginWall"' not in QA_HTML
    assert 'data-view="admin"' in QA_HTML
    assert 'data-view="client"' in QA_HTML
    assert 'data-view="kb"' in QA_HTML
    assert 'data-view="qa"' in QA_HTML
    assert "/api/kb" not in APP_JS
    assert "/api/kb" not in KB_JS
    assert "if (!state.me)" in QA_JS
    assert "/login/" in QA_JS
    assert "hayyo-kb-qa-conversations-v1" in QA_JS
    assert "loadCloud" in QA_JS
    assert "CREATE TABLE IF NOT EXISTS kb_conversations" in INIT_SQL
    assert "CREATE TABLE IF NOT EXISTS qa_rounds" in INIT_SQL


def test_ask_unauth_and_no_qa_perm_403(harness):
    client, store = harness
    ask = client.post("/api/kb/ask", json={"query": "hi"})
    assert ask.status_code == 401
    assert "event: done" not in ask.text
    store.repo.upsert_role({
        "id": "role-ops",
        "name": "仅配置",
        "is_super": 0,
        "is_preset": 0,
        "created_at": store.now(),
    })
    store.repo.set_role_perms("role-ops", ["配置"])
    store.create_account("ops", "pw", "role-ops")
    assert _login(client, "ops", "pw").status_code == 200
    denied = client.post("/api/kb/ask", json={"query": "hi"})
    assert denied.status_code == 403


def test_round_uid_and_feedback_owner(harness, monkeypatch):
    client, store = harness
    captured = {}

    def insert_running(row):
        captured["row"] = dict(row)
        return True

    monkeypatch.setattr(main.logs, "insert_running", insert_running)
    monkeypatch.setattr(main.logs, "update_round", lambda *a, **k: True)
    store.create_account("alice", "pw", ROLE_USER_ID)
    store.create_account("bob", "pw", ROLE_USER_ID)
    assert _login(client, "alice", "pw").status_code == 200
    me = client.get("/api/kb/auth/me").json()["id"]
    client.post("/api/kb/ask", json={"query": "hi", "user_id": "forged-other"})
    assert captured["row"]["user_id"] == me
    assert captured["row"]["user_id"] != "forged-other"

    rounds = {
        "r1": {"round_id": "r1", "user_id": me, "feedback": None, "answer": "ok", "status": "success"},
    }

    def get_round(rid):
        row = rounds.get(rid)
        return dict(row) if row else None

    def set_feedback(rid, fb):
        rounds[rid]["feedback"] = fb
        return "ok"

    monkeypatch.setattr(main.logs, "get_round", get_round)
    monkeypatch.setattr(main.logs, "set_feedback", set_feedback)
    assert client.post("/api/kb/rounds/r1/feedback", json={"feedback": "up"}).status_code == 200
    client.post("/api/kb/auth/logout")
    assert _login(client, "bob", "pw").status_code == 200
    assert client.post("/api/kb/rounds/r1/feedback", json={"feedback": "down"}).status_code == 403
    client.post("/api/kb/auth/logout")
    assert _login(client, "admin", "secret").status_code == 200
    assert client.post("/api/kb/rounds/r1/feedback", json={"feedback": "down"}).status_code == 403
    anon = TestClient(main.app)
    assert anon.post("/api/kb/rounds/r1/feedback", json={"feedback": "up"}).status_code == 401


def test_cloud_convs_isolated_not_import_local(harness):
    client, store = harness
    store.create_account("alice", "pw", ROLE_USER_ID)
    store.create_account("bob", "pw", ROLE_USER_ID)
    assert client.get("/api/kb/conversations").status_code == 401
    assert _login(client, "alice", "pw").status_code == 200
    c1 = client.post("/api/kb/conversations", json={"title": "A1"}).json()
    c2 = client.post("/api/kb/conversations", json={"title": "A2"}).json()
    ids_a = {c1["id"], c2["id"]}
    listed = client.get("/api/kb/conversations").json()["items"]
    assert {x["id"] for x in listed} == ids_a
    client.post("/api/kb/auth/logout")
    other = TestClient(main.app)
    assert _login(other, "bob", "pw").status_code == 200
    other.post("/api/kb/conversations", json={"title": "B1", "id": c1["id"]})
    bob_ids = {x["id"] for x in other.get("/api/kb/conversations").json()["items"]}
    assert bob_ids.isdisjoint(ids_a)
    assert other.get("/api/kb/conversations/" + c1["id"]).status_code == 404
    assert other.delete("/api/kb/conversations/" + c1["id"]).status_code == 404
    assert _login(client, "alice", "pw").status_code == 200
    assert client.delete("/api/kb/conversations/" + c1["id"]).status_code == 200
    left = {x["id"] for x in client.get("/api/kb/conversations").json()["items"]}
    assert c1["id"] not in left
    assert c2["id"] in left
    # 删会话不碰 qa_rounds 表结构
    assert "CREATE TABLE IF NOT EXISTS qa_rounds" in INIT_SQL
