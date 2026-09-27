# -*- coding: utf-8 -*-
"""只切 brief/current.md 的 chunk:default。"""
from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from pathlib import Path

from . import settings
from .aliases import collection_for
from .util import estimate_tokens, sha256_text

CHUNK_RE = re.compile(
    r"<!--\s*chunk:(default|no|related-row)(?P<attrs>[^>]*)-->",
    re.I,
)
ATTR_RE = re.compile(r"(\w+)=([^\s>]+)")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.M)
ANCHOR_IN_HEADING = re.compile(r"\{#([^}]+)\}\s*$")


@dataclass
class Chunk:
    path: str
    feature_id: str
    chunk_id: str
    section: str
    heading: str
    anchor: str
    content: str
    content_hash: str
    collection: str
    token_estimate: int
    oversized: bool

    def payload(self) -> dict:
        return {
            "path": self.path,
            "feature_id": self.feature_id,
            "chunk_id": self.chunk_id,
            "section": self.section,
            "heading": self.heading,
            "anchor": self.anchor,
            "content": self.content,
            "content_hash": self.content_hash,
            "collection": self.collection,
            "user_id": "",
            "owner_id": "",
            "tenant_id": "",
            "role": "",
        }

    def as_dict(self) -> dict:
        return asdict(self)


def _attrs(raw: str) -> dict[str, str]:
    return {m.group(1): m.group(2).strip() for m in ATTR_RE.finditer(raw or "")}


def _heading_before(text: str, pos: int) -> tuple[str, str]:
    prefix = text[:pos]
    matches = list(HEADING_RE.finditer(prefix))
    if not matches:
        return "", ""
    raw = matches[-1].group(2).strip()
    m = ANCHOR_IN_HEADING.search(raw)
    if m:
        return ANCHOR_IN_HEADING.sub("", raw).strip(), m.group(1)
    return raw, ""


def parse_brief(path: Path, repo_root: Path, feature_id: str) -> list[Chunk]:
    text = path.read_text(encoding="utf-8")
    rel = path.relative_to(repo_root).as_posix()
    marks = list(CHUNK_RE.finditer(text))
    chunks: list[Chunk] = []
    for i, mark in enumerate(marks):
        kind = mark.group(1).lower()
        if kind != "default":
            continue
        attrs = _attrs(mark.group("attrs") or "")
        start = mark.end()
        end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
        content = text[start:end].strip()
        heading, heading_anchor = _heading_before(text, mark.start())
        chunk_id = attrs.get("id") or f"{feature_id}.{i}"
        section = attrs.get("section") or ""
        anchor = heading_anchor or chunk_id.split(".")[-1]
        token_est = estimate_tokens(content)
        chunks.append(
            Chunk(
                path=rel,
                feature_id=feature_id,
                chunk_id=chunk_id,
                section=section,
                heading=heading,
                anchor=anchor,
                content=content,
                content_hash=sha256_text(content),
                collection=collection_for(feature_id),
                token_estimate=token_est,
                oversized=token_est > settings.EMBED_TOKEN_LIMIT,
            )
        )
    return chunks


def scan_briefs(repo_root: Path | None = None) -> list[Chunk]:
    root = repo_root or settings.REPO_ROOT
    design = root / "prd" / "design"
    out: list[Chunk] = []
    if not design.is_dir():
        return out
    for feature_dir in sorted(design.iterdir()):
        brief = feature_dir / "brief" / "current.md"
        if not brief.is_file():
            continue
        out.extend(parse_brief(brief, root, feature_dir.name))
    return out
