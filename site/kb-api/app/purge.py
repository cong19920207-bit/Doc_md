# -*- coding: utf-8 -*-
"""STEP-A06：超管对单个会话做实际删除。
先让会话不可读，再删消息、执行记录和记忆索引。重复提交返回同一次操作。
不删除备份，也不提供恢复。"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

import pymysql

from . import settings
from .auth_store import use_memory_auth
from .util import uid

log = logging.getLogger("kb-api.purge")

PURGE_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS kb_purge_ops (
  id VARCHAR(64) NOT NULL PRIMARY KEY,
  conv_id VARCHAR(64) NOT NULL,
  actor_id VARCHAR(64) NULL,
  status VARCHAR(16) NOT NULL,
  facts VARCHAR(16) NOT NULL,
  derived VARCHAR(16) NOT NULL,
  error VARCHAR(64) NULL,
  created_at DATETIME(3) NOT NULL,
  UNIQUE KEY uniq_purge_conv (conv_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
"""


def _now() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]


class MemoryPurgeRepo:
    def __init__(self) -> None:
        self.ops: dict[str, dict] = {}
        self.by_conv: dict[str, str] = {}

    def ensure_schema(self) -> bool:
        return True

    def get(self, op_id: str) -> dict | None:
        row = self.ops.get(op_id)
        return dict(row) if row else None

    def get_by_conv(self, conv_id: str) -> dict | None:
        oid = self.by_conv.get(conv_id)
        return self.get(oid) if oid else None

    def insert(self, row: dict) -> None:
        self.ops[row["id"]] = dict(row)
        self.by_conv[row["conv_id"]] = row["id"]

    def update(self, op_id, fields):
        self.ops[op_id].update(fields)


class MysqlPurgeRepo:
    def _conn(self):
        return pymysql.connect(
            host=settings.MYSQL_HOST, port=settings.MYSQL_PORT, user=settings.MYSQL_USER,
            password=settings.MYSQL_PASSWORD, database=settings.MYSQL_DATABASE,
            charset="utf8mb4", autocommit=True, cursorclass=pymysql.cursors.DictCursor,
        )

    def ensure_schema(self) -> bool:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(PURGE_SCHEMA_SQL)
        return True

    def get(self, op_id: str) -> dict | None:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM kb_purge_ops WHERE id=%s", (op_id,))
                row = cur.fetchone()
        return dict(row) if row else None

    def get_by_conv(self, conv_id: str) -> dict | None:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM kb_purge_ops WHERE conv_id=%s", (conv_id,))
                row = cur.fetchone()
        return dict(row) if row else None

    def insert(self, row: dict) -> None:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO kb_purge_ops (id, conv_id, actor_id, status, facts, derived, error, created_at) "
                    "VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                    (row["id"], row["conv_id"], row.get("actor_id"), row["status"], row["facts"],
                     row["derived"], row.get("error"), row["created_at"]),
                )


    def update(self, op_id, fields):
        cols = [k for k in ('status', 'facts', 'derived', 'error') if k in fields]
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute('UPDATE kb_purge_ops SET ' + ', '.join(k + '=%s' for k in cols) + ' WHERE id=%s',
                            [fields[k] for k in cols] + [op_id])


class PurgeBook:
    def __init__(self, repo: MemoryPurgeRepo | MysqlPurgeRepo | None = None) -> None:
        if repo is not None:
            self.repo = repo
        elif use_memory_auth():
            self.repo = MemoryPurgeRepo()
        else:
            self.repo = MysqlPurgeRepo()

    def ensure_schema(self) -> bool:
        try:
            return bool(self.repo.ensure_schema())
        except Exception as exc:  # noqa: BLE001
            log.warning("purge schema failed: %s", exc)
            return False

    def get(self, op_id: str) -> dict | None:
        return self.repo.get(op_id)

    def for_conv(self, conv_id: str) -> dict | None:
        return self.repo.get_by_conv(conv_id)

    def run(self, conv_id: str, actor_id: str, convs: Any, msgs: Any, logs: Any, mem_index: Any, diag: Any) -> dict:
        """已有操作直接返回。否则先阻断，再删事实与派生索引。失败也保持不可读。"""
        existing = self.for_conv(conv_id)
        if existing:
            return existing
        row = {'id': uid('pg'), 'conv_id': conv_id, 'actor_id': actor_id, 'status': 'running',
               'facts': 'pending', 'derived': 'pending', 'error': None, 'created_at': _now()}
        self.repo.insert(row)
        try:
            convs.mark_purged(conv_id)
        except Exception as exc:  # noqa: BLE001
            log.warning('purge barrier %s failed: %s', conv_id, exc)
            row.update(status='partial', facts='failed', error='barrier_failed')
            self.repo.update(row['id'], {'status': 'partial', 'facts': 'failed', 'error': 'barrier_failed'})
            return row
        facts, derived, error = "deleted", "deleted", None
        try:
            msgs.purge_conv(conv_id)
            if hasattr(logs, "delete_conv"):
                logs.delete_conv(conv_id)
        except Exception as exc:  # noqa: BLE001
            log.warning("purge facts %s failed: %s", conv_id, exc)
            facts, error = "failed", "facts_failed"
        try:
            if mem_index is not None:
                mem_index.delete_conversation(conv_id)
        except Exception as exc:  # noqa: BLE001
            log.warning("purge index %s failed: %s", conv_id, exc)
            derived, error = "failed", error or "derived_failed"
            if diag is not None:
                diag.record("purge_cleanup", error, conv_id=conv_id)
        status = "done" if facts == "deleted" and derived == "deleted" else "partial"
        row.update(status=status, facts=facts, derived=derived, error=error)
        self.repo.update(row['id'], {'status': status, 'facts': facts, 'derived': derived, 'error': error})
        return row
