#!/usr/bin/env python3
"""从明确清单生成 Web 根；不把仓库、site 或 core-docs 整目录公开。"""
import argparse
import hashlib
import json
import re
import shutil
import tempfile
from pathlib import Path, PurePosixPath


def safe_relative(value):
    path = PurePosixPath(value)
    if path.is_absolute() or not path.parts or any(part in {".", ".."} or part.startswith(".") for part in path.parts):
        raise ValueError(f"Unsafe publication path: {value}")
    return path.as_posix()


def source_file(root, relative):
    relative = safe_relative(relative)
    path = root / relative
    if any(p.is_symlink() for p in (path, *path.parents) if p != root and root in p.parents):
        raise ValueError(f"Publication refuses symlink: {relative}")
    if not path.is_file() or root not in path.resolve().parents:
        raise ValueError(f"Missing publication source: {relative}")
    return path


def build_site(repo_root):
    root = Path(repo_root).resolve()
    prefix = "site/core-docs/"
    sources = {}
    generated = {}

    def add(source, destination):
        destination = safe_relative(destination)
        if destination in sources:
            raise ValueError(f"Duplicate publication destination: {destination}")
        sources[destination] = source_file(root, source)

    policy = json.loads(source_file(root, "site/docker/publish-files.json").read_text())
    for source, destination in policy["static_files"].items():
        add(source, destination)
    manifest = json.loads(source_file(root, prefix + "prd/llm-manifest.json").read_text())

    def project(value):
        if not isinstance(value, str) or not value.startswith(prefix + "prd/"):
            raise ValueError(f"Manifest path outside core-docs: {value}")
        return safe_relative(value[len(prefix):])

    roots = manifest["scan_roots"]
    if not roots:
        raise ValueError("Empty product manifest")
    features = set()
    for source in roots:
        destination = project(source)
        # Default reading list contains current Markdown only; archives need a separate policy.
        if not re.fullmatch(r"prd/(?:[A-Z_]+\.md|inbox/INDEX\.md|design/[a-z0-9-]+/PRD\.md)", destination):
            raise ValueError(f"Not a current product document: {destination}")
        add(source, destination)
        match = re.fullmatch(r"prd/design/([a-z0-9-]+)/PRD\.md", destination)
        if match:
            features.add(match.group(1))
    if not features:
        raise ValueError("No product features in manifest")
    for feature in sorted(features):
        base = f"prd/design/{feature}"
        for name in ("brief/current.md", "changelog.md"):
            add(prefix + base + "/" + name, base + "/" + name)
        image_root = root / prefix / base / "images"
        for image in sorted(image_root.rglob("*")):
            if image.is_file() and image.suffix.lower() in {".png", ".jpeg", ".jpg", ".gif", ".webp"}:
                source = image.relative_to(root).as_posix()
                add(source, source[len(prefix):])
        history = []
        for path in sorted((root / prefix / base / "history").glob("*.md")):
            source = path.relative_to(root).as_posix()
            destination = source[len(prefix):]
            add(source, destination)
            history.append(destination)
        generated[base + "/history/index.json"] = {"files": history}
    manifest["scan_roots"] = [project(value) for value in roots]
    manifest.pop("exclude_roots", None)
    for doc in manifest.get("documents", []):
        doc["path"] = project(doc["path"])
        if doc["path"] not in sources:
            raise ValueError(f"Manifest references unpublished file: {doc['path']}")
    manifest["published_paths"] = sorted(set(sources) | set(generated) | {"prd/llm-manifest.json"})
    generated["prd/llm-manifest.json"] = manifest

    release = root / "site/release"
    www = release / "www"
    owner = release / ".hayyo-publish"
    if release.is_symlink() or www.is_symlink():
        raise ValueError("Publication destination must not be a symlink")
    if www.exists() and not owner.is_file():
        raise ValueError("Refusing to replace a directory not created by this publisher")
    release.mkdir(parents=True, exist_ok=True)
    backup = release / ".www-previous"
    if backup.exists():
        raise ValueError("Previous publish was interrupted; preserve and inspect .www-previous first")
    stage = Path(tempfile.mkdtemp(prefix=".www-", dir=release))
    stage.chmod(0o755)
    try:
        for destination, source in sources.items():
            target = stage / destination
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
        for destination, value in generated.items():
            target = stage / destination
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
        report = {"files": len(sources) + len(generated), "features": len(features), "paths": {}}
        for target in sorted(stage.rglob("*")):
            if target.is_file():
                report["paths"][target.relative_to(stage).as_posix()] = hashlib.sha256(target.read_bytes()).hexdigest()
        if www.exists():
            www.rename(backup)
        try:
            stage.rename(www)
        except OSError:
            if backup.exists():
                backup.rename(www)
            raise
        owner.write_text("Generated by site/scripts/build_site.py\n")
        (release / "publish-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        if backup.exists():
            shutil.rmtree(backup)
        return report
    finally:
        if stage.exists():
            shutil.rmtree(stage)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    result = build_site(args.repo_root)
    print(json.dumps({"files": result["files"], "features": result["features"], "output": "site/release/www"}))
