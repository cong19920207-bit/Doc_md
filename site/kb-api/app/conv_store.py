# -*- coding: utf-8 -*-
"""云端对话：按账号隔离，数量不设上限、不自动淘汰；用户删除 = 账号级隐藏，数据保留。"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

import pymysql

from . import settings
from .auth_store import use_memory_auth
from .listing import like_arg, time_key
from .util import json_dumps, json_loads, uid

log = logging.getLogger("kb-api.convs")
PAGE_DEFAULT = 50
PAGE_MAX = 200
# STEP-Q07：会话执行权租期（秒）；每进入新阶段续期，崩溃后到期自动恢复
RUN_LEASE_SEC = 300


def clamp_page(offset: Any, limit: Any) -> tuple[int, int]:
    try:
        off = max(0, int(offset or 0))
    except (TypeError, ValueError):
        off = 0
    try:
        lim = int(limit or PAGE_DEFAULT)
    except (TypeError, ValueError):
        lim = PAGE_DEFAULT
    return off, min(max(1, lim), PAGE_MAX)

CONV_SCHEMA_SQL = (
    """
    CREATE TABLE IF NOT EXISTS kb_conversations (
      id VARCHAR(64) NOT NULL PRIMARY KEY,
      account_id VARCHAR(64) NOT NULL,
      title VARCHAR(255) NOT NULL,
      title_locked TINYINT NOT NULL DEFAULT 0,
      payload MEDIUMTEXT NULL,
      last_seq BIGINT NOT NULL DEFAULT 0,
      clear_seq BIGINT NOT NULL DEFAULT 0,
      hidden_at DATETIME(3) NULL,
      purged_at DATETIME(3) NULL,
      run_exec_id VARCHAR(64) NULL,
      run_until DATETIME(3) NULL,
      save_block_exec_id VARCHAR(64) NULL,
      created_at DATETIME(3) NOT NULL,
      updated_at DATETIME(3) NOT NULL,
      INDEX idx_kb_convs_account (account_id, updated_at)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """,
)

# 已有数据卷补列；新库由建表语句直接带上
CONV_EXTRA_COLUMNS = (
    ("last_seq", "ALTER TABLE kb_conversations ADD COLUMN last_seq BIGINT NOT NULL DEFAULT 0"),
    ("clear_seq", "ALTER TABLE kb_conversations ADD COLUMN clear_seq BIGINT NOT NULL DEFAULT 0"),
    ("hidden_at", "ALTER TABLE kb_conversations ADD COLUMN hidden_at DATETIME(3) NULL"),
    ("run_exec_id", "ALTER TABLE kb_conversations ADD COLUMN run_exec_id VARCHAR(64) NULL"),
    ("run_until", "ALTER TABLE kb_conversations ADD COLUMN run_until DATETIME(3) NULL"),
    ("save_block_exec_id", "ALTER TABLE kb_conversations ADD COLUMN save_block_exec_id VARCHAR(64) NULL"),
    ("purged_at", "ALTER TABLE kb_conversations ADD COLUMN purged_at DATETIME(3) NULL"),
)


def _now() -> datetime:
    return datetime.utcnow()


def _as_dt(value: Any) -> datetime | None:
    if value is None or isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(str(value).replace("T", " ").rstrip("Z"))
    except ValueError:
        return None


# STEP-A05：后台会话交互状态（筛选用）；hidden 优先于阻塞，阻塞优先于忙碌
ADMIN_STATES = ("idle", "busy", "blocked", "inaccessible")


def _row_state(row: dict, now: datetime) -> str:
    if row.get("hidden_at"):
        return "inaccessible"
    if row.get("save_block_exec_id"):
        return "blocked"
    until = _as_dt(row.get("run_until"))
    if row.get("run_exec_id") and until and until >= now:
        return "busy"
    return "idle"


def _admin_match(row: dict, f: dict, now: datetime) -> bool:
    if row.get("purged_at"):
        return False
    if f.get("account_id") and str(row.get("account_id")) != f["account_id"]:
        return False
    if f.get("conv_id") and str(row.get("id")) != f["conv_id"]:
        return False
    if f.get("q"):
        ids = f.get("q_conv_ids") or set()
        if f["q"] not in str(row.get("title") or "") and row["id"] not in ids:
            return False
    vis = f.get("visibility")
    if vis == "hidden" and not row.get("hidden_at"):
        return False
    if vis == "visible" and row.get("hidden_at"):
        return False
    cleared = f.get("cleared")
    if cleared == "yes" and not int(row.get("clear_seq") or 0):
        return False
    if cleared == "no" and int(row.get("clear_seq") or 0):
        return False
    if f.get("state") and _row_state(row, now) != f["state"]:
        return False
    rng = f.get("range")
    if rng:
        ts = _as_dt(row.get(f.get("time_col") or "updated_at"))
        if ts is None or not (rng["start"] <= ts < rng["end"]):
            return False
    return True


class MemoryConvRepo:
    def __init__(self) -> None:
        self.rows: dict[str, dict] = {}

    def ensure_schema(self) -> bool:
        return True

    def list_for(self, account_id: str, offset: int = 0, limit: int | None = None) -> list[dict]:
        items = [
            dict(r) for r in self.rows.values()
            if r.get("account_id") == account_id and not r.get("hidden_at")
        ]
        items.sort(key=lambda r: (str(r.get("updated_at") or ""), str(r.get("id"))), reverse=True)
        items = items[offset:]
        return items[:limit] if limit else items

    def list_all(self) -> list[dict]:
        items = [dict(r) for r in self.rows.values()]
        items.sort(key=lambda r: str(r.get("updated_at") or ""), reverse=True)
        return items

    def admin_page(self, filters: dict, before: tuple[str, str] | None, size: int, now: datetime) -> list[dict]:
        items = [dict(r) for r in self.rows.values() if _admin_match(r, filters, now)]
        items.sort(key=lambda r: (time_key(r.get("updated_at")), str(r["id"])), reverse=True)
        if before:
            items = [r for r in items if (time_key(r.get("updated_at")), str(r["id"])) < before]
        return items[: size + 1]

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

    def try_acquire(self, conv_id: str, exec_id: str, now: datetime, until: datetime) -> bool:
        row = self.rows.get(conv_id)
        if not row or row.get("save_block_exec_id"):
            return False
        holder, expire = row.get("run_exec_id"), row.get("run_until")
        if holder and expire and expire >= now:
            return False
        row["run_exec_id"], row["run_until"] = exec_id, until
        return True

    def renew(self, conv_id: str, exec_id: str, until: datetime) -> None:
        row = self.rows.get(conv_id)
        if row and row.get("run_exec_id") == exec_id:
            row["run_until"] = until

    def release(self, conv_id: str, exec_id: str) -> None:
        row = self.rows.get(conv_id)
        if row and row.get("run_exec_id") == exec_id:
            row["run_exec_id"], row["run_until"] = None, None

    def set_block(self, conv_id: str, exec_id: str | None, only_if: str | None = None) -> None:
        row = self.rows.get(conv_id)
        if not row:
            return
        if only_if is not None and row.get("save_block_exec_id") != only_if:
            return
        row["save_block_exec_id"] = exec_id


class MysqlConvRepo:
    def ensure_schema(self) -> bool:
        try:
            with self._conn() as conn:
                with conn.cursor() as cur:
                    for sql in CONV_SCHEMA_SQL:
                        cur.execute(sql)
                    cur.execute(
                        "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS "
                        "WHERE TABLE_SCHEMA=%s AND TABLE_NAME='kb_conversations'",
                        (settings.MYSQL_DATABASE,),
                    )
                    have = {row["COLUMN_NAME"] for row in (cur.fetchall() or [])}
                    for name, alter in CONV_EXTRA_COLUMNS:
                        if name not in have:
                            cur.execute(alter)
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

    def list_for(self, account_id: str, offset: int = 0, limit: int | None = None) -> list[dict]:
        sql = (
            "SELECT * FROM kb_conversations WHERE account_id=%s AND hidden_at IS NULL "
            "ORDER BY updated_at DESC, id DESC"
        )
        args: list[Any] = [account_id]
        if limit:
            sql += " LIMIT %s OFFSET %s"
            args.extend([int(limit), int(offset)])
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, args)
                return [dict(r) for r in (cur.fetchall() or [])]

    def list_all(self) -> list[dict]:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM kb_conversations ORDER BY updated_at DESC")
                return [dict(r) for r in (cur.fetchall() or [])]

    def admin_page(self, filters: dict, before: tuple[str, str] | None, size: int, now: datetime) -> list[dict]:
        """STEP-A05：后台会话列表，服务端筛选 + 游标（updated_at 倒序、id 倒序）。库异常直接抛出。"""
        sql = "SELECT * FROM kb_conversations WHERE purged_at IS NULL"
        args: list[Any] = []
        if filters.get("account_id"):
            sql += " AND account_id=%s"
            args.append(filters["account_id"])
        if filters.get("conv_id"):
            sql += " AND id=%s"
            args.append(filters["conv_id"])
        if filters.get("q"):
            ids = sorted(filters.get("q_conv_ids") or [])
            if ids:
                sql += f" AND (title LIKE %s OR id IN ({', '.join(['%s'] * len(ids))}))"
                args.extend([like_arg(filters["q"]), *ids])
            else:
                sql += " AND title LIKE %s"
                args.append(like_arg(filters["q"]))
        if filters.get("visibility") == "hidden":
            sql += " AND hidden_at IS NOT NULL"
        elif filters.get("visibility") == "visible":
            sql += " AND hidden_at IS NULL"
        if filters.get("cleared") == "yes":
            sql += " AND clear_seq>0"
        elif filters.get("cleared") == "no":
            sql += " AND clear_seq=0"
        state = filters.get("state")
        if state == "inaccessible":
            sql += " AND hidden_at IS NOT NULL"
        elif state == "blocked":
            sql += " AND hidden_at IS NULL AND save_block_exec_id IS NOT NULL"
        elif state == "busy":
            sql += (" AND hidden_at IS NULL AND save_block_exec_id IS NULL"
                    " AND run_exec_id IS NOT NULL AND run_until>=%s")
            args.append(now)
        elif state == "idle":
            sql += (" AND hidden_at IS NULL AND save_block_exec_id IS NULL"
                    " AND (run_exec_id IS NULL OR run_until IS NULL OR run_until<%s)")
            args.append(now)
        rng = filters.get("range")
        if rng:
            col = "created_at" if filters.get("time_col") == "created_at" else "updated_at"
            sql += f" AND {col}>=%s AND {col}<%s"
            args.extend([rng["start"], rng["end"]])
        if before:
            sql += " AND (updated_at<%s OR (updated_at=%s AND id<%s))"
            args.extend([before[0], before[0], before[1]])
        sql += " ORDER BY updated_at DESC, id DESC LIMIT %s"
        args.append(int(size) + 1)
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, args)
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
        for key in ("title", "title_locked", "payload", "updated_at", "hidden_at", "purged_at"):
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

    def try_acquire(self, conv_id: str, exec_id: str, now: datetime, until: datetime) -> bool:
        # 单条带条件 UPDATE：多设备同时抢占时只有一条命中
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE kb_conversations SET run_exec_id=%s, run_until=%s "
                    "WHERE id=%s AND save_block_exec_id IS NULL "
                    "AND (run_exec_id IS NULL OR run_until IS NULL OR run_until<%s)",
                    (exec_id, until, conv_id, now),
                )
                return cur.rowcount == 1

    def renew(self, conv_id: str, exec_id: str, until: datetime) -> None:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE kb_conversations SET run_until=%s WHERE id=%s AND run_exec_id=%s",
                    (until, conv_id, exec_id),
                )

    def release(self, conv_id: str, exec_id: str) -> None:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE kb_conversations SET run_exec_id=NULL, run_until=NULL "
                    "WHERE id=%s AND run_exec_id=%s",
                    (conv_id, exec_id),
                )

    def set_block(self, conv_id: str, exec_id: str | None, only_if: str | None = None) -> None:
        sql = "UPDATE kb_conversations SET save_block_exec_id=%s WHERE id=%s"
        args: list[Any] = [exec_id, conv_id]
        if only_if is not None:
            sql += " AND save_block_exec_id=%s"
            args.append(only_if)
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, args)


class ConvStore:
    def __init__(self, repo: MemoryConvRepo | MysqlConvRepo | None = None) -> None:
        if repo is not None:
            self.repo = repo
        elif use_memory_auth():
            self.repo = MemoryConvRepo()
        else:
            self.repo = MysqlConvRepo()
        # STEP-Q09：阻塞标记写库失败时的进程内备份（重启即失）
        self._block_fallback: dict[str, str] = {}

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
            "saveBlockedExecId": self._block_fallback.get(row["id"]) or row.get("save_block_exec_id") or None,
        }

    # ---------- STEP-Q07：会话执行权 ----------

    def acquire_run(self, conv_id: str, exec_id: str) -> tuple[str, str | None]:
        """返回 (ok|busy|blocked, 相关执行 id)。库异常直接抛出，由调用方按未开始处理。"""
        blocked = self._block_fallback.get(conv_id)
        if blocked:
            return "blocked", blocked
        now = _now()
        until = now + timedelta(seconds=RUN_LEASE_SEC)
        if self.repo.try_acquire(conv_id, exec_id, now, until):
            return "ok", None
        row = self.repo.get(conv_id) or {}
        if row.get("save_block_exec_id"):
            return "blocked", row.get("save_block_exec_id")
        return "busy", row.get("run_exec_id")

    def renew_run(self, conv_id: str, exec_id: str) -> None:
        try:
            self.repo.renew(conv_id, exec_id, _now() + timedelta(seconds=RUN_LEASE_SEC))
        except Exception as exc:  # noqa: BLE001
            log.warning("renew run failed: %s", exc)

    def release_run(self, conv_id: str, exec_id: str) -> None:
        try:
            self.repo.release(conv_id, exec_id)
        except Exception as exc:  # noqa: BLE001
            log.warning("release run failed: %s", exc)

    # ---------- STEP-Q09：保存阻塞 ----------

    def set_save_block(self, conv_id: str, exec_id: str) -> bool:
        """返回是否写进库；写库失败时仍在进程内阻塞该会话。"""
        try:
            self.repo.set_block(conv_id, exec_id)
            return True
        except Exception as exc:  # noqa: BLE001
            log.warning("set save block failed: %s", exc)
            self._block_fallback[conv_id] = exec_id
            return False

    def save_block_of(self, conv_id: str) -> str | None:
        if self._block_fallback.get(conv_id):
            return self._block_fallback[conv_id]
        row = self.repo.get(conv_id) or {}
        return row.get("save_block_exec_id") or None

    def clear_save_block(self, conv_id: str, exec_id: str) -> None:
        """只解除指定执行造成的阻塞；库写失败抛出，由调用方保持阻塞。"""
        if self._block_fallback.get(conv_id) == exec_id:
            self._block_fallback.pop(conv_id, None)
        self.repo.set_block(conv_id, None, only_if=exec_id)

    def list_ids(self, account_id: str) -> list[str]:
        return [str(r["id"]) for r in self.repo.list_for(account_id)]

    def list_public(self, account_id: str) -> list[dict]:
        return [self._public(r) for r in self.repo.list_for(account_id)]

    def list_page(self, account_id: str, offset: Any = 0, limit: Any = None) -> tuple[list[dict], int | None]:
        """按页读取未隐藏会话；多取一条判断是否还有下一页。"""
        off, lim = clamp_page(offset, limit)
        rows = self.repo.list_for(account_id, off, lim + 1)
        next_offset = off + lim if len(rows) > lim else None
        return [self._public(r) for r in rows[:lim]], next_offset

    def _owned_row(self, account_id: str, conv_id: str) -> dict | None:
        """本人可见的会话；已隐藏与非本人统一视为不存在。"""
        row = self.repo.get(conv_id)
        if not row or str(row.get("account_id")) != str(account_id) or row.get("hidden_at"):
            return None
        return row

    def list_all_public(self) -> list[dict]:
        try:
            rows = self.repo.list_all()
        except Exception as exc:  # noqa: BLE001
            log.warning("list all convs failed: %s", exc)
            rows = []
        return [{"id": r["id"], "account_id": r.get("account_id"), "title": r.get("title")} for r in rows]

    # ---------- STEP-A05：后台只读查阅（含已隐藏会话） ----------

    def admin_page(self, filters: dict, before: tuple[str, str] | None, size: int) -> tuple[list[dict], bool]:
        rows = self.repo.admin_page(filters, before, size, _now())
        return rows[:size], len(rows) > size

    def note_clear(self, conv_id: str, boundary: int) -> None:
        """清空边界同步到会话行。MySQL 由清空事务在同表写入，这里只对内存仓库生效（MySQL 的 update 不写该列）。"""
        if isinstance(self.repo, MemoryConvRepo):
            self.repo.update(conv_id, {"clear_seq": int(boundary)})

    def admin_get(self, conv_id: str) -> dict | None:
        """不按归属与隐藏过滤；已实际删除的会话不再返回，避免残留原文。"""
        row = self.repo.get(conv_id)
        if row and row.get("purged_at"):
            return None
        return row

    def is_purged(self, conv_id: str) -> bool:
        row = self.repo.get(conv_id)
        return bool(row and row.get("purged_at"))

    def mark_purged(self, conv_id: str) -> None:
        """先阻断读取与晚到写回：打上删除时间、对用户隐藏，并清掉展示缓存里的原文。"""
        now = _now()
        self.repo.update(conv_id, {
            "purged_at": now, "hidden_at": now, "title": "已删除",
            "payload": json_dumps({"messages": [], "lastChunks": [], "citationsOpen": {}}),
            "updated_at": now,
        })

    def interaction(self, row: dict, now: datetime | None = None) -> dict:
        """当前交互状态：忙碌与保存阻塞分开给出；进程内阻塞备份一并计入。"""
        now = now or _now()
        blocked = self._block_fallback.get(row["id"]) or row.get("save_block_exec_id") or None
        until = _as_dt(row.get("run_until"))
        busy = bool(row.get("run_exec_id") and until and until >= now)
        hidden = bool(row.get("hidden_at"))
        if hidden:
            state = "inaccessible"
        elif blocked:
            state = "blocked"
        elif busy:
            state = "busy"
        else:
            state = "idle"
        return {
            "state": state,
            "busy": busy,
            "running_exec_id": row.get("run_exec_id") if busy else None,
            "save_blocked": bool(blocked),
            "blocked_exec_id": blocked,
            "hidden": hidden,
        }

    def get_owned(self, account_id: str, conv_id: str) -> dict | None:
        row = self._owned_row(account_id, conv_id)
        return self._public(row) if row else None

    def create(self, account_id: str, body: dict | None = None) -> dict | None:
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
        row = self._owned_row(account_id, conv_id)
        if not row:
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
        """用户删除：只记隐藏时间，不物理删除；本人各端从此不可见、不可自行恢复。"""
        row = self._owned_row(account_id, conv_id)
        if not row:
            return False
        self.repo.update(conv_id, {"hidden_at": _now()})
        return True
