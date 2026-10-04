"""迁移保护：文件缺失时不得把空扫描当成合法删库请求。"""
import asyncio
import json
from pathlib import Path

import pytest

from app import indexer, settings
from app.chunking import scan_briefs
from app.tls_store import TlsStore


def corpus(root, features=("vip",)):
    prd = root / "prd"
    prd.mkdir(parents=True, exist_ok=True)
    (prd / "llm-manifest.json").write_text(json.dumps({
        "scan_roots": [f"site/core-docs/prd/design/{fid}/PRD.md" for fid in features]
    }))
    for fid in features:
        folder = prd / "design" / fid
        (folder / "brief").mkdir(parents=True)
        (folder / "PRD.md").write_text("# 权威正文\n")
        (folder / "brief/current.md").write_text(
            f"# 规则 {{#scope}}\n<!-- chunk:default section=scope id={fid}.scope -->\n正文保持不变。\n"
        )
    return root


def test_default_core_docs_root_matches_local_authority():
    expected = Path(__file__).resolve().parents[3] / "site/core-docs"
    assert getattr(settings, "CORE_DOCS_ROOT", None) == expected


@pytest.mark.parametrize("condition", ["missing", "empty", "missing_brief", "no_chunks", "duplicate_ids", "escaped_symlink"])
def test_invalid_corpus_is_an_error(tmp_path, condition):
    root = tmp_path / "core-docs"
    if condition != "missing":
        corpus(root, () if condition == "empty" else ("vip", "admin"))
        brief = root / "prd/design/vip/brief/current.md"
        if condition == "missing_brief":
            brief.unlink()
        elif condition == "no_chunks":
            brief.write_text("# 文件还在，但正文未完整复制\n")
        elif condition == "duplicate_ids":
            brief.write_text(brief.read_text() * 2)
        elif condition == "escaped_symlink":
            outside = tmp_path / "outside.md"
            outside.write_text(brief.read_text())
            brief.unlink()
            brief.symlink_to(outside)
    with pytest.raises(RuntimeError, match="语料"):
        scan_briefs(root)


def test_moved_corpus_keeps_logical_paths(tmp_path):
    chunks = scan_briefs(corpus(tmp_path / "core-docs"))
    assert [(c.path, c.chunk_id) for c in chunks] == [("prd/design/vip/brief/current.md", "vip.scope")]


def test_empty_scan_never_touches_vector_store(monkeypatch):
    calls = []

    class Store:
        def ensure_collections(self): calls.append("ensure")
        def existing_points(self): return {"prd/old.md::vip.scope": {"collection": "hayyo-client", "payload": {}}}
        def delete_point(self, *args): calls.append("delete")
        def rebuild_bm25_from_qdrant(self): calls.append("bm25")
        def chunk_count(self): return 1

    async def embed(texts):
        calls.append("embed")
        return []

    monkeypatch.setattr(indexer, "scan_briefs", lambda: [])
    with pytest.raises(RuntimeError, match="语料"):
        asyncio.run(indexer.Indexer(Store(), embed).rebuild())
    assert calls == []


def test_tls_uses_dedicated_directory(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "TLS_DIR", tmp_path / "tls", raising=False)
    assert TlsStore().root == tmp_path / "tls"


def test_tls_migration_is_allowlisted_and_preserves_newer_certificate(tmp_path):
    legacy, target = tmp_path / "data", tmp_path / "tls"
    legacy.mkdir()
    for name in ("cert.pem", "key.pem", "pending-cert.pem", "pending-key.pem", "state.json", "https.enabled"):
        (legacy / name).write_text("old-" + name)
    (legacy / "kb-config.json").write_text("private config")
    store = TlsStore(target)
    assert callable(getattr(store, "migrate_legacy", None)), "TLS migration is required before Web starts"
    store.migrate_legacy(legacy)
    assert (target / "key.pem").read_text() == "old-key.pem"
    assert (target / "pending-key.pem").read_text() == "old-pending-key.pem"
    assert not (target / "kb-config.json").exists()
    assert (legacy / "key.pem").read_text() == "old-key.pem"
    (target / "key.pem").write_text("new active key")
    store.migrate_legacy(legacy)
    assert (target / "key.pem").read_text() == "new active key"


def test_tls_migration_conflict_preserves_both_directories(tmp_path):
    legacy, target = tmp_path / "data", tmp_path / "tls"
    legacy.mkdir()
    target.mkdir()
    (legacy / "cert.pem").write_text("old cert")
    (legacy / "key.pem").write_text("old key")
    (target / "key.pem").write_text("different key")
    with pytest.raises(RuntimeError, match="冲突"):
        TlsStore(target).migrate_legacy(legacy)
    assert not (target / "cert.pem").exists()
    assert not (target / ".legacy-migrated").exists()
    assert (target / "key.pem").read_text() == "different key"
    assert (legacy / "key.pem").read_text() == "old key"


def test_tls_migration_can_resume_partial_copy(tmp_path):
    legacy, target = tmp_path / "data", tmp_path / "tls"
    legacy.mkdir()
    target.mkdir()
    (legacy / "cert.pem").write_text("cert")
    (target / "cert.pem").write_text("cert")
    (legacy / "key.pem").write_text("key")
    TlsStore(target).migrate_legacy(legacy)
    assert (target / "key.pem").read_text() == "key"
    assert (target / ".legacy-migrated").is_file()
