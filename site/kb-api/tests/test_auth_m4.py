# -*- coding: utf-8 -*-
"""M4：操作审计、反馈汇总、证书与 compose 80/443。"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

from app import main
from app.auth_store import ROLE_USER_ID
from tests.test_auth_m1 import _login, harness  # noqa: F401


ROOT = Path(__file__).resolve().parents[3]
ADMIN_JS = (ROOT / "site" / "kb-admin" / "admin.js").read_text(encoding="utf-8")
NGINX = (ROOT / "site" / "docker" / "nginx.conf").read_text(encoding="utf-8")
COMPOSE = (ROOT / "site" / "docker-compose.yml").read_text(encoding="utf-8")
INIT_SQL = (ROOT / "site" / "kb-api" / "sql" / "init.sql").read_text(encoding="utf-8")


def _pem_pair():
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "localhost")])
    now = datetime.now(timezone.utc)
    cert = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now)
        .not_valid_after(now + timedelta(days=1))
        .sign(key, hashes.SHA256())
    )
    cert_pem = cert.public_bytes(serialization.Encoding.PEM).decode("utf-8")
    key_pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")
    return cert_pem, key_pem


async def _fake_rebuild():
    return {"chunk_count": 1, "scanned": 0, "changed": [], "failed": []}


def test_audit_config_and_reindex(harness, monkeypatch):
    client, store = harness
    assert _login(client, "admin", "secret").status_code == 200
    me = client.get("/api/kb/auth/me").json()["id"]
    put = client.put("/api/kb/config", json={"recall_k": 12, "rerank_n": 3})
    assert put.status_code == 200
    monkeypatch.setattr(main, "missing_keys", lambda: [])
    monkeypatch.setattr(main.store, "ping", lambda: True)
    monkeypatch.setattr(main.indexer, "rebuild", _fake_rebuild)
    reindex = client.post("/api/kb/reindex")
    assert reindex.status_code == 200
    items = client.get("/api/kb/admin/audits").json()["items"]
    dumped = json.dumps(items, ensure_ascii=False)
    cfg = [x for x in items if x.get("action") == "config_update"]
    assert cfg
    assert set(cfg[0].get("detail", {}).get("fields") or []) == {"recall_k", "rerank_n"}
    assert "changeme" not in dumped
    assert "BEGIN " not in dumped
    assert "private" not in dumped.lower()
    re = [x for x in items if x.get("action") == "reindex"]
    assert re
    assert re[0].get("actor_id") == me or re[0].get("object") == me
    client.post("/api/kb/auth/logout")
    store.create_account("alice", "pw", ROLE_USER_ID)
    assert _login(client, "alice", "pw").status_code == 200
    assert client.get("/api/kb/admin/audits").status_code == 403


def test_feedback_summary(harness, monkeypatch):
    client, store = harness
    monkeypatch.setattr(main.logs, "list_rounds", lambda **k: [
        {"round_id": "r-up", "feedback": "up", "original_query": "a", "created_at": "t", "status": "success"},
        {"round_id": "r-down", "feedback": "down", "original_query": "b", "created_at": "t", "status": "success"},
    ])
    assert _login(client, "admin", "secret").status_code == 200
    data = client.get("/api/kb/admin/feedback-summary").json()
    down_ids = [x["round_id"] for x in data.get("down") or []]
    assert down_ids == ["r-down"]
    client.post("/api/kb/auth/logout")
    store.create_account("alice", "pw", ROLE_USER_ID)
    assert _login(client, "alice", "pw").status_code == 200
    assert client.get("/api/kb/admin/feedback-summary").status_code == 403
    assert "data-qa-fb" not in ADMIN_JS


def test_tls_save_enable_disable(harness, tmp_path, monkeypatch):
    client, store = harness
    monkeypatch.setattr(main.tls, "root", tmp_path)
    store.create_account("alice", "pw", ROLE_USER_ID)
    assert _login(client, "alice", "pw").status_code == 200
    assert client.get("/api/kb/admin/tls").status_code == 403
    client.post("/api/kb/auth/logout")
    assert _login(client, "admin", "secret").status_code == 200
    cert_pem, key_pem = _pem_pair()
    saved = client.post("/api/kb/admin/tls", json={"cert_pem": cert_pem, "key_pem": key_pem})
    assert saved.status_code == 200
    st = saved.json()
    assert st["enabled"] is False
    assert st["scheme"] == "http"
    assert st["redirect_https"] is False
    dumped = json.dumps(st)
    assert "BEGIN " not in dumped
    assert key_pem not in dumped
    garbage = client.post("/api/kb/admin/tls", json={
        "cert_pem": "-----BEGIN CERTIFICATE-----\nAAAA\n-----END CERTIFICATE-----",
        "key_pem": "-----BEGIN PRIVATE KEY-----\nBBBB\n-----END PRIVATE KEY-----",
    })
    assert garbage.status_code == 200
    bad = client.post("/api/kb/admin/tls/enable")
    assert bad.status_code == 400
    assert client.get("/api/kb/admin/tls").json()["enabled"] is False
    client.post("/api/kb/admin/tls", json={"cert_pem": cert_pem, "key_pem": key_pem})
    ok = client.post("/api/kb/admin/tls/enable")
    assert ok.status_code == 200
    assert ok.json()["enabled"] is True
    assert ok.json()["redirect_https"] is False
    off = client.post("/api/kb/admin/tls/disable")
    assert off.status_code == 200
    assert off.json()["enabled"] is False
    assert off.json()["scheme"] == "http"


def test_compose_tls_ports_and_no_port_panel():
    assert "0.0.0.0" not in COMPOSE
    assert "HAYYO_TLS_PORT:-18769" in COMPOSE
    assert "return 301 https://" in NGINX
    assert "$kb_std_port" in NGINX
    assert "HAYYO_WEB_PORT" not in ADMIN_JS
    assert "改端口" not in ADMIN_JS
    assert "CREATE TABLE IF NOT EXISTS kb_audit_logs" in INIT_SQL
    assert "CREATE TABLE IF NOT EXISTS qa_rounds" in INIT_SQL
    assert INIT_SQL.find("kb_audit_logs") != INIT_SQL.find("qa_rounds")
