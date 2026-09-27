# -*- coding: utf-8 -*-
"""M3：去四钮、独立管理站、开户/解锁、热度分层。"""
from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app import main
from app.auth_store import ROLE_USER_ID
from tests.test_auth_m1 import _login, harness  # noqa: F401


ROOT = Path(__file__).resolve().parents[3]
QA_HTML = (ROOT / "site" / "feature-interaction" / "index.html").read_text(encoding="utf-8")
QA_JS = (ROOT / "site" / "feature-interaction" / "qa.js").read_text(encoding="utf-8")
ADMIN_HTML = (ROOT / "site" / "kb-admin" / "index.html").read_text(encoding="utf-8")
ADMIN_JS = (ROOT / "site" / "kb-admin" / "admin.js").read_text(encoding="utf-8")
NGINX = (ROOT / "site" / "docker" / "nginx.conf").read_text(encoding="utf-8")


def test_topbar_no_four_buttons_and_account_menu():
    assert "data-qa-config" not in QA_HTML
    assert "data-qa-reindex" not in QA_HTML
    assert "data-qa-rounds" not in QA_HTML
    assert "data-qa-heatmap" not in QA_HTML
    assert 'id="qaHealth"' in QA_HTML
    assert "退出" in QA_HTML
    assert "修改密码" in QA_HTML
    assert "/kb-admin/" in QA_JS
    assert "进管理模块" in QA_JS
    assert "admin-skin" not in ADMIN_HTML
    assert "admin-skin" not in ADMIN_JS
    assert "location ^~ /kb-admin/" in NGINX
    assert "auth_request" in NGINX
    assert "location ^~ /login/" in NGINX
    assert "_kb_site_gate" in NGINX
    assert "auth_request off" in NGINX
    assert "CHIP_FIXED" in QA_JS
    assert "qa-chips-heat" in QA_JS


def _make_mingxi(store):
    role = store.create_custom_role("明细", ["进管理模块", "问答明细"])
    acc = store.create_user("mingxi", "pw", role["id"])
    return acc, role


def test_admin_gate_and_mingxi_pages(harness):
    client, store = harness
    gate = client.get("/api/kb/auth/admin-gate")
    assert gate.status_code == 401
    store.create_account("alice", "pw", ROLE_USER_ID)
    assert _login(client, "alice", "pw").status_code == 200
    me = client.get("/api/kb/auth/me").json()
    assert "进管理模块" not in (me.get("permissions") or [])
    assert client.get("/api/kb/auth/admin-gate").status_code == 403
    assert client.get("/api/kb/heatmap").status_code == 200
    assert client.get("/api/kb/admin/heatmap").status_code == 403
    client.post("/api/kb/auth/logout")

    _make_mingxi(store)
    assert _login(client, "mingxi", "pw").status_code == 200
    assert client.get("/api/kb/auth/admin-gate").status_code == 204
    rounds = client.get("/api/kb/rounds")
    assert rounds.status_code == 200
    assert client.put("/api/kb/config", json={"recall_k": 8}).status_code == 403
    assert client.post("/api/kb/reindex").status_code == 403
    assert client.get("/api/kb/admin/conversations").status_code == 403
    assert client.get("/api/kb/heatmap").status_code == 403
    assert client.get("/api/kb/admin/heatmap").status_code == 403


def test_create_user_disable_last_super_unlock(harness):
    client, store = harness
    assert _login(client, "admin", "secret").status_code == 200
    created = client.post("/api/kb/admin/accounts", json={
        "username": "bob",
        "password": "init-pw",
        "role_id": ROLE_USER_ID,
    })
    assert created.status_code == 200
    bob_id = created.json()["id"]
    client.post("/api/kb/auth/logout")
    login = _login(client, "bob", "init-pw")
    assert login.status_code == 200
    me = client.get("/api/kb/auth/me")
    assert me.status_code == 200
    assert me.json()["id"] == bob_id
    bob_client = TestClient(main.app)
    assert _login(bob_client, "bob", "init-pw").status_code == 200
    assert bob_client.get("/api/kb/auth/me").status_code == 200

    assert _login(client, "admin", "secret").status_code == 200
    disabled = client.patch(f"/api/kb/admin/accounts/{bob_id}", json={"enabled": False})
    assert disabled.status_code == 200
    assert bob_client.get("/api/kb/auth/me").status_code == 401

    assert _login(client, "admin", "secret").status_code == 200
    admin_id = client.get("/api/kb/auth/me").json()["id"]
    last = client.patch(f"/api/kb/admin/accounts/{admin_id}", json={"enabled": False})
    assert last.status_code == 403
    assert store.count_enabled_super() >= 1
    assert client.patch(f"/api/kb/admin/accounts/{bob_id}", json={"enabled": True}).status_code == 200
    client.post("/api/kb/auth/logout")

    for _ in range(5):
        client.post("/api/kb/auth/login", json={"username": "bob", "password": "wrong"})
    assert client.post("/api/kb/auth/login", json={"username": "bob", "password": "init-pw"}).status_code == 401
    assert _login(client, "admin", "secret").status_code == 200
    assert client.post("/api/kb/admin/unlock", json={"username": "bob"}).status_code == 200
    client.post("/api/kb/auth/logout")
    ok = _login(client, "bob", "init-pw")
    assert ok.status_code == 200
    assert client.post("/api/kb/admin/unlock", json={"username": "x"}).status_code == 403


def test_conv_audit_all_ids(harness):
    client, store = harness
    store.create_account("alice", "pw", ROLE_USER_ID)
    store.create_account("carol", "pw", ROLE_USER_ID)
    assert _login(client, "alice", "pw").status_code == 200
    c1 = client.post("/api/kb/conversations", json={"title": "a"}).json()["id"]
    client.post("/api/kb/auth/logout")
    assert _login(client, "carol", "pw").status_code == 200
    c2 = client.post("/api/kb/conversations", json={"title": "b"}).json()["id"]
    assert client.get("/api/kb/admin/conversations").status_code == 403
    client.post("/api/kb/auth/logout")
    assert _login(client, "admin", "secret").status_code == 200
    ids = {x["id"] for x in client.get("/api/kb/admin/conversations").json()["items"]}
    assert {c1, c2} <= ids


def test_heatmap_perm_and_heat_chips_static():
    assert "if (!state.me || !hasPerm(\"知识问答\"))" in QA_JS
    assert "slice(0, 4)" in QA_JS
    titles = QA_JS.split("CHIP_FIXED = [")[1].split("];")[0]
    assert titles.count("title:") == 4
