# -*- coding: utf-8 -*-
"""M7 A13 / A14：知识来源只读、索引任务不重叠、记忆覆盖与回填。"""
from __future__ import annotations

from pathlib import Path

from app import main
from app.index_tasks import IndexTaskBook, MemoryTaskRepo
from app.memory_index import MemoryRecordRepo
from app.msg_store import MemoryMsgRepo, MsgStore
from app.util import sha256_text
from tests.test_auth_m1 import _login, harness  # noqa: F401
from tests.test_m3_admin_base import _role_user


def _ready(monkeypatch):
    monkeypatch.setattr(main, "missing_keys", lambda: [])
    monkeypatch.setattr(main.store, "ping", lambda: True)


def _tasks(monkeypatch):
    book = IndexTaskBook(MemoryTaskRepo())
    monkeypatch.setattr(main, "index_tasks", book)
    return book


def test_a13_t41_chunk_is_slice_not_whole_prd(harness, monkeypatch):
    client, _store = harness

    class _Chunk:
        path = "prd/design/demo/brief/current.md"
        feature_id = "demo"
        chunk_id = "demo.0"
        heading = "范围"
        anchor = "demo"
        collection = "hayyo-client"
        content_hash = "abc123"
        oversized = False

    monkeypatch.setattr("app.chunking.scan_briefs", lambda *a, **k: [_Chunk()])
    assert _login(client, "admin", "secret").status_code == 200
    resp = client.get("/api/kb/admin/knowledge-sources")
    assert resp.status_code == 200
    item = resp.json()["items"][0]
    assert item["integrity"] == "切片"
    assert "不是整份" in item["integrity_note"]
    assert "生效日期" in item["hash_note"]
    assert item["source_version"] == "未提供"
    assert "effective_date" not in item


def test_a13_t42_reject_arbitrary_path(harness, monkeypatch):
    client, store = harness
    assert _login(client, "admin", "secret").status_code == 200
    denied = client.get("/api/kb/admin/knowledge-sources", params={"path": "/etc/passwd"})
    assert denied.status_code == 400 and denied.json()["code"] == "source_rejected"
    walk = client.get("/api/kb/admin/knowledge-sources", params={"path": "../../etc/passwd"})
    assert walk.status_code == 400
    added = client.post("/api/kb/admin/knowledge-sources", json={"path": "/tmp/secret.md"})
    assert added.status_code == 400 and added.json()["code"] == "source_rejected"
    _role_user(store, "无来源权", ["问答明细"], "reader")
    assert _login(client, "reader", "pw").status_code == 200
    assert client.get("/api/kb/admin/knowledge-sources").status_code == 403


def test_a13_t43_partial_failure_kept(harness, monkeypatch):
    client, _store = harness
    _tasks(monkeypatch)
    _ready(monkeypatch)

    async def _rebuild():
        return {
            "scanned": 2,
            "changed": [],
            "failed": [{
                "path": "prd/design/demo/brief/current.md",
                "chunk_id": "demo.9",
                "action": "失败",
                "reason": "超过上限，该块不入库、不二次切、不截断",
            }],
            "chunk_count": 1,
        }

    monkeypatch.setattr(main.indexer, "rebuild", _rebuild)
    assert _login(client, "admin", "secret").status_code == 200
    resp = client.post("/api/kb/reindex")
    assert resp.status_code == 200
    body = resp.json()
    assert body["integrity"] == "partial" and body["complete"] is False
    assert body["failed"][0]["reason"] == "超过上限，该块不入库、不二次切、不截断"
    task = client.get(f"/api/kb/admin/index-tasks/{body['task_id']}")
    assert task.status_code == 200
    assert task.json()["integrity"] == "partial"
    assert "不截断" in str(task.json()["detail"])


def test_a13_t47_t100_overlap_and_retry(harness, monkeypatch):
    client, _store = harness
    book = _tasks(monkeypatch)
    _ready(monkeypatch)
    calls = {"n": 0}

    async def _rebuild():
        calls["n"] += 1
        return {"scanned": 1, "changed": [{"path": "p", "chunk_id": "c", "action": "增"}], "failed": [], "chunk_count": 1}

    monkeypatch.setattr(main.indexer, "rebuild", _rebuild)
    running, _hit = book.accept("knowledge", "rebuild", "all", "actor")
    assert _login(client, "admin", "secret").status_code == 200
    blocked = client.post("/api/kb/reindex")
    assert blocked.status_code == 409
    assert blocked.json()["code"] == "task_overlap"
    assert blocked.json()["task_id"] == running["id"]
    assert calls["n"] == 0
    book.finish(running["id"], "done", scanned=1)
    parent_before = book.get(running["id"])
    again = client.post(f"/api/kb/admin/index-tasks/{running['id']}/retry")
    assert again.status_code == 200
    body = again.json()
    assert body["task"]["parent_id"] == running["id"]
    assert body["task"]["id"] != running["id"]
    assert body["parent"]["status"] == "done"
    assert parent_before["status"] == "done"
    assert calls["n"] == 1


def test_a14_t44_hole_is_partial(harness, monkeypatch):
    client, store = harness
    repo = MemoryRecordRepo()
    monkeypatch.setattr(main.mem_index, "records", repo)
    monkeypatch.setattr(main.mem_index, "connected", True)
    msgs = MsgStore(MemoryMsgRepo())
    monkeypatch.setattr(main, "msgs", msgs)
    acc = store.repo.get_account_by_username("admin")
    conv = main.convs.create(acc["id"], {"title": "覆盖"})
    rows = [main.msgs.append_user(conv["id"], text, f"cr-{i}", f"ex-{i}") for i, text in enumerate(["甲", "乙", "丙"])]
    for row in (rows[0], rows[2]):
        repo.upsert({
            "msg_id": row["id"], "conv_id": conv["id"], "seq": int(row["seq"]),
            "status": "indexed", "content_hash": sha256_text(row["content"]), "gen": 1,
        })
    assert _login(client, "admin", "secret").status_code == 200
    cov = client.get("/api/kb/admin/memory-coverage", params={"conv_id": conv["id"]})
    assert cov.status_code == 200
    body = cov.json()
    assert body["state"] == "partial"
    assert body["holes"]
    assert "乙" not in cov.text


def test_a14_t45_missing_time_is_limited(harness, monkeypatch):
    client, store = harness
    monkeypatch.setattr(main.mem_index, "records", MemoryRecordRepo())
    monkeypatch.setattr(main.mem_index, "connected", True)
    msgs = MsgStore(MemoryMsgRepo())
    monkeypatch.setattr(main, "msgs", msgs)
    acc = store.repo.get_account_by_username("admin")
    conv = main.convs.create(acc["id"], {"title": "旧"})
    row = main.msgs.append_user(conv["id"], "旧问题", "cr-old", "ex-old")
    for item in msgs.repo.rows:
        if item["id"] == row["id"]:
            item["created_at"] = None
    assert _login(client, "admin", "secret").status_code == 200
    cov = client.get("/api/kb/admin/memory-coverage", params={"conv_id": conv["id"]})
    body = cov.json()
    assert body["quality"] == "受限"
    assert "完整原文" in body["quality_note"]
    assert "localStorage" not in cov.text
    assert "旧问题" not in cov.text


def test_a14_t46_backfill_keeps_hidden(harness, monkeypatch):
    client, store = harness
    _tasks(monkeypatch)
    monkeypatch.setattr(main.mem_index, "connected", False)
    monkeypatch.setattr(main.mem_index, "connect_error", "not_connected")
    acc = store.repo.get_account_by_username("admin")
    conv = main.convs.create(acc["id"], {"title": "已隐藏"})
    assert main.convs.delete(acc["id"], conv["id"]) is True
    assert _login(client, "admin", "secret").status_code == 200
    resp = client.post("/api/kb/admin/memory-backfill", json={"conv_id": conv["id"]})
    assert resp.status_code == 200
    assert "不恢复" in resp.json()["note"]
    row = main.convs.repo.get(conv["id"])
    assert row.get("hidden_at")
    assert row.get("purged_at") in (None, "")
    assert client.get(f"/api/kb/conversations/{conv['id']}").status_code == 404
    cov = client.get("/api/kb/admin/memory-coverage", params={"conv_id": conv["id"]})
    assert cov.status_code == 200
    assert cov.json()["state"] == "not_connected"
    assert cov.json()["backlog"] is None


def test_a14_t48_no_manual_complete_and_no_stale_text(harness, monkeypatch):
    client, store = harness
    repo = MemoryRecordRepo()
    monkeypatch.setattr(main.mem_index, "records", repo)
    monkeypatch.setattr(main.mem_index, "connected", True)
    msgs = MsgStore(MemoryMsgRepo())
    monkeypatch.setattr(main, "msgs", msgs)
    acc = store.repo.get_account_by_username("admin")
    conv = main.convs.create(acc["id"], {"title": "残留"})
    repo.upsert({
        "msg_id": "ghost", "conv_id": conv["id"], "seq": 9,
        "status": "indexed", "content_hash": "nope", "gen": 1,
    })
    assert _login(client, "admin", "secret").status_code == 200
    cov = client.get("/api/kb/admin/memory-coverage", params={"conv_id": conv["id"]})
    assert "ghost" in cov.json()["stale_ids"]
    assert "content" not in cov.json()
    banned = client.post("/api/kb/admin/memory-coverage/complete")
    assert banned.status_code == 400
    assert banned.json()["code"] == "manual_complete_forbidden"
    js = Path(__file__).resolve().parents[2].joinpath("kb-admin", "admin.js").read_text(encoding="utf-8")
    assert "设为完整" not in js
    assert "回填这个会话" in js
