# -*- coding: utf-8 -*-
"""M7 A17：轻量问题记录。不扩原文权限，不改赞踩，来源删除后摘录失效。"""
from __future__ import annotations

from app import main
from app.issues import IssueBook, MemoryIssueRepo
from app.msg_store import MemoryMsgRepo, MsgStore
from app.purge import MemoryPurgeRepo, PurgeBook
from tests.test_auth_m1 import _login, harness  # noqa: F401
from tests.test_m2_exec_versions import FakeLogs
from tests.test_m3_admin_base import _role_user

SECRET = "问题来源原文"


def _book(monkeypatch):
    book = IssueBook(MemoryIssueRepo())
    monkeypatch.setattr(main, "issues", book)
    return book


def _create(client, **extra):
    body = {"title": "退款答非所问", "category": "route"}
    body.update(extra)
    return client.post("/api/kb/admin/issues", json=body)


def test_a17_t61_assign_does_not_grant_source(harness, monkeypatch):
    """处理人没有原文权限时，只看到管理信息，角色权限不变。"""
    client, store = harness
    _book(monkeypatch)
    assert _login(client, "admin", "secret").status_code == 200
    _role_user(store, "只处理问题", ["问题处理"], "handler")
    handler = store.repo.get_account_by_username("handler")
    before = store.role_perm_set(handler["role_id"])
    made = _create(client, symptom="管理员自己写的现象", content=SECRET, excerpt=SECRET, conv_id="c-nope")
    assert made.status_code == 200
    assert SECRET not in made.text
    assert made.json()["symptom"] == "管理员自己写的现象"
    assert "content" not in made.json()
    issue_id = made.json()["id"]
    assigned = client.post(f"/api/kb/admin/issues/{issue_id}", json={"assignee_id": handler["id"]})
    assert assigned.status_code == 200
    assert store.role_perm_set(handler["role_id"]) == before
    assert "对话审计" not in before
    assert _login(client, "handler", "pw").status_code == 200
    detail = client.get(f"/api/kb/admin/issues/{issue_id}")
    assert detail.status_code == 200
    body = detail.json()
    assert body["assignee_id"] == handler["id"]
    assert "content" not in body and "excerpt" not in body
    assert client.get("/api/kb/admin/conversations/c-nope").status_code == 403


def test_a17_t62_publish_does_not_close(harness, monkeypatch):
    client, _store = harness
    book = _book(monkeypatch)
    assert _login(client, "admin", "secret").status_code == 200
    issue_id = _create(client).json()["id"]
    book.on_publish("pkg-1")
    still = client.get(f"/api/kb/admin/issues/{issue_id}").json()
    assert still["status"] == "open"
    denied = client.post(f"/api/kb/admin/issues/{issue_id}", json={
        "status": "closed", "close_reason": "verified", "close_basis": "看过一眼", "retested": False,
    })
    assert denied.status_code == 400
    assert "复测" in denied.json()["message"]
    assert client.get(f"/api/kb/admin/issues/{issue_id}").json()["status"] == "open"


def test_a17_t63_reopen_keeps_notes(harness, monkeypatch):
    client, _store = harness
    _book(monkeypatch)
    assert _login(client, "admin", "secret").status_code == 200
    issue_id = _create(client).json()["id"]
    note = client.post(f"/api/kb/admin/issues/{issue_id}/notes", json={"text": "先看执行记录"})
    assert note.status_code == 200
    closed = client.post(f"/api/kb/admin/issues/{issue_id}", json={
        "status": "closed", "close_reason": "not_defect", "close_basis": "复现不到",
    })
    assert closed.status_code == 200 and closed.json()["status"] == "closed"
    opened = client.post(f"/api/kb/admin/issues/{issue_id}", json={
        "status": "open", "reopen_reason": "用户又遇到了",
    })
    assert opened.status_code == 200 and opened.json()["status"] == "open"
    texts = [n["body"] for n in opened.json()["notes"]]
    assert "先看执行记录" in texts
    assert any("重新打开" in t for t in texts)
    assert opened.json()["close_reason"] in (None, "")


def test_a17_t64_purge_invalidates_excerpt(harness, monkeypatch):
    """来源被实际删除后，摘录清空并标来源已删除，问题行还在。"""
    client, store = harness
    book = _book(monkeypatch)
    msgs = MsgStore(MemoryMsgRepo())
    monkeypatch.setattr(main, "msgs", msgs)
    monkeypatch.setattr(main, "logs", FakeLogs())
    monkeypatch.setattr(main, "purge_book", PurgeBook(MemoryPurgeRepo()))
    monkeypatch.setattr(main, "mem_index", type("I", (), {"delete_conversation": lambda self, cid: None})())
    acc = store.repo.get_account_by_username("admin")
    conv = main.convs.create(acc["id"], {"title": "待删"})
    main.msgs.append_user(conv["id"], SECRET, "cr-i", "ex-i")
    assert _login(client, "admin", "secret").status_code == 200
    made = _create(client, title="关联会话", symptom=SECRET, source_type="conv", source_id=conv["id"], conv_id=conv["id"])
    issue_id = made.json()["id"]
    assert _purge_ok(client, conv["id"])
    detail = client.get(f"/api/kb/admin/issues/{issue_id}")
    assert detail.status_code == 200
    body = detail.json()
    assert body["source_deleted"] is True
    assert body["source_note"] == "来源已删除"
    assert body["symptom"] == ""
    assert SECRET not in detail.text
    assert book.get(issue_id)["title"] == "来源已删除"


def _purge_ok(client, conv_id: str) -> bool:
    resp = client.post(f"/api/kb/admin/conversations/{conv_id}/purge", json={"confirm": conv_id})
    return resp.status_code == 200


def test_a17_other_perm_forbidden(harness, monkeypatch):
    client, store = harness
    _book(monkeypatch)
    _role_user(store, "只有明细", ["问答明细"], "reader")
    assert _login(client, "reader", "pw").status_code == 200
    assert client.get("/api/kb/admin/issues").status_code == 403
    assert client.post("/api/kb/admin/issues", json={"title": "x"}).status_code == 403
