# -*- coding: utf-8 -*-
"""M7 A06：超管单会话实际删除。用户删除仍只隐藏。"""
from __future__ import annotations

from app import main
from app.auth_store import AuditUnavailable
from app.msg_store import MemoryMsgRepo, MsgStore
from app.purge import MemoryPurgeRepo, PurgeBook
from tests.test_auth_m1 import _login, harness  # noqa: F401
from tests.test_m2_exec_versions import FakeLogs
from tests.test_m3_admin_base import _role_user

SECRET = "机密删除正文"


class _Index:
    def __init__(self) -> None:
        self.deleted: list[str] = []
        self.fail = False

    def delete_conversation(self, conv_id: str) -> None:
        if self.fail:
            raise RuntimeError("index down")
        self.deleted.append(conv_id)


def _wire(monkeypatch):
    msgs = MsgStore(MemoryMsgRepo())
    book = PurgeBook(MemoryPurgeRepo())
    index = _Index()
    logs = FakeLogs()
    monkeypatch.setattr(main, "msgs", msgs)
    monkeypatch.setattr(main, "purge_book", book)
    monkeypatch.setattr(main, "mem_index", index)
    monkeypatch.setattr(main, "logs", logs)
    return msgs, book, index, logs


def _seed(store):
    acc = store.repo.get_account_by_username("admin")
    conv = main.convs.create(acc["id"], {"title": "待删会话"})
    user = main.msgs.append_user(conv["id"], SECRET, "cr-purge", "ex-purge")
    main.msgs.append_assistant(conv["id"], user, "ex-purge", SECRET + "答", "complete")
    main.logs.insert_running({"round_id": "ex-purge", "conv_id": conv["id"], "status": "running"})
    return conv


def _purge(client, conv_id: str):
    return client.post(
        f"/api/kb/admin/conversations/{conv_id}/purge",
        json={"confirm": conv_id},
    )


def test_a06_t08_audit_perm_cannot_purge(harness, monkeypatch):
    """T08 / AT-25：对话审计不能实际删除，原文仍在。"""
    client, store = harness
    _wire(monkeypatch)
    conv = _seed(store)
    _role_user(store, "对话审计员", ["对话审计"], "auditor")
    assert _login(client, "auditor", "pw").status_code == 200
    denied = _purge(client, conv["id"])
    assert denied.status_code == 403
    assert SECRET not in denied.text
    assert client.get("/api/kb/admin/purge-ops/missing").status_code == 403
    detail = client.get(f"/api/kb/admin/conversations/{conv['id']}")
    assert detail.status_code == 200
    assert SECRET in detail.text
    assert main.convs.repo.get(conv["id"]).get("purged_at") in (None, "")


def test_purge_barrier_failure_is_recorded_before_any_facts_are_deleted(harness, monkeypatch):
    client, store = harness
    _wire(monkeypatch)
    conv = _seed(store)
    _login(client, 'admin', 'secret')
    monkeypatch.setattr(main.convs, 'mark_purged', lambda _: (_ for _ in ()).throw(OSError('database unavailable')))
    result = _purge(client, conv['id'])
    assert result.status_code == 503
    operation = main.purge_book.for_conv(conv['id'])
    assert operation['status'] == 'partial'
    assert operation['facts'] == 'failed'
    assert operation['error'] == 'barrier_failed'
    assert SECRET in client.get('/api/kb/admin/conversations/' + conv['id']).text


def test_a06_need_confirm(harness, monkeypatch):
    client, store = harness
    _wire(monkeypatch)
    conv = _seed(store)
    assert _login(client, "admin", "secret").status_code == 200
    bad = client.post(f"/api/kb/admin/conversations/{conv['id']}/purge", json={})
    assert bad.status_code == 400
    assert bad.json()["code"] == "need_confirm"
    assert SECRET in client.get(f"/api/kb/admin/conversations/{conv['id']}").text


def test_a06_c27_purge_idempotent_and_indexed(harness, monkeypatch):
    """C27：先不可读，再删事实与记忆索引；重复点击不重做。"""
    client, store = harness
    _msgs, _book, index, logs = _wire(monkeypatch)
    conv = _seed(store)
    assert _login(client, "admin", "secret").status_code == 200
    first = _purge(client, conv["id"])
    assert first.status_code == 200
    body = first.json()
    assert body["status"] == "done"
    assert body["facts"] == "deleted"
    assert body["derived"] == "deleted"
    assert SECRET not in first.text
    assert index.deleted == [conv["id"]]
    again = _purge(client, conv["id"])
    assert again.status_code == 200
    assert again.json()["id"] == body["id"]
    assert index.deleted == [conv["id"]]
    assert logs.rows == {}
    assert main.msgs.admin_messages(conv["id"]) == []
    detail = client.get(f"/api/kb/admin/conversations/{conv['id']}")
    assert detail.status_code == 404
    assert SECRET not in detail.text
    listed = client.get("/api/kb/admin/conversations")
    assert conv["id"] not in listed.text
    got = client.get(f"/api/kb/admin/purge-ops/{body['id']}")
    assert got.status_code == 200
    assert got.json()["id"] == body["id"]
    assert SECRET not in got.text


def test_a06_t09_late_write_does_not_restore(harness, monkeypatch):
    """T09：删除后晚到的回答写回不再带出原文。"""
    client, store = harness
    _wire(monkeypatch)
    conv = _seed(store)
    assert _login(client, "admin", "secret").status_code == 200
    assert _purge(client, conv["id"]).status_code == 200
    row = main._write_reply(
        conv["id"],
        {"round_id": "r-late", "id": "u-late"},
        "ex-late",
        {"content": SECRET, "completeness": "complete", "op_type": "send"},
    )
    assert row.get("_purged") is True
    assert main.msgs.admin_messages(conv["id"]) == []
    user = client.get(f"/api/kb/conversations/{conv['id']}")
    assert user.status_code == 404
    assert SECRET not in user.text


def test_a06_audit_unavailable_refuses(harness, monkeypatch):
    client, store = harness
    _wire(monkeypatch)
    conv = _seed(store)
    assert _login(client, "admin", "secret").status_code == 200

    def _boom(*_a, **_k):
        raise AuditUnavailable("down")

    monkeypatch.setattr(main.auth, "begin_audit", _boom)
    denied = _purge(client, conv["id"])
    assert denied.status_code == 503
    assert denied.json()["code"] == "audit_unavailable"
    assert main.convs.repo.get(conv["id"]).get("purged_at") in (None, "")
    assert SECRET in client.get(f"/api/kb/admin/conversations/{conv['id']}").text


def test_a06_user_delete_stays_hide(harness, monkeypatch):
    """用户删除只隐藏，消息还在，不走实际删除。"""
    client, store = harness
    _wire(monkeypatch)
    conv = _seed(store)
    assert _login(client, "admin", "secret").status_code == 200
    gone = client.delete(f"/api/kb/conversations/{conv['id']}")
    assert gone.status_code == 200
    row = main.convs.repo.get(conv["id"])
    assert row.get("hidden_at")
    assert row.get("purged_at") in (None, "")
    assert any(SECRET in (m.get("content") or "") for m in main.msgs.admin_messages(conv["id"]))


def test_a06_derived_fail_stays_unreadable(harness, monkeypatch):
    client, store = harness
    _msgs, _book, index, _logs = _wire(monkeypatch)
    index.fail = True
    conv = _seed(store)
    assert _login(client, "admin", "secret").status_code == 200
    resp = _purge(client, conv["id"])
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "partial"
    assert body["facts"] == "deleted"
    assert body["derived"] == "failed"
    assert client.get(f"/api/kb/admin/conversations/{conv['id']}").status_code == 404
    assert SECRET not in resp.text
