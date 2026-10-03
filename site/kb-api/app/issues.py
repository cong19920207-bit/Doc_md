# -*- coding: utf-8 -*-
"""STEP-A17：轻量人工问题记录。只存管理摘要和对象 id，不复制对话原文。
来源被实际删除后摘录失效。不改赞踩，也不因发布自动关闭。"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

import pymysql

from . import settings
from . import listing
from .auth_store import use_memory_auth
from .util import uid

log = logging.getLogger("kb-api.issues")

STATUSES = {
    "open": "未处理",
    "doing": "处理中",
    "closed": "已关闭",
}
CATEGORIES = {
    "route": "路由",
    "context": "语境",
    "retrieve": "检索",
    "source": "来源",
    "generate": "生成/检查",
    "save": "保存",
    "perm": "权限",
    "ux": "体验",
    "other": "其他/未确定",
}
CLOSE_REASONS = {
    "verified": "已验证修复",
    "not_defect": "复核非缺陷",
    "external": "资料待补/外部处理",
    "unrepro": "无法复现",
}
SOURCE_TYPES = ("", "feedback", "version", "exec", "index_task", "diag", "conv")

ISSUE_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS kb_issues (
  id VARCHAR(64) NOT NULL PRIMARY KEY,
  title VARCHAR(80) NOT NULL,
  symptom VARCHAR(500) NOT NULL,
  category VARCHAR(16) NOT NULL,
  status VARCHAR(16) NOT NULL,
  assignee_id VARCHAR(64) NULL,
  close_reason VARCHAR(16) NULL,
  close_basis VARCHAR(500) NULL,
  source_type VARCHAR(16) NOT NULL,
  source_id VARCHAR(64) NULL,
  conv_id VARCHAR(64) NULL,
  source_deleted TINYINT NOT NULL DEFAULT 0,
  created_by VARCHAR(64) NULL,
  created_at DATETIME(3) NOT NULL,
  updated_at DATETIME(3) NOT NULL,
  INDEX idx_kb_issues_status (status, updated_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
"""

NOTE_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS kb_issue_notes (
  id VARCHAR(64) NOT NULL PRIMARY KEY,
  issue_id VARCHAR(64) NOT NULL,
  actor_id VARCHAR(64) NULL,
  body VARCHAR(500) NOT NULL,
  created_at DATETIME(3) NOT NULL,
  INDEX idx_kb_issue_notes (issue_id, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
"""


def _now() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]


def _clip(value: Any, limit: int) -> str:
    return str(value or "").strip()[:limit]


class MemoryIssueRepo:
    def __init__(self) -> None:
        self.rows: dict[str, dict] = {}
        self.notes: list[dict] = []

    def ensure_schema(self) -> bool:
        return True

    def insert(self, row: dict) -> None:
        self.rows[row["id"]] = dict(row)

    def update(self, issue_id: str, fields: dict) -> None:
        row = self.rows.get(issue_id)
        if row:
            row.update(fields)

    def get(self, issue_id: str) -> dict | None:
        row = self.rows.get(issue_id)
        return dict(row) if row else None

    def list_all(self) -> list[dict]:
        items = [dict(r) for r in self.rows.values()]
        items.sort(key=lambda r: str(r.get("updated_at") or ""), reverse=True)
        return items

    def add_note(self, row: dict) -> None:
        self.notes.append(dict(row))

    def notes_of(self, issue_id: str) -> list[dict]:
        items = [dict(n) for n in self.notes if n["issue_id"] == issue_id]
        items.sort(key=lambda n: str(n.get("created_at") or ""))
        return items

    def for_conv(self, conv_id: str) -> list[dict]:
        return [
            dict(r) for r in self.rows.values()
            if r.get("conv_id") == conv_id or (r.get("source_type") == "conv" and r.get("source_id") == conv_id)
        ]

    def redact_notes(self, issue_id: str) -> None:
        for note in self.notes:
            if note['issue_id'] == issue_id:
                note['body'] = ''

    def for_source(self, source_type, source_id):
        return [dict(r) for r in self.rows.values() if r.get('source_type') == source_type and r.get('source_id') == source_id]

    def page(self, cursor, size, status=''):
        return listing.paginate([r for r in self.rows.values() if not status or r.get('status') == status],
                                ts_of=lambda r: r['updated_at'], id_of=lambda r: r['id'], cursor=cursor, size=size)


class MysqlIssueRepo:
    def page(self, cursor, size, status=''):
        before = listing.decode_cursor(cursor)
        sql, args = 'SELECT * FROM kb_issues WHERE 1=1', []
        if status:
            sql += ' AND status=%s'
            args.append(status)
        if before:
            sql += ' AND (updated_at<%s OR (updated_at=%s AND id<%s))'
            args.extend([before[0], before[0], before[1]])
        sql += ' ORDER BY updated_at DESC, id DESC LIMIT %s'
        args.append(size + 1)
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, args)
                rows = [dict(r) for r in cur.fetchall() or []]
        more, rows = len(rows) > size, rows[:size]
        nxt = listing.encode_cursor(rows[-1]['updated_at'], rows[-1]['id']) if more and rows else None
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
                cur.execute(ISSUE_SCHEMA_SQL)
                cur.execute(NOTE_SCHEMA_SQL)
        return True

    def insert(self, row: dict) -> None:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO kb_issues (id, title, symptom, category, status, assignee_id, close_reason, "
                    "close_basis, source_type, source_id, conv_id, source_deleted, created_by, created_at, updated_at) "
                    "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                    (row["id"], row["title"], row["symptom"], row["category"], row["status"], row.get("assignee_id"),
                     row.get("close_reason"), row.get("close_basis"), row["source_type"], row.get("source_id"),
                     row.get("conv_id"), int(row.get("source_deleted") or 0), row.get("created_by"),
                     row["created_at"], row["updated_at"]),
                )

    def update(self, issue_id: str, fields: dict) -> None:
        allowed = (
            "title", "symptom", "category", "status", "assignee_id", "close_reason", "close_basis",
            "source_deleted", "updated_at",
        )
        cols = [k for k in allowed if k in fields]
        if not cols:
            return
        sql = "UPDATE kb_issues SET " + ", ".join(f"{k}=%s" for k in cols) + " WHERE id=%s"
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, [fields[k] for k in cols] + [issue_id])

    def get(self, issue_id: str) -> dict | None:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM kb_issues WHERE id=%s", (issue_id,))
                row = cur.fetchone()
        return dict(row) if row else None

    def list_all(self) -> list[dict]:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM kb_issues ORDER BY updated_at DESC, id DESC LIMIT 200")
                return [dict(r) for r in (cur.fetchall() or [])]

    def add_note(self, row: dict) -> None:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO kb_issue_notes (id, issue_id, actor_id, body, created_at) VALUES (%s,%s,%s,%s,%s)",
                    (row["id"], row["issue_id"], row.get("actor_id"), row["body"], row["created_at"]),
                )

    def notes_of(self, issue_id: str) -> list[dict]:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM kb_issue_notes WHERE issue_id=%s ORDER BY created_at ASC, id ASC",
                    (issue_id,),
                )
                return [dict(r) for r in (cur.fetchall() or [])]

    def redact_notes(self, issue_id: str) -> None:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute('UPDATE kb_issue_notes SET body=%s WHERE issue_id=%s', ('', issue_id))

    def for_source(self, source_type, source_id):
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT * FROM kb_issues WHERE source_type=%s AND source_id=%s', (source_type, source_id))
                return [dict(r) for r in cur.fetchall() or []]

    def for_conv(self, conv_id: str) -> list[dict]:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM kb_issues WHERE conv_id=%s OR (source_type='conv' AND source_id=%s)",
                    (conv_id, conv_id),
                )
                return [dict(r) for r in (cur.fetchall() or [])]


class IssueBook:
    def __init__(self, repo: MemoryIssueRepo | MysqlIssueRepo | None = None) -> None:
        if repo is not None:
            self.repo = repo
        elif use_memory_auth():
            self.repo = MemoryIssueRepo()
        else:
            self.repo = MysqlIssueRepo()

    def ensure_schema(self) -> bool:
        try:
            return bool(self.repo.ensure_schema())
        except Exception as exc:  # noqa: BLE001
            log.warning("issue schema failed: %s", exc)
            return False

    def on_publish(self, _package_id: str | None = None) -> None:
        """发布成功不自动关闭问题。"""
        return None

    def create(self, actor_id: str, body: dict) -> dict:
        title = _clip(body.get("title"), 80)
        if not title:
            raise ValueError("需要标题")
        category = str(body.get("category") or "other")
        if category not in CATEGORIES:
            raise ValueError("分类无效")
        source_type = str(body.get("source_type") or "")
        if source_type not in SOURCE_TYPES:
            raise ValueError("来源类型无效")
        now = _now()
        conv_id = _clip(body.get("conv_id"), 64) or None
        source_id = _clip(body.get("source_id"), 64) or None
        if source_type == "conv" and source_id and not conv_id:
            conv_id = source_id
        row = {
            "id": uid("is"),
            "title": title,
            "symptom": _clip(body.get("symptom"), 500),
            "category": category,
            "status": "open",
            "assignee_id": None,
            "close_reason": None,
            "close_basis": None,
            "source_type": source_type,
            "source_id": source_id,
            "conv_id": conv_id,
            "source_deleted": 0,
            "created_by": actor_id,
            "created_at": now,
            "updated_at": now,
        }
        self.repo.insert(row)
        return row

    def get(self, issue_id: str) -> dict | None:
        return self.repo.get(issue_id)

    def list_all(self) -> list[dict]:
        return self.repo.list_all()

    def notes(self, issue_id: str) -> list[dict]:
        return self.repo.notes_of(issue_id)

    def add_note(self, issue_id: str, actor_id: str, text: str) -> dict:
        row = self.repo.get(issue_id)
        if not row:
            raise KeyError("未找到该问题")
        body = _clip(text, 500)
        if not body:
            raise ValueError("记录不能为空")
        note = {"id": uid("in"), "issue_id": issue_id, "actor_id": actor_id, "body": body, "created_at": _now()}
        self.repo.add_note(note)
        self.repo.update(issue_id, {"updated_at": note["created_at"]})
        return note

    def apply(self, issue_id: str, actor_id: str, body: dict, assignee_ok) -> dict:
        """改状态、处理人或分类。处理记录只追加。关闭必须有结论；已验证修复必须标明复测过。"""
        row = self.repo.get(issue_id)
        if not row:
            raise KeyError("未找到该问题")
        fields: dict[str, Any] = {"updated_at": _now()}
        if "category" in body and body.get("category"):
            if body["category"] not in CATEGORIES:
                raise ValueError("分类无效")
            fields["category"] = body["category"]
        if "assignee_id" in body:
            aid = _clip(body.get("assignee_id"), 64)
            if aid and not assignee_ok(aid):
                raise ValueError("处理人需要有问题处理权限")
            fields["assignee_id"] = aid or None
        if body.get("status"):
            status = str(body["status"])
            if status not in STATUSES:
                raise ValueError("状态无效")
            if status == "closed":
                reason = str(body.get("close_reason") or "")
                basis = _clip(body.get("close_basis"), 500)
                if reason not in CLOSE_REASONS or not basis:
                    raise ValueError("关闭需要结论和依据")
                if reason == "verified" and not body.get("retested"):
                    raise ValueError("未经复测不能标已验证修复")
                fields.update(status="closed", close_reason=reason, close_basis=basis)
            elif row.get("status") == "closed":
                why = _clip(body.get("reopen_reason"), 500)
                if not why:
                    raise ValueError("重新打开需要原因")
                self.add_note(issue_id, actor_id, "重新打开：" + why)
                fields.update(status=status, close_reason=None, close_basis=None)
            else:
                fields["status"] = status
        self.repo.update(issue_id, fields)
        return self.repo.get(issue_id) or row

    def invalidate_conv(self, conv_id: str) -> int:
        """实际删除后：摘录清空，标来源已删除。问题行和处理过程还在。"""
        n = 0
        for row in self.repo.for_conv(conv_id):
            self.repo.update(row["id"], {"title": '来源已删除', "symptom": "", "close_basis": '', "source_deleted": 1, "updated_at": _now()})
            self.repo.redact_notes(row['id'])
            n += 1
        return n

    def public(self, row: dict, names: dict[str, str] | None = None) -> dict:
        names = names or {}
        deleted = bool(int(row.get("source_deleted") or 0))
        return {
            "id": row["id"],
            "title": '来源已删除' if deleted else (row.get("title") or ""),
            "symptom": "" if deleted else (row.get("symptom") or ""),
            "category": row.get("category") or "other",
            "category_label": CATEGORIES.get(row.get("category") or "", "其他/未确定"),
            "status": row.get("status") or "open",
            "status_label": STATUSES.get(row.get("status") or "", "未处理"),
            "assignee_id": row.get("assignee_id"),
            "assignee_username": names.get(str(row.get("assignee_id") or "")),
            "close_reason": row.get("close_reason"),
            "close_reason_label": CLOSE_REASONS.get(row.get("close_reason") or "", ""),
            "close_basis": '' if deleted else (row.get("close_basis") or ""),
            "source_type": row.get("source_type") or "",
            "source_id": row.get("source_id"),
            "conv_id": row.get("conv_id"),
            "source_deleted": deleted,
            "source_note": "来源已删除" if deleted else "",
            "created_at": str(row.get("created_at") or ""),
            "updated_at": str(row.get("updated_at") or ""),
            "notes": [
                {
                    "id": n["id"],
                    "actor_id": n.get("actor_id"),
                    "actor_username": names.get(str(n.get("actor_id") or "")),
                    "body": '' if deleted else (n.get("body") or ""),
                    "created_at": str(n.get("created_at") or ""),
                }
                for n in self.notes(row["id"])
            ],
        }
