# -*- coding: utf-8 -*-
"""会话消息事实源：每条实际 User/Assistant 消息一行，服务端 seq 定序；清空边界按回合过滤。"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

import pymysql

from . import settings
from .auth_store import use_memory_auth
from .util import uid

log = logging.getLogger("kb-api.msgs")

COMPLETENESS = {"complete", "partial", "error_notice"}

MSG_SCHEMA_SQL = (
    """
    CREATE TABLE IF NOT EXISTS kb_conv_messages (
      id VARCHAR(64) NOT NULL PRIMARY KEY,
      conv_id VARCHAR(64) NOT NULL,
      seq BIGINT NOT NULL,
      round_id VARCHAR(64) NOT NULL,
      round_seq BIGINT NOT NULL,
      exec_id VARCHAR(64) NULL,
      role VARCHAR(16) NOT NULL,
      content MEDIUMTEXT,
      op_type VARCHAR(16) NOT NULL DEFAULT 'send',
      version_no INT NULL,
      is_current TINYINT NOT NULL DEFAULT 1,
      completeness VARCHAR(16) NOT NULL DEFAULT 'complete',
      client_request_id VARCHAR(64) NULL,
      source VARCHAR(16) NOT NULL DEFAULT 'live',
      created_at DATETIME(3) NOT NULL,
      UNIQUE KEY uk_conv_msg_seq (conv_id, seq),
      UNIQUE KEY uk_conv_msg_req (conv_id, client_request_id),
      INDEX idx_conv_msg_round (conv_id, round_seq),
      INDEX idx_conv_msg_round_id (round_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """,
    """
    CREATE TABLE IF NOT EXISTS kb_conv_clears (
      id VARCHAR(64) NOT NULL PRIMARY KEY,
      conv_id VARCHAR(64) NOT NULL,
      boundary_seq BIGINT NOT NULL,
      actor_id VARCHAR(64) NULL,
      created_at DATETIME(3) NOT NULL,
      INDEX idx_conv_clears_conv (conv_id, created_at)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """,
)


class DuplicateRequest(Exception):
    """同一会话内 client_request_id 已写过 User 消息。"""

    def __init__(self, existing: dict) -> None:
        super().__init__("duplicate_request")
        self.existing = existing


def _now() -> datetime:
    return datetime.utcnow()


class MemoryMsgRepo:
    def __init__(self) -> None:
        self.rows: list[dict] = []
        self.last_seq: dict[str, int] = {}
        self.clear_seq_map: dict[str, int] = {}
        self.clears: list[dict] = []

    def ensure_schema(self) -> bool:
        return True

    def find_message(self, msg_id):
        return next((dict(r) for r in self.rows if r['id'] == msg_id), None)

    def next_seq(self, conv_id: str) -> int:
        seq = self.last_seq.get(conv_id, 0) + 1
        self.last_seq[conv_id] = seq
        return seq

    def find_by_request(self, conv_id: str, client_request_id: str) -> dict | None:
        for r in self.rows:
            if r["conv_id"] == conv_id and r.get("client_request_id") == client_request_id:
                return dict(r)
        return None

    def insert(self, row: dict) -> None:
        crid = row.get("client_request_id")
        if crid and self.find_by_request(row["conv_id"], crid):
            raise DuplicateRequest(self.find_by_request(row["conv_id"], crid) or {})
        self.rows.append(dict(row))

    def insert_many(self, rows: list[dict]) -> None:
        # STEP-Q06：迁移批量写入
        self.rows.extend(dict(r) for r in rows)

    def list_range(self, conv_id: str, min_round_seq: int, after_seq: int, limit: int | None) -> list[dict]:
        items = [
            dict(r) for r in self.rows
            if r["conv_id"] == conv_id and int(r["round_seq"]) > min_round_seq and int(r["seq"]) > after_seq
        ]
        items.sort(key=lambda r: int(r["seq"]))
        return items[:limit] if limit else items

    def list_round(self, conv_id: str, round_id: str) -> list[dict]:
        items = [dict(r) for r in self.rows if r["conv_id"] == conv_id and r["round_id"] == round_id]
        items.sort(key=lambda r: int(r["seq"]))
        return items

    def purge_conv(self, conv_id: str) -> None:
        """实际删除：去掉该会话的消息与清空记录。"""
        self.rows = [r for r in self.rows if r["conv_id"] != conv_id]
        self.clears = [c for c in self.clears if c["conv_id"] != conv_id]
        self.last_seq.pop(conv_id, None)
        self.clear_seq_map.pop(conv_id, None)

    def get_by_ids(self, conv_id: str, ids: list[str]) -> list[dict]:
        want = set(ids)
        return [dict(r) for r in self.rows if r["conv_id"] == conv_id and r["id"] in want]

    def set_current(self, conv_id: str, round_id: str, msg_id: str) -> None:
        for r in self.rows:
            if r["conv_id"] == conv_id and r["round_id"] == round_id and r["role"] == "assistant":
                r["is_current"] = 1 if r["id"] == msg_id else 0

    def get_clear_seq(self, conv_id: str) -> int:
        return self.clear_seq_map.get(conv_id, 0)

    def set_clear(self, conv_id: str, actor_id: str | None) -> int:
        boundary = self.last_seq.get(conv_id, 0)
        self.clear_seq_map[conv_id] = boundary
        self.clears.append({
            "id": uid("clr"),
            "conv_id": conv_id,
            "boundary_seq": boundary,
            "actor_id": actor_id,
            "created_at": _now(),
        })
        return boundary

    # ---------- STEP-A05：后台只读 ----------

    def search(self, q: str, limit: int) -> list[dict]:
        hits = [dict(r) for r in self.rows if q in str(r.get("content") or "")]
        hits.sort(key=lambda r: (str(r.get("created_at") or ""), int(r["seq"])), reverse=True)
        return hits[:limit]

    def stats(self, conv_ids: list[str]) -> dict[str, dict]:
        want = set(conv_ids)
        out: dict[str, dict] = {}
        for r in self.rows:
            if r["conv_id"] not in want:
                continue
            s = out.setdefault(r["conv_id"], {"msgs": 0, "rounds": set(), "last_msg_at": None})
            s["msgs"] += 1
            if r["role"] == "user":
                s["rounds"].add(r["round_id"])
            if s["last_msg_at"] is None or r["created_at"] > s["last_msg_at"]:
                s["last_msg_at"] = r["created_at"]
        for s in out.values():
            s["rounds"] = len(s["rounds"])
        for c in self.clears:
            if c["conv_id"] not in want:
                continue
            s = out.setdefault(c["conv_id"], {"msgs": 0, "rounds": 0, "last_msg_at": None})
            s["clear_count"] = s.get("clear_count", 0) + 1
            if not s.get("last_clear_at") or c["created_at"] > s["last_clear_at"]:
                s["last_clear_at"] = c["created_at"]
        return out

    def list_clears(self, conv_id: str) -> list[dict]:
        items = [dict(c) for c in self.clears if c["conv_id"] == conv_id]
        items.sort(key=lambda c: (int(c["boundary_seq"]), str(c.get("created_at") or "")))
        return items


class MysqlMsgRepo:
    def find_message(self, msg_id):
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT * FROM kb_conv_messages WHERE id=%s', (msg_id,))
                row = cur.fetchone()
        return dict(row) if row else None

    def _conn(self, autocommit: bool = True):
        return pymysql.connect(
            host=settings.MYSQL_HOST,
            port=settings.MYSQL_PORT,
            user=settings.MYSQL_USER,
            password=settings.MYSQL_PASSWORD,
            database=settings.MYSQL_DATABASE,
            charset="utf8mb4",
            autocommit=autocommit,
            cursorclass=pymysql.cursors.DictCursor,
            connect_timeout=3,
            read_timeout=5,
            write_timeout=5,
        )

    def ensure_schema(self) -> bool:
        try:
            with self._conn() as conn:
                with conn.cursor() as cur:
                    for sql in MSG_SCHEMA_SQL:
                        cur.execute(sql)
            return True
        except Exception as exc:  # noqa: BLE001
            log.warning("ensure msg schema failed: %s", exc)
            return False

    def next_seq(self, conv_id: str) -> int:
        # LAST_INSERT_ID(expr) 在同一连接内原子取号，并发下不重号
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE kb_conversations SET last_seq=LAST_INSERT_ID(last_seq+1) WHERE id=%s",
                    (conv_id,),
                )
                if cur.rowcount == 0:
                    raise LookupError("conversation_not_found")
                cur.execute("SELECT LAST_INSERT_ID() AS s")
                return int((cur.fetchone() or {}).get("s") or 0)

    def find_by_request(self, conv_id: str, client_request_id: str) -> dict | None:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM kb_conv_messages WHERE conv_id=%s AND client_request_id=%s",
                    (conv_id, client_request_id),
                )
                row = cur.fetchone()
        return dict(row) if row else None

    _COLS = (
        "id", "conv_id", "seq", "round_id", "round_seq", "exec_id", "role", "content",
        "op_type", "version_no", "is_current", "completeness", "client_request_id",
        "source", "created_at",
    )

    def insert_many(self, rows: list[dict]) -> None:
        """STEP-Q06：一个会话的迁移消息同一事务写入，失败整体回滚，不留半截会话。"""
        if not rows:
            return
        cols = self._COLS
        sql = (
            f"INSERT INTO kb_conv_messages ({', '.join(cols)}) "
            f"VALUES ({', '.join(['%s'] * len(cols))})"
        )
        with self._conn(autocommit=False) as conn:
            try:
                with conn.cursor() as cur:
                    cur.executemany(sql, [tuple(r.get(c) for c in cols) for r in rows])
                conn.commit()
            except Exception:
                conn.rollback()
                raise

    def insert(self, row: dict) -> None:
        cols = (
            "id", "conv_id", "seq", "round_id", "round_seq", "exec_id", "role", "content",
            "op_type", "version_no", "is_current", "completeness", "client_request_id",
            "source", "created_at",
        )
        sql = (
            f"INSERT INTO kb_conv_messages ({', '.join(cols)}) "
            f"VALUES ({', '.join(['%s'] * len(cols))})"
        )
        try:
            with self._conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(sql, tuple(row.get(c) for c in cols))
        except pymysql.err.IntegrityError as exc:
            crid = row.get("client_request_id")
            existing = self.find_by_request(row["conv_id"], crid) if crid else None
            if existing:
                raise DuplicateRequest(existing) from exc
            raise

    def list_range(self, conv_id: str, min_round_seq: int, after_seq: int, limit: int | None) -> list[dict]:
        sql = (
            "SELECT * FROM kb_conv_messages WHERE conv_id=%s AND round_seq>%s AND seq>%s "
            "ORDER BY seq ASC"
        )
        args: list[Any] = [conv_id, int(min_round_seq), int(after_seq)]
        if limit:
            sql += " LIMIT %s"
            args.append(int(limit))
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, args)
                return [dict(r) for r in (cur.fetchall() or [])]

    def list_round(self, conv_id: str, round_id: str) -> list[dict]:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM kb_conv_messages WHERE conv_id=%s AND round_id=%s ORDER BY seq ASC",
                    (conv_id, round_id),
                )
                return [dict(r) for r in (cur.fetchall() or [])]

    def get_by_ids(self, conv_id: str, ids: list[str]) -> list[dict]:
        if not ids:
            return []
        marks = ", ".join(["%s"] * len(ids))
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"SELECT * FROM kb_conv_messages WHERE conv_id=%s AND id IN ({marks})",
                    (conv_id, *ids),
                )
                return [dict(r) for r in (cur.fetchall() or [])]

    def purge_conv(self, conv_id: str) -> None:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM kb_conv_messages WHERE conv_id=%s", (conv_id,))
                cur.execute("DELETE FROM kb_conv_clears WHERE conv_id=%s", (conv_id,))

    def set_current(self, conv_id: str, round_id: str, msg_id: str) -> None:
        # 同一事务内切换：任一时刻本回合只有一个当前版本
        with self._conn(autocommit=False) as conn:
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE kb_conv_messages SET is_current=0 "
                        "WHERE conv_id=%s AND round_id=%s AND role='assistant' AND id<>%s",
                        (conv_id, round_id, msg_id),
                    )
                    cur.execute(
                        "UPDATE kb_conv_messages SET is_current=1 WHERE conv_id=%s AND id=%s",
                        (conv_id, msg_id),
                    )
                conn.commit()
            except Exception:
                conn.rollback()
                raise

    def get_clear_seq(self, conv_id: str) -> int:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT clear_seq FROM kb_conversations WHERE id=%s", (conv_id,))
                row = cur.fetchone()
        return int((row or {}).get("clear_seq") or 0)

    def set_clear(self, conv_id: str, actor_id: str | None) -> int:
        # 边界取清空当下的 last_seq，同一条 UPDATE 内读取，避免与取号交错
        with self._conn(autocommit=False) as conn:
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE kb_conversations SET clear_seq=last_seq WHERE id=%s",
                        (conv_id,),
                    )
                    cur.execute("SELECT clear_seq FROM kb_conversations WHERE id=%s", (conv_id,))
                    boundary = int((cur.fetchone() or {}).get("clear_seq") or 0)
                    cur.execute(
                        "INSERT INTO kb_conv_clears (id, conv_id, boundary_seq, actor_id, created_at) "
                        "VALUES (%s,%s,%s,%s,%s)",
                        (uid("clr"), conv_id, boundary, actor_id, _now()),
                    )
                conn.commit()
                return boundary
            except Exception:
                conn.rollback()
                raise

    # ---------- STEP-A05：后台只读 ----------

    def search(self, q: str, limit: int) -> list[dict]:
        text = str(q or "").replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, conv_id, seq, round_id, round_seq, exec_id, role, content, version_no, "
                    "is_current, completeness, created_at FROM kb_conv_messages "
                    "WHERE content LIKE %s ORDER BY created_at DESC, seq DESC LIMIT %s",
                    (f"%{text}%", int(limit)),
                )
                return [dict(r) for r in (cur.fetchall() or [])]

    def stats(self, conv_ids: list[str]) -> dict[str, dict]:
        if not conv_ids:
            return {}
        marks = ", ".join(["%s"] * len(conv_ids))
        out: dict[str, dict] = {}
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT conv_id, COUNT(*) AS msgs, "
                    "COUNT(DISTINCT CASE WHEN role='user' THEN round_id END) AS rounds, "
                    f"MAX(created_at) AS last_msg_at FROM kb_conv_messages WHERE conv_id IN ({marks}) "
                    "GROUP BY conv_id",
                    tuple(conv_ids),
                )
                for r in cur.fetchall() or []:
                    out[r["conv_id"]] = {
                        "msgs": int(r["msgs"] or 0),
                        "rounds": int(r["rounds"] or 0),
                        "last_msg_at": r["last_msg_at"],
                    }
                cur.execute(
                    "SELECT conv_id, COUNT(*) AS n, MAX(created_at) AS last_at FROM kb_conv_clears "
                    f"WHERE conv_id IN ({marks}) GROUP BY conv_id",
                    tuple(conv_ids),
                )
                for r in cur.fetchall() or []:
                    s = out.setdefault(r["conv_id"], {"msgs": 0, "rounds": 0, "last_msg_at": None})
                    s["clear_count"] = int(r["n"] or 0)
                    s["last_clear_at"] = r["last_at"]
        return out

    def list_clears(self, conv_id: str) -> list[dict]:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM kb_conv_clears WHERE conv_id=%s ORDER BY boundary_seq ASC, created_at ASC",
                    (conv_id,),
                )
                return [dict(r) for r in (cur.fetchall() or [])]


class MsgStore:
    def __init__(self, repo: MemoryMsgRepo | MysqlMsgRepo | None = None) -> None:
        if repo is not None:
            self.repo = repo
        elif use_memory_auth():
            self.repo = MemoryMsgRepo()
        else:
            self.repo = MysqlMsgRepo()
        # STEP-Q14：保存成功后的通知（交给记忆索引后台写入）；通知失败不影响保存结果
        self.on_saved = None

    def ensure_schema(self) -> bool:
        try:
            return bool(self.repo.ensure_schema())
        except Exception as exc:  # noqa: BLE001
            log.warning("msg schema failed: %s", exc)
            return False

    def _notify(self, row: dict) -> None:
        if self.on_saved is None:
            return
        try:
            self.on_saved(dict(row))
        except Exception as exc:  # noqa: BLE001
            log.warning("msg saved hook failed: %s", exc)

    def append_user(
        self,
        conv_id: str,
        content: str,
        client_request_id: str | None,
        exec_id: str | None,
        op_type: str = "send",
    ) -> dict:
        """先查重再写；写失败直接抛出，由调用方按 user_save_fail 处理。"""
        if client_request_id:
            existing = self.repo.find_by_request(conv_id, client_request_id)
            if existing:
                raise DuplicateRequest(existing)
        seq = self.repo.next_seq(conv_id)
        row = {
            "id": uid("m"),
            "conv_id": conv_id,
            "seq": seq,
            "round_id": uid("lr"),
            "round_seq": seq,
            "exec_id": exec_id,
            "role": "user",
            "content": content,
            "op_type": op_type,
            "version_no": None,
            "is_current": 1,
            "completeness": "complete",
            "client_request_id": client_request_id or None,
            "source": "live",
            "created_at": _now(),
        }
        self.repo.insert(row)
        self._notify(row)
        return row

    def append_assistant(
        self,
        conv_id: str,
        user_row: dict,
        exec_id: str | None,
        content: str,
        completeness: str,
        op_type: str = "send",
        version_no: int = 1,
        is_current: int = 1,
    ) -> dict:
        """普通发送写第 1 版并直接为当前版本；刷新由调用方传入新版本号且 is_current=0，采用另行切换。"""
        if completeness not in COMPLETENESS:
            completeness = "partial"
        seq = self.repo.next_seq(conv_id)
        row = {
            "id": uid("m"),
            "conv_id": conv_id,
            "seq": seq,
            "round_id": user_row["round_id"],
            "round_seq": int(user_row["round_seq"]),
            "exec_id": exec_id,
            "role": "assistant",
            "content": content,
            "op_type": op_type,
            "version_no": int(version_no),
            "is_current": 1 if is_current else 0,
            "completeness": completeness,
            "client_request_id": None,
            "source": "live",
            "created_at": _now(),
        }
        self.repo.insert(row)
        self._notify(row)
        return row

    def clear_seq(self, conv_id: str) -> int:
        return self.repo.get_clear_seq(conv_id)

    def effective_messages(self, conv_id: str, after_seq: int = 0, limit: int | None = None) -> list[dict]:
        """当前有效范围：只含清空边界之后开始的回合。L1、Memory、旧版本回看都必须经此读取。"""
        boundary = self.repo.get_clear_seq(conv_id)
        return self.repo.list_range(conv_id, boundary, int(after_seq or 0), limit)

    def clear(self, conv_id: str, actor_id: str | None) -> int:
        return self.repo.set_clear(conv_id, actor_id)

    def find_request(self, conv_id: str, client_request_id: str) -> dict | None:
        return self.repo.find_by_request(conv_id, client_request_id)

    # ---------- STEP-Q06：旧云端历史迁移 ----------

    def has_messages(self, conv_id: str) -> bool:
        """不按清空边界过滤：只要消息表里有这个会话的任何记录，迁移就跳过它。"""
        return bool(self.repo.list_range(conv_id, -1, 0, 1))

    def next_seq(self, conv_id: str) -> int:
        return self.repo.next_seq(conv_id)

    def insert_migrated(self, rows: list[dict]) -> None:
        self.repo.insert_many(rows)

    # ---------- STEP-Q08：逻辑回合与回答版本 ----------

    def round_rows(self, conv_id: str, round_id: str) -> list[dict]:
        """本回合全部消息，不按清空边界过滤；只供写入侧判重使用，不得用于用户侧读取。"""
        return self.repo.list_round(conv_id, round_id)

    def visible_round(self, conv_id: str, round_id: str) -> list[dict]:
        """本回合全部消息（含各版本）；回合在清空边界之前则视为不可见，返回空。"""
        rows = self.repo.list_round(conv_id, round_id)
        if not rows or int(rows[0]["round_seq"]) <= self.repo.get_clear_seq(conv_id):
            return []
        return rows

    def next_version_no(self, conv_id: str, round_id: str) -> int:
        nums = [
            int(r.get("version_no") or 0)
            for r in self.repo.list_round(conv_id, round_id)
            if r["role"] == "assistant"
        ]
        return (max(nums) if nums else 0) + 1

    def get_by_ids(self, conv_id: str, ids: list[str]) -> list[dict]:
        return self.repo.get_by_ids(conv_id, list(ids))

    def purge_conv(self, conv_id: str) -> None:
        self.repo.purge_conv(conv_id)

    def adopt_version(self, conv_id: str, round_id: str, msg_id: str) -> None:
        self.repo.set_current(conv_id, round_id, msg_id)

    # ---------- STEP-A05：后台只读查阅（不经清空边界，只供「对话审计」） ----------

    def admin_search(self, q: str, cap: int) -> tuple[list[dict], bool]:
        """正文关键词命中的消息，最多 cap 条；第二项表示是否被截断。库异常抛出。"""
        rows = self.repo.search(q, cap + 1)
        return rows[:cap], len(rows) > cap

    def admin_stats(self, conv_ids: list[str]) -> dict[str, dict]:
        return self.repo.stats(list(conv_ids))

    def admin_messages(self, conv_id: str) -> list[dict]:
        """全部消息（含清空前与各回答版本），按服务端 seq 升序。"""
        return self.repo.list_range(conv_id, -1, 0, None)

    def clears(self, conv_id: str) -> list[dict]:
        return self.repo.list_clears(conv_id)

    @staticmethod
    def excerpt(content: str, q: str, width: int = 36) -> str:
        """命中处前后各取一段，超出部分以省略号表示。"""
        text = str(content or "")
        pos = text.find(q) if q else -1
        if pos < 0:
            return text[: width * 2] + ("…" if len(text) > width * 2 else "")
        start = max(0, pos - width)
        end = min(len(text), pos + len(q) + width)
        return ("…" if start else "") + text[start:end] + ("…" if end < len(text) else "")

    @staticmethod
    def public(row: dict) -> dict:
        return {
            "id": row["id"],
            "seq": int(row["seq"]),
            "round_id": row["round_id"],
            "exec_id": row.get("exec_id"),
            "role": row["role"],
            "content": row.get("content") or "",
            "op_type": row.get("op_type") or "send",
            "version_no": row.get("version_no"),
            "is_current": bool(row.get("is_current", 1)),
            "completeness": row.get("completeness") or "complete",
            "source": row.get("source") or "live",
            "created_at": str(row.get("created_at") or ""),
        }
