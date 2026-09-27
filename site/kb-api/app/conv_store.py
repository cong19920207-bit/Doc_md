# -*- coding: utf-8 -*-
"""云端对话：按账号隔离，上限 40，删会话不删 qa_rounds。"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

import pymysql

from . import settings
from .auth_store import use_memory_auth
from .util import json_dumps, json_loads, uid

log = logging.getLogger("kb-api.convs")
MAX_CONVS = 40

CONV_SCHEMA_SQL = (
    """
    CREATE TABLE IF NOT EXISTS kb_conversations (
      id VARCHAR(64) NOT NULL PRIMARY KEY,
      account_id VARCHAR(64) NOT NULL,
      title VARCHAR(255) NOT NULL,
      title_locked TINYINT NOT NULL DEFAULT 0,
      payload MEDIUMTEXT NULL,
      created_at DATETIME(3) NOT NULL,
      updated_at DATETIME(3) NOT NULL,
      INDEX idx_kb_convs_account (account_id, updated_at)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """,
)


def _now() -> datetime:
    return datetime.utcnow()


class MemoryConvRepo:
    def __init__(self) -> None:
        self.rows: dict[str, dict] = {}

    def ensure_schema(self) -> bool:
        return True

    def list_for(self, account_id: str) -> list[dict]:
        items = [dict(r) for r in self.rows.values() if r.get("account_id") == account_id]
        items.sort(key=lambda r: str(r.get("updated_at") or ""), reverse=True)
        return items

    def list_all(self) -> list[dict]:
        items = [dict(r) for r in self.rows.values()]
        items.sort(key=lambda r: str(r.get("updated_at") or ""), reverse=True)
        return items

    def get(self, conv_id: str) -> dict | None:
        row = self.rows.get(conv_id)
        return dict(row) if row else None

    def insert(self, row: dict) -> None:
        self.rows[row["id"]] = dict(row)

    def update(self, conv_id: str, fields: dict) -> None:
        row = self.rows.get(conv_id)
        if not row:
            return
        row.update(fields)

    def delete(self, conv_id: str) -> None:
        self.rows.pop(conv_id, None)


class MysqlConvRepo:
    def ensure_schema(self) -> bool:
        try:
            with self._conn() as conn:
                with conn.cursor() as cur:
                    for sql in CONV_SCHEMA_SQL:
                        cur.execute(sql)
            return True
        except Exception as exc:  # noqa: BLE001
            log.warning("ensure conv schema failed: %s", exc)
            return False

    def _conn(self):
        return pymysql.connect(
            host=settings.MYSQL_HOST,
            port=settings.MYSQL_PORT,
            user=settings.MYSQL_USER,
            password=settings.MYSQL_PASSWORD,
            database=settings.MYSQL_DATABASE,
            charset="utf8mb4",
            autocommit=True,
            cursorclass=pymysql.cursors.DictCursor,
            connect_timeout=3,
            read_timeout=5,
            write_timeout=5,
        )

    def list_for(self, account_id: str) -> list[dict]:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM kb_conversations WHERE account_id=%s "
                    "ORDER BY updated_at DESC",
                    (account_id,),
                )
                return [dict(r) for r in (cur.fetchall() or [])]

    def list_all(self) -> list[dict]:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM kb_conversations ORDER BY updated_at DESC")
                return [dict(r) for r in (cur.fetchall() or [])]

    def get(self, conv_id: str) -> dict | None:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM kb_conversations WHERE id=%s", (conv_id,))
                row = cur.fetchone()
        return dict(row) if row else None

    def insert(self, row: dict) -> None:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO kb_conversations (id, account_id, title, title_locked, payload, "
                    "created_at, updated_at) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                    (
                        row["id"],
                        row["account_id"],
                        row["title"],
                        row["title_locked"],
                        row.get("payload"),
                        row["created_at"],
                        row["updated_at"],
                    ),
                )

    def update(self, conv_id: str, fields: dict) -> None:
        sets = []
        args: list[Any] = []
        for key in ("title", "title_locked", "payload", "updated_at"):
            if key in fields:
                sets.append(f"{key}=%s")
                args.append(fields[key])
        if not sets:
            return
        args.append(conv_id)
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"UPDATE kb_conversations SET {', '.join(sets)} WHERE id=%s",
                    args,
                )

    def delete(self, conv_id: str) -> None:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM kb_conversations WHERE id=%s", (conv_id,))


class ConvStore:
    def __init__(self, repo: MemoryConvRepo | MysqlConvRepo | None = None) -> None:
        if repo is not None:
            self.repo = repo
        elif use_memory_auth():
            self.repo = MemoryConvRepo()
        else:
            self.repo = MysqlConvRepo()

    def ensure_schema(self) -> bool:
        try:
            return bool(self.repo.ensure_schema())
        except Exception as exc:  # noqa: BLE001
            log.warning("conv schema failed: %s", exc)
            return False

    def _public(self, row: dict) -> dict:
        payload = json_loads(row.get("payload"), {}) or {}
        return {
            "id": row["id"],
            "title": row.get("title") or "新对话",
            "titleLocked": bool(row.get("title_locked")),
            "messages": payload.get("messages") or [],
            "lastChunks": payload.get("lastChunks") or [],
            "citationsOpen": payload.get("citationsOpen") or {},
            "updatedAt": str(row.get("updated_at") or ""),
        }

    def list_ids(self, account_id: str) -> list[str]:
        return [str(r["id"]) for r in self.repo.list_for(account_id)]

    def list_public(self, account_id: str) -> list[dict]:
        return [self._public(r) for r in self.repo.list_for(account_id)]

    def list_all_public(self) -> list[dict]:
        try:
            rows = self.repo.list_all()
        except Exception as exc:  # noqa: BLE001
            log.warning("list all convs failed: %s", exc)
            rows = []
        return [{"id": r["id"], "account_id": r.get("account_id"), "title": r.get("title")} for r in rows]

    def get_owned(self, account_id: str, conv_id: str) -> dict | None:
        row = self.repo.get(conv_id)
        if not row or str(row.get("account_id")) != str(account_id):
            return None
        return self._public(row)

    def create(self, account_id: str, body: dict | None = None) -> dict | None:
        owned = self.repo.list_for(account_id)
        if len(owned) >= MAX_CONVS:
            oldest = owned[-1]
            self.repo.delete(str(oldest["id"]))
        now = _now()
        body = body or {}
        row = {
            "id": uid("c"),
            "account_id": account_id,
            "title": str(body.get("title") or "新对话")[:255],
            "title_locked": 1 if body.get("titleLocked") else 0,
            "payload": json_dumps({
                "messages": body.get("messages") or [],
                "lastChunks": body.get("lastChunks") or [],
                "citationsOpen": body.get("citationsOpen") or {},
            }),
            "created_at": now,
            "updated_at": now,
        }
        self.repo.insert(row)
        return self._public(row)

    def update(self, account_id: str, conv_id: str, body: dict) -> dict | None:
        row = self.repo.get(conv_id)
        if not row or str(row.get("account_id")) != str(account_id):
            return None
        now = _now()
        payload = json_loads(row.get("payload"), {}) or {}
        if "messages" in body:
            payload["messages"] = body.get("messages") or []
        if "lastChunks" in body:
            payload["lastChunks"] = body.get("lastChunks") or []
        if "citationsOpen" in body:
            payload["citationsOpen"] = body.get("citationsOpen") or {}
        fields = {
            "payload": json_dumps(payload),
            "updated_at": now,
        }
        if "title" in body:
            fields["title"] = str(body.get("title") or "新对话")[:255]
        if "titleLocked" in body:
            fields["title_locked"] = 1 if body.get("titleLocked") else 0
        self.repo.update(conv_id, fields)
        return self.get_owned(account_id, conv_id)

    def delete(self, account_id: str, conv_id: str) -> bool:
        row = self.repo.get(conv_id)
        if not row or str(row.get("account_id")) != str(account_id):
            return False
        self.repo.delete(conv_id)
        return True
