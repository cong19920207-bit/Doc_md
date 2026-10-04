"""发布边界以独立临时仓库验证，禁止工作区/源码混入 Web 根。"""
import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[3]


def publisher():
    path = ROOT / "site/scripts/build_site.py"
    assert path.is_file(), "A controlled publication builder is required"
    spec = importlib.util.spec_from_file_location("build_site", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.build_site


def repository(root):
    def write(path, text):
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)
    write("site/docker/publish-files.json", json.dumps({"static_files": {"site/login/index.html": "login/index.html"}}))
    write("site/login/index.html", "login")
    write("site/login/tests/private.js", "private test")
    write("site/docs/internal.md", "internal")
    write("site/.env", "SECRET=private")
    write("site/kb-api/app/main.py", "private server")
    write("workspace/private.md", "private work")
    prefix = "site/core-docs/prd/"
    paths = [prefix + "INDEX.md", prefix + "design/vip/PRD.md"]
    write(prefix + "llm-manifest.json", json.dumps({"scan_roots": paths, "documents": [{"id": "vip", "path": paths[1]}]}))
    write(prefix + "INDEX.md", "# 文档")
    write(paths[1], "# VIP\n![image](images/a.png)")
    write(prefix + "design/vip/brief/current.md", "# 当前规则")
    write(prefix + "design/vip/changelog.md", "# 变更")
    write(prefix + "design/vip/images/a.png", "image")
    write(prefix + "design/vip/history/v1.md", "# 旧版")
    write(prefix + "design/vip/history/.env", "PRIVATE")
    write(prefix + "archive/private.md", "private archive")
    return root


def test_only_approved_files_and_projected_manifest_are_published(tmp_path):
    build = publisher()
    repo = repository(tmp_path)
    build(repo)
    www = repo / "site/release/www"
    assert (www / "login/index.html").is_file()
    assert (www / "prd/design/vip/images/a.png").read_text() == "image"
    assert (www / "prd/design/vip/brief/current.md").is_file()
    manifest = json.loads((www / "prd/llm-manifest.json").read_text())
    assert manifest["scan_roots"] == ["prd/INDEX.md", "prd/design/vip/PRD.md"]
    assert manifest["documents"][0]["path"] == "prd/design/vip/PRD.md"
    assert json.loads((www / "prd/design/vip/history/index.json").read_text()) == {"files": ["prd/design/vip/history/v1.md"]}
    for private in [".env", "site/.env", "docs/internal.md", "kb-api/app/main.py", "workspace/private.md", "login/tests/private.js", "prd/archive/private.md", "prd/design/vip/history/.env"]:
        assert not (www / private).exists(), private
    assert (repo / "site/.env").read_text() == "SECRET=private"


def test_rebuild_removes_stale_files_and_failed_build_preserves_previous_release(tmp_path):
    build = publisher()
    repo = repository(tmp_path)
    build(repo)
    www = repo / "site/release/www"
    (www / "stale-private.txt").write_text("should disappear")
    build(repo)
    assert not (www / "stale-private.txt").exists()
    (repo / "site/core-docs/prd/design/vip/brief/current.md").unlink()
    with pytest.raises((ValueError, RuntimeError, FileNotFoundError)):
        build(repo)
    assert (www / "prd/design/vip/brief/current.md").is_file()


def test_publisher_rejects_symlink_source(tmp_path):
    build = publisher()
    repo = repository(tmp_path)
    page = repo / "site/login/index.html"
    page.unlink()
    page.symlink_to(repo / "site/.env")
    with pytest.raises(ValueError, match="symlink"):
        build(repo)


def test_manifest_cannot_publish_outside_core_docs(tmp_path):
    build = publisher()
    repo = repository(tmp_path)
    manifest = repo / "site/core-docs/prd/llm-manifest.json"
    manifest.write_text(json.dumps({"scan_roots": ["workspace/private.md"], "documents": []}))
    with pytest.raises(ValueError):
        build(repo)
