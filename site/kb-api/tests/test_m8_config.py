# -*- coding: utf-8 -*-
"""M8 A08：草稿不生效，发布才切换；回退是一次新发布。"""
from __future__ import annotations

import threading

from app import main
from app.config_store import ConfigConflict, ConfigStore
from tests.test_auth_m1 import _login, harness  # noqa: F401


def _store(monkeypatch, tmp_path):
    store = ConfigStore(tmp_path / "kb-config.json")
    monkeypatch.setattr(main, "config_store", store)
    return store


def test_a08_t24_draft_does_not_change_live(harness, monkeypatch, tmp_path):
    client, _s = harness
    store = _store(monkeypatch, tmp_path)
    live = store.data["recall_k"]
    assert _login(client, "admin", "secret").status_code == 200
    saved = client.put("/api/kb/config", json={"recall_k": live + 3})
    assert saved.status_code == 200
    assert store.data["recall_k"] == live
    assert saved.json()["draft"]["recall_k"] == live + 3
    assert saved.json()["package_id"] == store.package_id
    bound = store.accept_config()
    assert bound["recall_k"] == live


def test_a08_t87_second_publish_conflicts(harness, monkeypatch, tmp_path):
    client, _s = harness
    store = _store(monkeypatch, tmp_path)
    assert _login(client, "admin", "secret").status_code == 200
    draft = client.put("/api/kb/config", json={"recall_k": 6})
    rev = draft.json()["draft_rev"]
    first = client.post("/api/kb/config/publish", json={"rev": rev, "op_id": "pub-a"})
    assert first.status_code == 200
    second = client.post("/api/kb/config/publish", json={"rev": rev, "op_id": "pub-b"})
    assert second.status_code == 409
    assert second.json()["code"] == "publish_conflict"
    assert store.package_id == first.json()["package_id"]


def test_a08_t87_concurrent_one_wins(tmp_path):
    store = ConfigStore(tmp_path / "kb-config.json")
    store.save_draft({"recall_k": 4})
    rev = store.draft_rev
    results = []

    def go():
        try:
            results.append(("ok", store.publish(rev, None)))
        except (ConfigConflict, ValueError) as exc:
            results.append(("err", type(exc).__name__))

    threads = [threading.Thread(target=go) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert len([r for r in results if r[0] == "ok"]) == 1
    assert store.data["recall_k"] == 4


def test_a08_t88_inflight_keeps_old_package(harness, monkeypatch, tmp_path):
    client, _s = harness
    store = _store(monkeypatch, tmp_path)
    bound = store.accept_config()
    assert _login(client, "admin", "secret").status_code == 200
    rev = client.put("/api/kb/config", json={"recall_k": bound["recall_k"] + 2}).json()["draft_rev"]
    pub = client.post("/api/kb/config/publish", json={"rev": rev})
    assert pub.status_code == 200
    assert bound["recall_k"] != store.data["recall_k"]
    assert store.packages[bound["_package_id"]]["recall_k"] == bound["recall_k"]
    assert store.accept_config()["recall_k"] == store.data["recall_k"]


def test_a08_t89_incompatible_rollback_rejected(harness, monkeypatch, tmp_path):
    client, _s = harness
    store = _store(monkeypatch, tmp_path)
    current = store.package_id
    store.history.append({"id": "old-40", "data": {"max_conversations": 40, "recall_k": 1}})
    assert _login(client, "admin", "secret").status_code == 200
    denied = client.post("/api/kb/config/rollback", json={"package_id": "old-40"})
    assert denied.status_code == 400
    assert denied.json()["code"] == "incompatible"
    assert store.package_id == current


def test_a08_t90_repeat_op_does_not_republish(harness, monkeypatch, tmp_path):
    client, _s = harness
    store = _store(monkeypatch, tmp_path)
    assert _login(client, "admin", "secret").status_code == 200
    rev = client.put("/api/kb/config", json={"recall_k": 9}).json()["draft_rev"]
    first = client.post("/api/kb/config/publish", json={"rev": rev, "op_id": "same-op"})
    assert first.status_code == 200
    pid = first.json()["package_id"]
    hist = len(store.history)
    again = client.post("/api/kb/config/publish", json={"rev": rev, "op_id": "same-op"})
    assert again.status_code == 200
    assert again.json()["repeated"] is True
    assert again.json()["package_id"] == pid
    assert store.package_id == pid
    assert len(store.history) == hist
