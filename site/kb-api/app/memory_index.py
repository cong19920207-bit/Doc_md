# -*- coding: utf-8 -*-
"""STEP-Q14：Conversation Memory 派生索引（G-E04-1～4）。
消息表是事实源，索引只是派生数据：每条已保存消息一条（超长切片记字符范围），保存后后台异步写入；
逐条记录已索引/失败/待处理，覆盖按「应索引 vs 已索引」逐条比对，能认出中间空洞。
用户隐藏与清空不删索引，由查询与回源过滤（Q15）；只有管理员实际删除才物理删除（A06）。"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any, Awaitable, Callable

import pymysql

from . import settings
from .auth_store import use_memory_auth
from .util import sha256_text, stable_point_id

log = logging.getLogger("kb-api.memory")

CHUNK_CHARS = 600
INDEX_GEN = 1
STATUSES = ("pending", "indexed", "failed")
COVERAGE_STATES = ("normal", "partial", "lagging", "failed", "unknown", "not_connected")

INDEX_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS kb_mem_index (
  msg_id VARCHAR(64) NOT NULL PRIMARY KEY,
  conv_id VARCHAR(64) NOT NULL,
  seq BIGINT NOT NULL,
  status VARCHAR(16) NOT NULL,
  chunks INT NOT NULL DEFAULT 0,
  content_hash CHAR(64) NULL,
  attempts INT NOT NULL DEFAULT 0,
  error VARCHAR(64) NULL,
  gen INT NOT NULL DEFAULT 1,
  updated_at DATETIME(3) NOT NULL,
  INDEX idx_mem_index_conv (conv_id, seq)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
"""


def _now() -> datetime:
    return datetime.utcnow()


def indexable(row: dict) -> bool:
    """G-E04-2：User 原文一律索引；Assistant 只索引已保存的完整回答（部分、失败提示不当最终答案）。"""
    if not str(row.get("content") or "").strip():
        return False
    if row.get("role") == "user":
        return True
    return row.get("role") == "assistant" and (row.get("completeness") or "complete") == "complete"


def chunk_ranges(text: str, size: int = CHUNK_CHARS) -> list[tuple[int, int]]:
    """按字符切片，半开区间 [start, end)；短消息只有一片。"""
    n = len(text or "")
    if n <= size:
        return [(0, n)]
    return [(i, min(n, i + size)) for i in range(0, n, size)]


# ---------------- 索引记录 ----------------

class MemoryRecordRepo:
    def __init__(self) -> None:
        self.rows: dict[str, dict] = {}

    def ensure_schema(self) -> bool:
        return True

    def upsert(self, rec: dict) -> None:
        cur = self.rows.get(rec["msg_id"], {})
        cur.update(rec)
        self.rows[rec["msg_id"]] = cur

    def get(self, msg_id: str) -> dict | None:
        row = self.rows.get(msg_id)
        return dict(row) if row else None

    def list_conv(self, conv_id: str) -> list[dict]:
        return sorted((dict(r) for r in self.rows.values() if r["conv_id"] == conv_id), key=lambda r: int(r["seq"]))

    def delete_conv(self, conv_id: str) -> None:
        for k in [k for k, r in self.rows.items() if r["conv_id"] == conv_id]:
            self.rows.pop(k, None)


class MysqlRecordRepo:
    _COLS = ("msg_id", "conv_id", "seq", "status", "chunks", "content_hash", "attempts", "error", "gen", "updated_at")

    def _conn(self):
        return pymysql.connect(
            host=settings.MYSQL_HOST, port=settings.MYSQL_PORT, user=settings.MYSQL_USER,
            password=settings.MYSQL_PASSWORD, database=settings.MYSQL_DATABASE, charset="utf8mb4",
            autocommit=True, cursorclass=pymysql.cursors.DictCursor,
            connect_timeout=3, read_timeout=5, write_timeout=5,
        )

    def ensure_schema(self) -> bool:
        try:
            with self._conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(INDEX_SCHEMA_SQL)
            return True
        except Exception as exc:  # noqa: BLE001
            log.warning("ensure mem index schema failed: %s", exc)
            return False

    def upsert(self, rec: dict) -> None:
        cols = [c for c in self._COLS if c in rec]
        updates = ", ".join(f"{c}=VALUES({c})" for c in cols if c != "msg_id")
        sql = (
            f"INSERT INTO kb_mem_index ({', '.join(cols)}) VALUES ({', '.join(['%s'] * len(cols))}) "
            f"ON DUPLICATE KEY UPDATE {updates}"
        )
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, tuple(rec[c] for c in cols))

    def get(self, msg_id: str) -> dict | None:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM kb_mem_index WHERE msg_id=%s", (msg_id,))
                row = cur.fetchone()
        return dict(row) if row else None

    def list_conv(self, conv_id: str) -> list[dict]:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM kb_mem_index WHERE conv_id=%s ORDER BY seq ASC", (conv_id,))
                return [dict(r) for r in (cur.fetchall() or [])]

    def delete_conv(self, conv_id: str) -> None:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM kb_mem_index WHERE conv_id=%s", (conv_id,))


# ---------------- 向量库 ----------------

class QdrantMemoryVec:
    """对话记忆专用 collection；只按会话过滤检索，不与知识库混用。"""

    def __init__(self, client: Any) -> None:
        self.client = client

    def ensure(self) -> None:
        from qdrant_client.http import models as qm

        existing = {c.name for c in self.client.get_collections().collections}
        if settings.COLLECTION_MEMORY in existing:
            return
        self.client.create_collection(
            collection_name=settings.COLLECTION_MEMORY,
            vectors_config=qm.VectorParams(size=settings.EMBED_DIM, distance=qm.Distance.COSINE),
        )
        for field in ("conv_id", "msg_id", "account_id"):
            self.client.create_payload_index(
                collection_name=settings.COLLECTION_MEMORY, field_name=field,
                field_schema=qm.PayloadSchemaType.KEYWORD,
            )

    def upsert(self, points: list[tuple[str, list[float], dict]]) -> None:
        from qdrant_client.http import models as qm

        self.client.upsert(
            collection_name=settings.COLLECTION_MEMORY,
            points=[qm.PointStruct(id=pid, vector=vec, payload=payload) for pid, vec, payload in points],
        )

    def _delete_where(self, key: str, value: str) -> None:
        from qdrant_client.http import models as qm

        self.client.delete(
            collection_name=settings.COLLECTION_MEMORY,
            points_selector=qm.FilterSelector(
                filter=qm.Filter(must=[qm.FieldCondition(key=key, match=qm.MatchValue(value=value))])
            ),
        )

    def delete_msg(self, msg_id: str) -> None:
        self._delete_where("msg_id", msg_id)

    def delete_conv(self, conv_id: str) -> None:
        self._delete_where("conv_id", conv_id)

    def search(self, vector: list[float], conv_id: str, limit: int) -> list[dict]:
        from qdrant_client.http import models as qm

        flt = qm.Filter(must=[qm.FieldCondition(key="conv_id", match=qm.MatchValue(value=conv_id))])
        hits = self.client.query_points(
            collection_name=settings.COLLECTION_MEMORY, query=vector, limit=limit,
            query_filter=flt, with_payload=True,
        ).points
        return [dict(h.payload or {}, _score=float(h.score or 0)) for h in hits]


# ---------------- 索引作业 ----------------

class MemoryIndex:
    def __init__(
        self,
        records: MemoryRecordRepo | MysqlRecordRepo | None,
        vec: Any,
        embed: Callable[[list[str]], Awaitable[list[list[float]]]],
        owner_of: Callable[[str], str | None],
    ) -> None:
        if records is None:
            records = MemoryRecordRepo() if use_memory_auth() else MysqlRecordRepo()
        self.records = records
        self.vec = vec
        self.embed = embed
        self.owner_of = owner_of
        self.connected = False
        self.connect_error: str | None = None
        self._tasks: set = set()

    def ensure_schema(self) -> bool:
        try:
            return bool(self.records.ensure_schema())
        except Exception as exc:  # noqa: BLE001
            log.warning("mem index schema failed: %s", exc)
            return False

    def connect(self) -> bool:
        """启动时确认向量库与 Key 可用；不可用时覆盖状态报「未接入」，消息照常保存。"""
        if not settings.DASHSCOPE_API_KEY:
            self.connected, self.connect_error = False, "missing_key"
            return False
        try:
            self.vec.ensure()
        except Exception as exc:  # noqa: BLE001
            log.warning("memory collection unavailable: %s", exc)
            self.connected, self.connect_error = False, "vector_unavailable"
            return False
        self.connected, self.connect_error = True, None
        return True

    def _record(self, row: dict, status: str, **extra: Any) -> None:
        self.records.upsert({
            "msg_id": row["id"], "conv_id": row["conv_id"], "seq": int(row["seq"]), "status": status,
            "gen": INDEX_GEN, "updated_at": _now(), **extra,
        })

    def note_saved(self, row: dict) -> bool:
        """消息保存成功后调用：先记「待处理」，再交后台写入。任何异常都不向保存流程抛出。"""
        if not indexable(row):
            return False
        try:
            self._record(row, "pending")
        except Exception as exc:  # noqa: BLE001
            # 记录写不进时覆盖会显示缺失，由回填补齐
            log.warning("mem index pending record failed: %s", exc)
        if not self.connected:
            return True
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return True
        task = loop.create_task(self.index_rows([dict(row)]))
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)
        return True

    async def drain(self) -> None:
        while self._tasks:
            await asyncio.gather(*list(self._tasks), return_exceptions=True)

    def _points(self, row: dict, vectors: list[list[float]], ranges: list[tuple[int, int]]) -> list[tuple]:
        text = str(row.get("content") or "")
        owner = self.owner_of(row["conv_id"])
        out = []
        for i, ((start, end), vec) in enumerate(zip(ranges, vectors)):
            out.append((stable_point_id(row["id"], str(i)), vec, {
                "conv_id": row["conv_id"], "account_id": owner or "", "msg_id": row["id"],
                "round_id": row["round_id"], "round_seq": int(row["round_seq"]), "seq": int(row["seq"]),
                "role": row["role"], "version_no": row.get("version_no"), "source": row.get("source") or "live",
                "created_at": str(row.get("created_at") or ""), "chunk_index": i, "chunk_count": len(ranges),
                "char_start": start, "char_end": end, "text": text[start:end],
            }))
        return out

    async def index_rows(self, rows: list[dict]) -> dict:
        """逐条写入；单条失败只记该条，不影响其他。消息不可变，同一条重写按稳定点 id 覆盖。"""
        done = {"indexed": 0, "failed": 0}
        for row in rows:
            if not indexable(row):
                continue
            text = str(row.get("content") or "")
            ranges = chunk_ranges(text)
            prev = None
            try:
                prev = self.records.get(row["id"])
            except Exception:  # noqa: BLE001
                prev = None
            attempts = int((prev or {}).get("attempts") or 0) + 1
            try:
                label = "用户" if row["role"] == "user" else "回答"
                vectors = await self.embed([f"{label}：{text[s:e]}" for s, e in ranges])
                if len(vectors) != len(ranges):
                    raise ValueError("embed_count_mismatch")
                self.vec.upsert(self._points(row, vectors, ranges))
                self._record(row, "indexed", chunks=len(ranges), content_hash=sha256_text(text),
                             attempts=attempts, error=None)
                done["indexed"] += 1
            except Exception as exc:  # noqa: BLE001
                code = getattr(exc, "code", None) or type(exc).__name__
                log.warning("mem index %s failed: %s", row.get("id"), exc)
                try:
                    self._record(row, "failed", attempts=attempts, error=str(code)[:64])
                except Exception:  # noqa: BLE001
                    pass
                done["failed"] += 1
        return done

    async def backfill(self, msgs: Any, conv_ids: list[str]) -> dict:
        """补齐遗漏：迁移消息、待处理、失败、内容变更的都重写；已索引且一致的跳过。
        按全部消息（含清空前）回填，清空与隐藏由查询时过滤，不因回填恢复可见。"""
        total = {"convs": 0, "indexed": 0, "failed": 0, "skipped": 0}
        if not self.connected:
            return dict(total, error=self.connect_error or "not_connected")
        for cid in conv_ids:
            total["convs"] += 1
            try:
                rows = [r for r in msgs.admin_messages(cid) if indexable(r)]
                recs = {r["msg_id"]: r for r in self.records.list_conv(cid)}
            except Exception as exc:  # noqa: BLE001
                log.warning("mem backfill %s read failed: %s", cid, exc)
                total["failed"] += 1
                continue
            todo = []
            for r in rows:
                rec = recs.get(r["id"])
                if rec and rec.get("status") == "indexed" and rec.get("content_hash") == sha256_text(r.get("content") or ""):
                    total["skipped"] += 1
                    continue
                todo.append(r)
            res = await self.index_rows(todo)
            total["indexed"] += res["indexed"]
            total["failed"] += res["failed"]
        return total

    def coverage(self, conv_id: str, messages: list[dict]) -> dict:
        """C29 / AT-21：按应索引的每条消息比对，不只看最新时间。
        messages 由调用方给定范围（Memory Tool 用本轮有效范围，后台用全部）。"""
        expected = sorted((m for m in messages if indexable(m)), key=lambda m: int(m["seq"]))
        base = {"conv_id": conv_id, "gen": INDEX_GEN, "expected": len(expected), "indexed": 0,
                "pending": 0, "failed": 0, "missing": 0, "holes": [], "indexed_through_seq": None}
        if not self.connected:
            return dict(base, state="not_connected", connected=False, reason=self.connect_error)
        try:
            recs = {r["msg_id"]: r for r in self.records.list_conv(conv_id)}
        except Exception as exc:  # noqa: BLE001
            log.warning("mem coverage %s failed: %s", conv_id, exc)
            return dict(base, state="unknown", connected=True, reason="records_unavailable")
        done_seqs, gaps = [], []
        for m in expected:
            rec = recs.get(m["id"])
            status = (rec or {}).get("status")
            if status == "indexed" and rec.get("content_hash") == sha256_text(m.get("content") or ""):
                base["indexed"] += 1
                done_seqs.append(int(m["seq"]))
                continue
            key = status if status in ("pending", "failed") else "missing"
            base[key] += 1
            gaps.append((int(m["seq"]), key))
        base["indexed_through_seq"] = max(done_seqs) if done_seqs else None
        if not gaps:
            state = "normal"
        elif not done_seqs:
            state = "failed" if base["failed"] else "lagging"
        else:
            top = max(done_seqs)
            holes = [s for s, _ in gaps if s < top]
            base["holes"] = _ranges(holes)
            if holes or base["failed"]:
                state = "partial"
            else:
                # 缺的都是最新几条且只是还没写完：落后，不是空洞
                state = "lagging"
        return dict(base, state=state, connected=True)

    def delete_conversation(self, conv_id: str) -> None:
        """管理员实际删除（A06）时清理派生索引与记录；用户隐藏/清空不走这里。"""
        self.vec.delete_conv(conv_id)
        self.records.delete_conv(conv_id)


def _ranges(seqs: list[int]) -> list[list[int]]:
    """把空洞 seq 合并成 [起, 止] 区间，便于展示与排查。"""
    out: list[list[int]] = []
    for s in sorted(seqs):
        if out and s == out[-1][1] + 1:
            out[-1][1] = s
        else:
            out.append([s, s])
    return out
