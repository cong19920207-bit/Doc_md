# -*- coding: utf-8 -*-
"""Qdrant 两 collection + 内存 BM25。"""
from __future__ import annotations

import logging
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.http import models as qm

from . import settings
from .bm25 import Bm25Index, rrf_merge
from .util import stable_point_id

log = logging.getLogger("kb-api.store")


class VectorStore:
    def __init__(self, url: str | None = None) -> None:
        self.client = QdrantClient(url=url or settings.QDRANT_URL, timeout=30)
        self.bm25 = Bm25Index()
        self.meta: dict[str, dict] = {}

    def ping(self) -> bool:
        try:
            self.client.get_collections()
            return True
        except Exception as exc:  # noqa: BLE001
            log.warning("qdrant ping failed: %s", exc)
            return False

    def ensure_collections(self) -> None:
        existing = {c.name for c in self.client.get_collections().collections}
        for name in (settings.COLLECTION_CLIENT, settings.COLLECTION_ADMIN):
            if name in existing:
                continue
            self.client.create_collection(
                collection_name=name,
                vectors_config=qm.VectorParams(
                    size=settings.EMBED_DIM,
                    distance=qm.Distance.COSINE,
                ),
            )
            self.client.create_payload_index(
                collection_name=name,
                field_name="feature_id",
                field_schema=qm.PayloadSchemaType.KEYWORD,
            )
            self.client.create_payload_index(
                collection_name=name,
                field_name="chunk_id",
                field_schema=qm.PayloadSchemaType.KEYWORD,
            )
            self.client.create_payload_index(
                collection_name=name,
                field_name="path",
                field_schema=qm.PayloadSchemaType.KEYWORD,
            )

    def collection_count(self, name: str) -> int:
        try:
            return int(self.client.count(name, exact=True).count)
        except Exception:  # noqa: BLE001
            return 0

    def chunk_count(self) -> int:
        return self.collection_count(settings.COLLECTION_CLIENT) + self.collection_count(settings.COLLECTION_ADMIN)

    def _scroll_all(self, name: str) -> list[qm.Record]:
        out: list[qm.Record] = []
        offset = None
        while True:
            records, offset = self.client.scroll(
                collection_name=name,
                limit=128,
                offset=offset,
                with_payload=True,
                with_vectors=False,
            )
            out.extend(records or [])
            if offset is None:
                break
        return out

    def rebuild_bm25_from_qdrant(self) -> None:
        self.bm25.clear()
        self.meta.clear()
        for name in (settings.COLLECTION_CLIENT, settings.COLLECTION_ADMIN):
            try:
                records = self._scroll_all(name)
            except Exception as exc:  # noqa: BLE001
                log.warning("scroll %s failed: %s", name, exc)
                continue
            for rec in records:
                payload = rec.payload or {}
                key = self._key(payload.get("path", ""), payload.get("chunk_id", ""))
                self.meta[key] = dict(payload)
                self.bm25.add(key, payload.get("content") or "", dict(payload))

    def existing_points(self) -> dict[str, dict]:
        found: dict[str, dict] = {}
        for name in (settings.COLLECTION_CLIENT, settings.COLLECTION_ADMIN):
            try:
                records = self._scroll_all(name)
            except Exception:  # noqa: BLE001
                continue
            for rec in records:
                payload = rec.payload or {}
                key = self._key(payload.get("path", ""), payload.get("chunk_id", ""))
                found[key] = {
                    "collection": name,
                    "point_id": str(rec.id),
                    "payload": payload,
                }
        return found

    @staticmethod
    def _key(path: str, chunk_id: str) -> str:
        return f"{path}::{chunk_id}"

    def lookup_payload(self, path: str, chunk_id: str) -> dict | None:
        """按 path::chunk_id 取内存中的入库块（含 content）。找不到返回 None。"""
        key = self._key(path or "", chunk_id or "")
        payload = self.meta.get(key)
        if not payload:
            return None
        return dict(payload)

    def upsert(self, collection: str, payload: dict, vector: list[float]) -> None:
        point_id = stable_point_id(payload["path"], payload["chunk_id"])
        self.client.upsert(
            collection_name=collection,
            points=[
                qm.PointStruct(id=point_id, vector=vector, payload=payload),
            ],
        )
        key = self._key(payload["path"], payload["chunk_id"])
        self.meta[key] = dict(payload)
        self.bm25.add(key, payload.get("content") or "", dict(payload))

    def delete_point(self, collection: str, path: str, chunk_id: str) -> None:
        point_id = stable_point_id(path, chunk_id)
        self.client.delete(
            collection_name=collection,
            points_selector=qm.PointIdsList(points=[point_id]),
        )
        key = self._key(path, chunk_id)
        self.meta.pop(key, None)
        self.bm25.remove(key)

    def vector_search(
        self,
        collection: str,
        vector: list[float],
        k: int,
        feature_id: str | None = None,
    ) -> list[dict]:
        query_filter = None
        if feature_id:
            query_filter = qm.Filter(
                must=[qm.FieldCondition(key="feature_id", match=qm.MatchValue(value=feature_id))]
            )
        try:
            hits = self.client.query_points(
                collection_name=collection,
                query=vector,
                limit=k,
                query_filter=query_filter,
                with_payload=True,
            ).points
        except Exception:
            hits = self.client.search(
                collection_name=collection,
                query_vector=vector,
                limit=k,
                query_filter=query_filter,
                with_payload=True,
            )
        out: list[dict] = []
        for hit in hits:
            payload = dict(hit.payload or {})
            payload["_score"] = float(hit.score or 0)
            payload["_key"] = self._key(payload.get("path", ""), payload.get("chunk_id", ""))
            out.append(payload)
        return out

    def hybrid_search(
        self,
        query_text: str,
        vector: list[float],
        k: int,
        collections: list[str],
        feature_id: str | None = None,
    ) -> list[dict]:
        vec_keys: list[str] = []
        by_key: dict[str, dict] = {}
        for col in collections:
            for item in self.vector_search(col, vector, k, feature_id=feature_id):
                key = item["_key"]
                by_key[key] = item
                vec_keys.append(key)

        def accept(meta: dict) -> bool:
            if meta.get("collection") not in collections:
                return False
            if feature_id and meta.get("feature_id") != feature_id:
                return False
            return True

        bm_keys = []
        for key, _score, meta in self.bm25.search(query_text, k, accept=accept):
            bm_keys.append(key)
            if key not in by_key:
                by_key[key] = dict(meta)
                by_key[key]["_key"] = key

        merged = rrf_merge([vec_keys, bm_keys], k)
        result: list[dict] = []
        seen: set[str] = set()
        for key in merged:
            if key in seen:
                continue
            seen.add(key)
            item = by_key.get(key) or dict(self.meta.get(key) or {})
            if not item:
                continue
            item["_key"] = key
            result.append(item)
        return result[:k]

    def get_payload_sample(self, limit: int = 5) -> list[dict[str, Any]]:
        samples: list[dict[str, Any]] = []
        for name in (settings.COLLECTION_CLIENT, settings.COLLECTION_ADMIN):
            try:
                records, _ = self.client.scroll(collection_name=name, limit=limit, with_payload=True)
            except Exception:  # noqa: BLE001
                continue
            for rec in records or []:
                samples.append(rec.payload or {})
        return samples
