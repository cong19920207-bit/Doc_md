# -*- coding: utf-8 -*-
"""STEP-A13 / A14：知识重建与记忆回填的任务记录。
进行中的范围重叠时不再另起一份。不提供把覆盖改成完整的入口。"""
from __future__ import annotations

import logging
import threading
from contextlib import contextmanager
from datetime import datetime
from typing import Any

import pymysql

from . import settings
from .auth_store import use_memory_auth
from .util import json_dumps, json_loads, uid
from . import listing

log = logging.getLogger("kb-api.index-tasks")

TASK_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS kb_index_tasks (
  id VARCHAR(64) NOT NULL PRIMARY KEY,
  grp VARCHAR(16) NOT NULL,
  kind VARCHAR(32) NOT NULL,
  scope VARCHAR(64) NOT NULL,
  actor_id VARCHAR(64) NULL,
  status VARCHAR(16) NOT NULL,
  parent_id VARCHAR(64) NULL,
  scanned INT NOT NULL DEFAULT 0,
  changed INT NOT NULL DEFAULT 0,
  failed INT NOT NULL DEFAULT 0,
  integrity VARCHAR(16) NOT NULL,
  error VARCHAR(255) NULL,
  detail MEDIUMTEXT NULL,
  created_at DATETIME(3) NOT NULL,
  finished_at DATETIME(3) NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
"""


def _now() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]


class MemoryTaskRepo:
    def __init__(self) -> None:
        self.rows: dict[str, dict] = {}

    def ensure_schema(self) -> bool:
        return True

    def insert(self, row: dict) -> None:
        self.rows[row["id"]] = dict(row)

    def update(self, task_id: str, fields: dict) -> None:
        row = self.rows.get(task_id)
        if row:
            row.update(fields)

    def get(self, task_id: str) -> dict | None:
        row = self.rows.get(task_id)
        return dict(row) if row else None

    def list_all(self) -> list[dict]:
        items = [dict(r) for r in self.rows.values()]
        items.sort(key=lambda r: str(r.get("created_at") or ""), reverse=True)
        return items

    def running_overlap(self, grp: str, scope: str) -> dict | None:
        return next((dict(r) for r in self.rows.values() if r.get('status') == 'running'
                     and r.get('grp') == grp and (scope == 'all' or r.get('scope') in ('all', scope))), None)

    @contextmanager
    def accept_lock(self):
        yield

    def page(self, group, cursor, size):
        return listing.paginate([r for r in self.rows.values() if not group or r.get('grp') == group],
                                ts_of=lambda r: r['created_at'], id_of=lambda r: r['id'], cursor=cursor, size=size)


class MysqlTaskRepo:
    @contextmanager
    def accept_lock(self):
        name = 'kb-index-accept:' + settings.MYSQL_DATABASE
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT GET_LOCK(%s, 2) AS acquired', (name,))
                if (cur.fetchone() or {}).get('acquired') != 1:
                    raise RuntimeError('任务受理锁暂时不可用')
                try:
                    yield
                finally:
                    cur.execute('SELECT RELEASE_LOCK(%s)', (name,))

    def page(self, group, cursor, size):
        before = listing.decode_cursor(cursor)
        sql, args = 'SELECT * FROM kb_index_tasks WHERE 1=1', []
        if group:
            sql += ' AND grp=%s'
            args.append(group)
        if before:
            sql += ' AND (created_at<%s OR (created_at=%s AND id<%s))'
            args.extend([before[0], before[0], before[1]])
        sql += ' ORDER BY created_at DESC, id DESC LIMIT %s'
        args.append(size + 1)
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, args)
                rows = [dict(r) for r in cur.fetchall() or []]
        for row in rows:
            row['detail'] = json_loads(row.get('detail'), {}) or {}
        more, rows = len(rows) > size, rows[:size]
        nxt = listing.encode_cursor(rows[-1]['created_at'], rows[-1]['id']) if more and rows else None
        return rows, nxt, more
    def _conn(self):
        return pymysql.connect(
            host=settings.MYSQL_HOST, port=settings.MYSQL_PORT, user=settings.MYSQL_USER,
            password=settings.MYSQL_PASSWORD, database=settings.MYSQL_DATABASE,
            charset="utf8mb4", autocommit=True, cursorclass=pymysql.cursors.DictCursor,
        )

    def ensure_schema(self) -> bool:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(TASK_SCHEMA_SQL)
        return True

    def insert(self, row: dict) -> None:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO kb_index_tasks (id, grp, kind, scope, actor_id, status, parent_id, scanned, "
                    "changed, failed, integrity, error, detail, created_at, finished_at) "
                    "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                    (row["id"], row["grp"], row["kind"], row["scope"], row.get("actor_id"), row["status"],
                     row.get("parent_id"), row["scanned"], row["changed"], row["failed"], row["integrity"],
                     row.get("error"), json_dumps(row.get("detail") or {}), row["created_at"], row.get("finished_at")),
                )

    def update(self, task_id: str, fields: dict) -> None:
        data = dict(fields)
        if "detail" in data:
            data["detail"] = json_dumps(data["detail"] or {})
        cols = [k for k in data if k in {
            "status", "scanned", "changed", "failed", "integrity", "error", "detail", "finished_at",
        }]
        if not cols:
            return
        sql = "UPDATE kb_index_tasks SET " + ", ".join(f"{k}=%s" for k in cols) + " WHERE id=%s"
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, [data[k] for k in cols] + [task_id])

    def get(self, task_id: str) -> dict | None:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM kb_index_tasks WHERE id=%s", (task_id,))
                row = cur.fetchone()
        if not row:
            return None
        row = dict(row)
        row["detail"] = json_loads(row.get("detail"), {}) or {}
        return row

    def list_all(self) -> list[dict]:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM kb_index_tasks ORDER BY created_at DESC LIMIT 100")
                out = []
                for row in cur.fetchall() or []:
                    item = dict(row)
                    item["detail"] = json_loads(item.get("detail"), {}) or {}
                    out.append(item)
                return out

    def running_overlap(self, grp: str, scope: str) -> dict | None:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM kb_index_tasks WHERE status='running' AND grp=%s "
                            "AND (%s='all' OR scope='all' OR scope=%s) ORDER BY created_at LIMIT 1", (grp, scope, scope))
                row = cur.fetchone()
        if row:
            row = dict(row)
            row['detail'] = json_loads(row.get('detail'), {}) or {}
        return row


class IndexTaskBook:
    def __init__(self, repo: MemoryTaskRepo | MysqlTaskRepo | None = None) -> None:
        if repo is not None:
            self.repo = repo
        elif use_memory_auth():
            self.repo = MemoryTaskRepo()
        else:
            self.repo = MysqlTaskRepo()
        self._lock = threading.Lock()

    def ensure_schema(self) -> bool:
        try:
            return bool(self.repo.ensure_schema())
        except Exception as exc:  # noqa: BLE001
            log.warning("index task schema failed: %s", exc)
            return False

    def get(self, task_id: str) -> dict | None:
        return self.repo.get(task_id)

    def list_all(self) -> list[dict]:
        return self.repo.list_all()

    def _overlap(self, grp: str, scope: str) -> dict | None:
        return self.repo.running_overlap(grp, scope)

    def accept(self, grp: str, kind: str, scope: str, actor_id: str, parent_id: str | None = None) -> tuple[dict | None, dict | None]:
        """返回 (新任务, 已有重叠任务)。有重叠时不新建。"""
        with self._lock, self.repo.accept_lock():
            hit = self._overlap(grp, scope)
            if hit:
                return None, hit
            row = {
                "id": uid("ix"),
                "grp": grp,
                "kind": kind,
                "scope": scope,
                "actor_id": actor_id,
                "status": "running",
                "parent_id": parent_id,
                "scanned": 0,
                "changed": 0,
                "failed": 0,
                "integrity": "unknown",
                "error": None,
                "detail": {},
                "created_at": _now(),
                "finished_at": None,
            }
            self.repo.insert(row)
            return row, None

    def finish(self, task_id: str, status: str, *, scanned: int = 0, changed: int = 0, failed: int = 0,
               error: str | None = None, detail: dict | None = None) -> None:
        integrity = "complete" if status == "done" and not failed else ("partial" if failed else status)
        if status == "partial":
            integrity = "partial"
        self.repo.update(task_id, {
            "status": status,
            "scanned": scanned,
            "changed": changed,
            "failed": failed,
            "integrity": integrity,
            "error": (error or "")[:255] or None,
            "detail": detail or {},
            "finished_at": _now(),
        })

    def public(self, row: dict) -> dict:
        return {
            "id": row["id"],
            "group": row.get("grp"),
            "kind": row.get("kind"),
            "scope": row.get("scope"),
            "actor_id": row.get("actor_id"),
            "status": row.get("status"),
            "parent_id": row.get("parent_id"),
            "scanned": row.get("scanned") or 0,
            "changed": row.get("changed") or 0,
            "failed": row.get("failed") or 0,
            "integrity": row.get("integrity") or "unknown",
            "error": row.get("error"),
            "detail": row.get("detail") or {},
            "created_at": str(row.get("created_at") or ""),
            "finished_at": str(row.get("finished_at") or "") or None,
        }
