# -*- coding: utf-8 -*-
"""增量对账：同 hash 不重复 embed；超长进失败清单。"""
from __future__ import annotations

import logging
from typing import Awaitable, Callable

from . import settings
from .chunking import Chunk, scan_briefs
from .store import VectorStore

log = logging.getLogger("kb-api.indexer")

EmbedFn = Callable[[list[str]], Awaitable[list[list[float]]]]


class Indexer:
    def __init__(self, store: VectorStore, embed: EmbedFn) -> None:
        self.store = store
        self.embed = embed

    async def rebuild(self) -> dict:
        chunks = scan_briefs()
        if not chunks:
            raise RuntimeError("语料扫描为空，禁止清除已有索引")
        self.store.ensure_collections()
        existing = self.store.existing_points()
        current_keys = {f"{c.path}::{c.chunk_id}" for c in chunks if not c.oversized}
        items: list[dict] = []
        failed: list[dict] = []
        to_embed: list[Chunk] = []

        for chunk in chunks:
            key = f"{chunk.path}::{chunk.chunk_id}"
            old = existing.get(key)
            old_hash = (old or {}).get("payload", {}).get("content_hash") or ""
            if chunk.oversized:
                failed.append({
                    "path": chunk.path,
                    "chunk_id": chunk.chunk_id,
                    "action": "失败",
                    "old_hash": old_hash,
                    "new_hash": chunk.content_hash,
                    "reason": f"超过 {settings.EMBED_MODEL} 上限 {settings.EMBED_TOKEN_LIMIT} token，该块不入库、不二次切、不截断",
                })
                if old:
                    self.store.delete_point(old["collection"], chunk.path, chunk.chunk_id)
                    items.append({
                        "path": chunk.path,
                        "chunk_id": chunk.chunk_id,
                        "action": "删",
                        "old_hash": old_hash,
                        "new_hash": "",
                    })
                continue
            if old and old_hash == chunk.content_hash:
                continue
            action = "改" if old else "增"
            to_embed.append(chunk)
            items.append({
                "path": chunk.path,
                "chunk_id": chunk.chunk_id,
                "action": action,
                "old_hash": old_hash,
                "new_hash": chunk.content_hash,
            })

        for old_key, old in existing.items():
            if old_key in current_keys:
                continue
            payload = old.get("payload") or {}
            path = payload.get("path") or old_key.split("::", 1)[0]
            chunk_id = payload.get("chunk_id") or old_key.split("::", 1)[-1]
            self.store.delete_point(old["collection"], path, chunk_id)
            items.append({
                "path": path,
                "chunk_id": chunk_id,
                "action": "删",
                "old_hash": payload.get("content_hash") or "",
                "new_hash": "",
            })

        batch_size = 8
        for i in range(0, len(to_embed), batch_size):
            batch = to_embed[i:i + batch_size]
            vectors = await self.embed([c.content for c in batch])
            for chunk, vector in zip(batch, vectors):
                self.store.upsert(chunk.collection, chunk.payload(), vector)

        self.store.rebuild_bm25_from_qdrant()
        return {
            "scanned": len(chunks),
            "changed": items,
            "failed": failed,
            "chunk_count": self.store.chunk_count(),
        }
