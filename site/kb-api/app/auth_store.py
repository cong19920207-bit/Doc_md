# -*- coding: utf-8 -*-
"""账号、角色、会话、登录锁定与登录审计。密码不明文。"""
from __future__ import annotations

import base64
import logging
import os
import secrets
import threading
from datetime import datetime, timedelta
from typing import Any

import pymysql
from cryptography.exceptions import InvalidKey
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from . import settings
from .util import json_dumps, json_loads, uid

log = logging.getLogger("kb-api.auth")

PERM_CHECKBOX = (
    "知识问答",
    "进管理模块",
    "配置查看",
    "配置编辑",
    "Prompt查看",
    "Prompt编辑",
    "Prompt调试",
    "配置发布",
    "重建",
    "问答明细",
    "功能热度",
    "对话审计",
    "健康",
    "操作审计",
    "反馈汇总",
    "知识源查看",
    "数据概览",
    "问题处理",
)
# G-ADM-E06：本版新增的动作权限，不自动附加给已有角色
NEW_PERMS = (
    "配置查看",
    "配置编辑",
    "Prompt查看",
    "Prompt编辑",
    "Prompt调试",
    "配置发布",
    "知识源查看",
    "数据概览",
    "问题处理",
)
# 已注册但对应功能尚未接入，勾选后页面显示「未接入」
# STEP-A15：「数据概览」已接入运行概览，不再列为未接入
PENDING_PERMS = ()
# 已停用的旧权限码：库内保留供迁移报告，不再授予任何能力
RETIRED_PERMS = {
    "配置": {
        "was": "读取并直接保存当前配置（含系统/改写 Prompt）",
        "now": "不再授予任何能力；请按需分配配置查看、配置编辑、Prompt查看、Prompt编辑",
    },
}
ROLE_SUPER_ID = "role-super"
ROLE_USER_ID = "role-user"
ROLE_SUPER_NAME = "超级管理员"
ROLE_USER_NAME = "普通用户"

LOGIN_FAIL_MSG = "用户名或密码不正确"
LOGIN_LOCK_MSG = "登录失败，请稍后重试"
OLD_PASSWORD_MSG = "原密码不正确"

AUTH_SCHEMA_SQL = (
    """
    CREATE TABLE IF NOT EXISTS kb_roles (
      id VARCHAR(64) NOT NULL PRIMARY KEY,
      name VARCHAR(64) NOT NULL,
      is_super TINYINT NOT NULL DEFAULT 0,
      is_preset TINYINT NOT NULL DEFAULT 0,
      created_at DATETIME(3) NOT NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """,
    """
    CREATE TABLE IF NOT EXISTS kb_role_permissions (
      role_id VARCHAR(64) NOT NULL,
      perm_code VARCHAR(64) NOT NULL,
      PRIMARY KEY (role_id, perm_code)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """,
    """
    CREATE TABLE IF NOT EXISTS kb_accounts (
      id VARCHAR(64) NOT NULL PRIMARY KEY,
      username VARCHAR(64) NOT NULL,
      password_hash VARCHAR(255) NOT NULL,
      role_id VARCHAR(64) NOT NULL,
      enabled TINYINT NOT NULL DEFAULT 1,
      tenant_id VARCHAR(64) NULL,
      created_at DATETIME(3) NOT NULL,
      updated_at DATETIME(3) NOT NULL,
      UNIQUE KEY uk_kb_accounts_username (username)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """,
    """
    CREATE TABLE IF NOT EXISTS kb_sessions (
      id VARCHAR(64) NOT NULL PRIMARY KEY,
      account_id VARCHAR(64) NOT NULL,
      created_at DATETIME(3) NOT NULL,
      expires_at DATETIME(3) NOT NULL,
      revoked_at DATETIME(3) NULL,
      INDEX idx_kb_sessions_account (account_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """,
    """
    CREATE TABLE IF NOT EXISTS kb_login_locks (
      username VARCHAR(64) NOT NULL PRIMARY KEY,
      fail_count INT NOT NULL DEFAULT 0,
      locked_until DATETIME(3) NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """,
    """
    CREATE TABLE IF NOT EXISTS kb_audit_logs (
      id VARCHAR(64) NOT NULL PRIMARY KEY,
      actor_id VARCHAR(64) NULL,
      actor_username VARCHAR(64) NULL,
      action VARCHAR(64) NOT NULL,
      object VARCHAR(255) NULL,
      ip VARCHAR(64) NULL,
      created_at DATETIME(3) NOT NULL,
      detail JSON NULL,
      INDEX idx_kb_audit_created (created_at)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """,
)


# G-ADM-E07：审计补列；旧记录这些列为空，按「旧记录」显示，不补造
AUDIT_EXTRA_COLUMNS = (
    ("op_id", "ALTER TABLE kb_audit_logs ADD COLUMN op_id VARCHAR(64) NULL"),
    ("result", "ALTER TABLE kb_audit_logs ADD COLUMN result VARCHAR(16) NULL"),
    ("error_code", "ALTER TABLE kb_audit_logs ADD COLUMN error_code VARCHAR(64) NULL"),
    ("object_type", "ALTER TABLE kb_audit_logs ADD COLUMN object_type VARCHAR(32) NULL"),
    ("actor_role", "ALTER TABLE kb_audit_logs ADD COLUMN actor_role VARCHAR(64) NULL"),
    ("changed_fields", "ALTER TABLE kb_audit_logs ADD COLUMN changed_fields JSON NULL"),
    ("before_ver", "ALTER TABLE kb_audit_logs ADD COLUMN before_ver VARCHAR(64) NULL"),
    ("after_ver", "ALTER TABLE kb_audit_logs ADD COLUMN after_ver VARCHAR(64) NULL"),
    ("relation", "ALTER TABLE kb_audit_logs ADD COLUMN relation JSON NULL"),
    ("reason", "ALTER TABLE kb_audit_logs ADD COLUMN reason VARCHAR(255) NULL"),
)
AUDIT_FIELDS = tuple(name for name, _ in AUDIT_EXTRA_COLUMNS)
AUDIT_JSON_FIELDS = ("changed_fields", "relation")
AUDIT_RESULTS = ("accepted", "success", "failed", "unknown")
# 新登记事件编码：由后续 STEP 负责写入
AUDIT_ACTIONS_PLANNED = (
    "config_draft_save", "config_validate", "config_publish", "config_publish_fail",
    "config_rollback", "config_draft_discard", "debug_run", "index_backfill", "index_retry",
    "conv_delete", "issue_create", "issue_update", "issue_close", "issue_reopen", "sensitive_read",
)
# 审计不写秘密与被查看正文：键名含以下片段即丢弃
_AUDIT_SECRET_PARTS = (
    "password", "secret", "token", "jwt", "authorization", "cookie", "session",
    "api_key", "apikey", "key_pem", "private", "prompt", "content", "answer", "query",
)


# 改启停/改角色串行执行，保证「最后一名启用超管」检查与写入之间不被穿插
_SUPER_GUARD = threading.Lock()


class AuditUnavailable(Exception):
    """审计写入不可用：高风险写须拒绝。"""


AUDIT_FILTER_KEYS = ("action", "actor_username", "result", "object", "object_type", "op_id")


def _audit_match(row: dict, filters: dict) -> bool:
    for key in AUDIT_FILTER_KEYS:
        want = filters.get(key)
        if not want:
            continue
        if key == "result" and want == "legacy":
            if row.get("result") is not None:
                return False
            continue
        if str(row.get(key) or "") != str(want):
            return False
    return True


def _safe_audit_value(value: Any) -> Any:
    if isinstance(value, dict):
        out = {}
        for key, val in value.items():
            low = str(key).lower()
            if any(part in low for part in _AUDIT_SECRET_PARTS):
                continue
            out[key] = _safe_audit_value(val)
        return out
    if isinstance(value, list):
        return [_safe_audit_value(v) for v in value]
    return value


def use_memory_auth() -> bool:
    return os.environ.get("KB_AUTH_MEMORY", "").strip().lower() in {"1", "true", "yes"}


def _now_naive() -> datetime:
    return datetime.utcnow()


def hash_password(password: str, iterations: int | None = None) -> str:
    iters = int(iterations or settings.PBKDF2_ITERATIONS)
    salt = os.urandom(16)
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=iters)
    dk = kdf.derive(password.encode("utf-8"))
    return "pbkdf2_sha256$%s$%s$%s" % (
        iters,
        base64.b64encode(salt).decode("ascii"),
        base64.b64encode(dk).decode("ascii"),
    )


def verify_password(password: str, stored: str) -> bool:
    try:
        algo, iter_s, salt_b64, dk_b64 = (stored or "").split("$")
        if algo != "pbkdf2_sha256":
            return False
        salt = base64.b64decode(salt_b64)
        dk = base64.b64decode(dk_b64)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=len(dk),
            salt=salt,
            iterations=int(iter_s),
        )
        kdf.verify(password.encode("utf-8"), dk)
        return True
    except (ValueError, InvalidKey, TypeError) as exc:  # noqa: BLE001
        log.debug("password verify failed: %s", exc)
        return False


def _dt(value: Any) -> datetime | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value
    text = str(value)
    for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


class MemoryAuthRepo:
    """测试用内存库，语义与 MySQL 表一致。"""

    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.roles: dict[str, dict] = {}
        self.role_perms: dict[str, set[str]] = {}
        self.accounts: dict[str, dict] = {}
        self.by_username: dict[str, str] = {}
        self.sessions: dict[str, dict] = {}
        self.locks: dict[str, dict] = {}
        self.audits: list[dict] = []

    def ensure_schema(self) -> bool:
        return True

    def count_accounts(self) -> int:
        return len(self.accounts)

    def upsert_role(self, row: dict) -> None:
        self.roles[row["id"]] = dict(row)

    def set_role_perms(self, role_id: str, perms: list[str]) -> None:
        self.role_perms[role_id] = set(perms)

    def get_role(self, role_id: str) -> dict | None:
        row = self.roles.get(role_id)
        return dict(row) if row else None

    def get_role_perms(self, role_id: str) -> set[str]:
        return set(self.role_perms.get(role_id) or [])

    def insert_account(self, row: dict) -> None:
        if row["username"] in self.by_username:
            raise ValueError("username taken")
        self.accounts[row["id"]] = dict(row)
        self.by_username[row["username"]] = row["id"]

    def get_account(self, account_id: str) -> dict | None:
        row = self.accounts.get(account_id)
        return dict(row) if row else None

    def get_account_by_username(self, username: str) -> dict | None:
        aid = self.by_username.get(username)
        return self.get_account(aid) if aid else None

    def update_password_hash(self, account_id: str, password_hash: str, updated_at: datetime) -> None:
        row = self.accounts.get(account_id)
        if not row:
            return
        row["password_hash"] = password_hash
        row["updated_at"] = updated_at

    def insert_session(self, row: dict) -> None:
        self.sessions[row["id"]] = dict(row)

    def get_session(self, session_id: str) -> dict | None:
        row = self.sessions.get(session_id)
        return dict(row) if row else None

    def revoke_session(self, session_id: str, revoked_at: datetime) -> None:
        row = self.sessions.get(session_id)
        if row and row.get("revoked_at") is None:
            row["revoked_at"] = revoked_at

    def revoke_account_sessions(self, account_id: str, revoked_at: datetime) -> None:
        for row in self.sessions.values():
            if row.get("account_id") == account_id and row.get("revoked_at") is None:
                row["revoked_at"] = revoked_at

    def get_lock(self, username: str) -> dict | None:
        row = self.locks.get(username)
        return dict(row) if row else None

    def set_lock(self, username: str, fail_count: int, locked_until: datetime | None) -> None:
        self.locks[username] = {
            "username": username,
            "fail_count": int(fail_count),
            "locked_until": locked_until,
        }

    def insert_audit(self, row: dict) -> None:
        self.audits.append(dict(row))

    def update_audit(self, audit_id: str, fields: dict) -> bool:
        for row in self.audits:
            if row.get("id") == audit_id:
                row.update(fields)
                return True
        return False

    def list_audits(self) -> list[dict]:
        return [dict(x) for x in reversed(self.audits)]

    def page_audits(self, filters: dict, before: tuple[str, str] | None, size: int) -> tuple[list[dict], bool]:
        from .listing import time_key
        rows = [dict(x) for x in self.audits if _audit_match(x, filters)]
        rows.sort(key=lambda r: (time_key(r.get("created_at")), str(r.get("id") or "")), reverse=True)
        if before:
            rows = [r for r in rows if (time_key(r.get("created_at")), str(r.get("id") or "")) < before]
        return rows[:size], len(rows) > size

    def list_accounts(self) -> list[dict]:
        return [dict(x) for x in self.accounts.values()]

    def list_roles(self) -> list[dict]:
        return [dict(x) for x in self.roles.values()]

    def update_account_fields(self, account_id: str, fields: dict) -> None:
        row = self.accounts.get(account_id)
        if not row:
            return
        old_name = row.get("username")
        row.update(fields)
        if "username" in fields and old_name in self.by_username:
            self.by_username.pop(old_name, None)
            self.by_username[row["username"]] = account_id


class MysqlAuthRepo:
    """已有 MySQL 卷上 CREATE IF NOT EXISTS 补表。"""

    def ensure_schema(self) -> bool:
        try:
            with self._conn() as conn:
                with conn.cursor() as cur:
                    for sql in AUTH_SCHEMA_SQL:
                        cur.execute(sql)
                    cur.execute(
                        "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS "
                        "WHERE TABLE_SCHEMA=%s AND TABLE_NAME='kb_audit_logs'",
                        (settings.MYSQL_DATABASE,),
                    )
                    have = {row["COLUMN_NAME"] for row in (cur.fetchall() or [])}
                    for name, alter in AUDIT_EXTRA_COLUMNS:
                        if name not in have:
                            cur.execute(alter)
            return True
        except Exception as exc:  # noqa: BLE001
            log.warning("ensure auth schema failed: %s", exc)
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

    def count_accounts(self) -> int:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) AS n FROM kb_accounts")
                row = cur.fetchone() or {}
        return int(row.get("n") or 0)

    def upsert_role(self, row: dict) -> None:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO kb_roles (id, name, is_super, is_preset, created_at) "
                    "VALUES (%s,%s,%s,%s,%s) "
                    "ON DUPLICATE KEY UPDATE name=VALUES(name), is_super=VALUES(is_super), "
                    "is_preset=VALUES(is_preset)",
                    (row["id"], row["name"], row["is_super"], row["is_preset"], row["created_at"]),
                )

    def set_role_perms(self, role_id: str, perms: list[str]) -> None:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM kb_role_permissions WHERE role_id=%s", (role_id,))
                for code in perms:
                    cur.execute(
                        "INSERT INTO kb_role_permissions (role_id, perm_code) VALUES (%s,%s)",
                        (role_id, code),
                    )

    def get_role(self, role_id: str) -> dict | None:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM kb_roles WHERE id=%s", (role_id,))
                row = cur.fetchone()
        return dict(row) if row else None

    def get_role_perms(self, role_id: str) -> set[str]:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT perm_code FROM kb_role_permissions WHERE role_id=%s",
                    (role_id,),
                )
                rows = cur.fetchall() or []
        return {str(r["perm_code"]) for r in rows}

    def insert_account(self, row: dict) -> None:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO kb_accounts (id, username, password_hash, role_id, enabled, "
                    "tenant_id, created_at, updated_at) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                    (
                        row["id"],
                        row["username"],
                        row["password_hash"],
                        row["role_id"],
                        row["enabled"],
                        row.get("tenant_id"),
                        row["created_at"],
                        row["updated_at"],
                    ),
                )

    def get_account(self, account_id: str) -> dict | None:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM kb_accounts WHERE id=%s", (account_id,))
                row = cur.fetchone()
        return dict(row) if row else None

    def get_account_by_username(self, username: str) -> dict | None:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM kb_accounts WHERE username=%s", (username,))
                row = cur.fetchone()
        return dict(row) if row else None

    def update_password_hash(self, account_id: str, password_hash: str, updated_at: datetime) -> None:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE kb_accounts SET password_hash=%s, updated_at=%s WHERE id=%s",
                    (password_hash, updated_at, account_id),
                )

    def insert_session(self, row: dict) -> None:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO kb_sessions (id, account_id, created_at, expires_at, revoked_at) "
                    "VALUES (%s,%s,%s,%s,%s)",
                    (
                        row["id"],
                        row["account_id"],
                        row["created_at"],
                        row["expires_at"],
                        row.get("revoked_at"),
                    ),
                )

    def get_session(self, session_id: str) -> dict | None:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM kb_sessions WHERE id=%s", (session_id,))
                row = cur.fetchone()
        return dict(row) if row else None

    def revoke_session(self, session_id: str, revoked_at: datetime) -> None:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE kb_sessions SET revoked_at=%s "
                    "WHERE id=%s AND revoked_at IS NULL",
                    (revoked_at, session_id),
                )

    def revoke_account_sessions(self, account_id: str, revoked_at: datetime) -> None:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE kb_sessions SET revoked_at=%s "
                    "WHERE account_id=%s AND revoked_at IS NULL",
                    (revoked_at, account_id),
                )

    def get_lock(self, username: str) -> dict | None:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM kb_login_locks WHERE username=%s", (username,))
                row = cur.fetchone()
        return dict(row) if row else None

    def set_lock(self, username: str, fail_count: int, locked_until: datetime | None) -> None:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO kb_login_locks (username, fail_count, locked_until) "
                    "VALUES (%s,%s,%s) ON DUPLICATE KEY UPDATE "
                    "fail_count=VALUES(fail_count), locked_until=VALUES(locked_until)",
                    (username, int(fail_count), locked_until),
                )

    def insert_audit(self, row: dict) -> None:
        extra = [name for name in AUDIT_FIELDS if row.get(name) is not None]
        cols = ["id", "actor_id", "actor_username", "action", "object", "ip", "created_at", "detail"] + extra
        args = [
            row["id"],
            row.get("actor_id"),
            row.get("actor_username"),
            row["action"],
            row.get("object"),
            row.get("ip"),
            row["created_at"],
            json_dumps(row.get("detail") or {}),
        ] + [
            json_dumps(row[name]) if name in AUDIT_JSON_FIELDS else row[name]
            for name in extra
        ]
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"INSERT INTO kb_audit_logs ({', '.join(cols)}) "
                    f"VALUES ({','.join(['%s'] * len(cols))})",
                    args,
                )

    def update_audit(self, audit_id: str, fields: dict) -> bool:
        allowed = set(AUDIT_FIELDS) | {"object", "detail"}
        sets = []
        args: list[Any] = []
        for key, value in fields.items():
            if key not in allowed:
                continue
            sets.append(f"{key}=%s")
            args.append(json_dumps(value) if key in AUDIT_JSON_FIELDS or key == "detail" else value)
        if not sets:
            return False
        args.append(audit_id)
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(f"UPDATE kb_audit_logs SET {', '.join(sets)} WHERE id=%s", args)
                return cur.rowcount > 0

    def list_audits(self) -> list[dict]:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM kb_audit_logs ORDER BY created_at DESC, id DESC")
                rows = cur.fetchall() or []
        out = []
        for row in rows:
            item = dict(row)
            raw = item.get("detail")
            if isinstance(raw, str):
                item["detail"] = json_loads(raw, {})
            for name in AUDIT_JSON_FIELDS:
                if isinstance(item.get(name), str):
                    item[name] = json_loads(item[name], None)
            out.append(item)
        return out

    def page_audits(self, filters: dict, before: tuple[str, str] | None, size: int) -> tuple[list[dict], bool]:
        sql = "SELECT * FROM kb_audit_logs WHERE 1=1"
        args: list[Any] = []
        for key in AUDIT_FILTER_KEYS:
            want = filters.get(key)
            if not want:
                continue
            if key == "result" and want == "legacy":
                sql += " AND result IS NULL"
                continue
            sql += f" AND {key}=%s"
            args.append(str(want))
        if before:
            sql += " AND (created_at < %s OR (created_at = %s AND id < %s))"
            args.extend([before[0], before[0], before[1]])
        sql += " ORDER BY created_at DESC, id DESC LIMIT %s"
        args.append(int(size) + 1)
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, args)
                rows = cur.fetchall() or []
        out = []
        for row in rows:
            item = dict(row)
            for name in ("detail",) + AUDIT_JSON_FIELDS:
                if isinstance(item.get(name), str):
                    item[name] = json_loads(item[name], {} if name == "detail" else None)
            out.append(item)
        return out[:size], len(out) > size

    def list_accounts(self) -> list[dict]:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM kb_accounts")
                return [dict(r) for r in (cur.fetchall() or [])]

    def list_roles(self) -> list[dict]:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM kb_roles")
                return [dict(r) for r in (cur.fetchall() or [])]

    def update_account_fields(self, account_id: str, fields: dict) -> None:
        allowed = {"role_id", "enabled", "updated_at"}
        sets = []
        args: list[Any] = []
        for key, value in fields.items():
            if key not in allowed:
                continue
            sets.append(f"{key}=%s")
            args.append(value)
        if not sets:
            return
        args.append(account_id)
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"UPDATE kb_accounts SET {', '.join(sets)} WHERE id=%s",
                    args,
                )


class AuthStore:
    """账号体系业务：引导超管、Session、锁定、改密、审计打点。"""

    def __init__(self, repo: MemoryAuthRepo | MysqlAuthRepo | None = None) -> None:
        if repo is not None:
            self.repo = repo
        elif use_memory_auth():
            self.repo = MemoryAuthRepo()
        else:
            self.repo = MysqlAuthRepo()
        self._now: datetime | None = None

    def set_now(self, value: datetime | None) -> None:
        """测试时钟：不改产品 TTL。"""
        self._now = value

    def now(self) -> datetime:
        return self._now or _now_naive()

    def ensure_schema(self) -> bool:
        try:
            return bool(self.repo.ensure_schema())
        except Exception as exc:  # noqa: BLE001
            log.warning("auth schema failed: %s", exc)
            return False

    def bootstrap_if_empty(
        self,
        username: str | None = None,
        password: str | None = None,
    ) -> bool:
        """仅账号表为空时创建超管与预置普通用户角色；不重置已有哈希。"""
        try:
            if self.repo.count_accounts() > 0:
                return False
        except Exception as exc:  # noqa: BLE001
            log.warning("count accounts failed: %s", exc)
            return False
        user = (username if username is not None else settings.KB_BOOTSTRAP_USER).strip()
        pw = password if password is not None else settings.KB_BOOTSTRAP_PASSWORD
        if not user or not pw:
            log.warning("empty account table but bootstrap user/password missing")
            return False
        now = self.now()
        self.repo.upsert_role({
            "id": ROLE_SUPER_ID,
            "name": ROLE_SUPER_NAME,
            "is_super": 1,
            "is_preset": 1,
            "created_at": now,
        })
        self.repo.set_role_perms(ROLE_SUPER_ID, list(PERM_CHECKBOX))
        self.repo.upsert_role({
            "id": ROLE_USER_ID,
            "name": ROLE_USER_NAME,
            "is_super": 0,
            "is_preset": 1,
            "created_at": now,
        })
        self.repo.set_role_perms(ROLE_USER_ID, ["知识问答"])
        self.create_account(user, pw, ROLE_SUPER_ID, enabled=True, account_id="acct-bootstrap")
        log.info("bootstrapped superadmin username=%s", user)
        return True

    def create_account(
        self,
        username: str,
        password: str,
        role_id: str,
        enabled: bool = True,
        account_id: str | None = None,
    ) -> dict:
        now = self.now()
        row = {
            "id": account_id or uid("acct"),
            "username": username,
            "password_hash": hash_password(password),
            "role_id": role_id,
            "enabled": 1 if enabled else 0,
            "tenant_id": None,
            "created_at": now,
            "updated_at": now,
        }
        self.repo.insert_account(row)
        return row

    def role_perm_set(self, role_id: str) -> set[str]:
        return self.repo.get_role_perms(role_id)

    def hydrate_account(self, account: dict | None) -> dict | None:
        if not account:
            return None
        role = self.repo.get_role(str(account["role_id"])) or {}
        perms = self.repo.get_role_perms(str(account["role_id"]))
        out = dict(account)
        out["enabled"] = bool(out.get("enabled"))
        out["role_name"] = role.get("name") or ""
        out["is_super"] = bool(role.get("is_super"))
        # 停用的旧码不进入授权集合
        out["permissions"] = {p for p in perms if p not in RETIRED_PERMS}
        return out

    def sync_super_perms(self) -> None:
        """启动时把超管角色的权限清单补全为当前完整清单；其他角色不动。"""
        try:
            for role in self.repo.list_roles():
                if role.get("is_super"):
                    self.repo.set_role_perms(str(role["id"]), list(PERM_CHECKBOX))
        except Exception as exc:  # noqa: BLE001
            log.warning("sync super perms failed: %s", exc)

    def perm_migration_report(self) -> list[dict]:
        """持有已停用旧码的非超管角色清单，供超管重新分配。"""
        counts: dict[str, int] = {}
        for acc in self.repo.list_accounts():
            rid = str(acc.get("role_id") or "")
            counts[rid] = counts.get(rid, 0) + 1
        out = []
        for role in self.repo.list_roles():
            if role.get("is_super"):
                continue
            perms = self.repo.get_role_perms(str(role["id"]))
            retired = sorted(p for p in perms if p in RETIRED_PERMS)
            if not retired:
                continue
            out.append({
                "role_id": role["id"],
                "role_name": role.get("name") or "",
                "retired": retired,
                "was": [RETIRED_PERMS[p]["was"] for p in retired],
                "now": [RETIRED_PERMS[p]["now"] for p in retired],
                "current_permissions": sorted(p for p in perms if p in PERM_CHECKBOX),
                "account_count": counts.get(str(role["id"]), 0),
            })
        return out

    def has_perm(self, account: dict | None, perm: str) -> bool:
        if not account:
            return False
        if account.get("is_super"):
            return True
        return perm in (account.get("permissions") or set())

    def get_live_account(self, session_id: str | None) -> dict | None:
        if not session_id:
            return None
        try:
            sess = self.repo.get_session(session_id)
        except Exception as exc:  # noqa: BLE001
            log.warning("get session failed: %s", exc)
            return None
        if not sess:
            return None
        if sess.get("revoked_at") is not None:
            return None
        expires = _dt(sess.get("expires_at"))
        if expires is None or expires <= self.now():
            return None
        account = self.hydrate_account(self.repo.get_account(str(sess["account_id"])))
        if not account or not account.get("enabled"):
            return None
        return account

    def _locked(self, username: str) -> bool:
        row = self.repo.get_lock(username)
        if not row:
            return False
        until = _dt(row.get("locked_until"))
        return until is not None and until > self.now()

    def _bump_fail(self, username: str) -> None:
        row = self.repo.get_lock(username) or {"fail_count": 0, "locked_until": None}
        fail_count = int(row.get("fail_count") or 0) + 1
        locked_until = _dt(row.get("locked_until"))
        if fail_count >= settings.AUTH_LOCK_FAILS:
            locked_until = self.now() + timedelta(seconds=settings.AUTH_LOCK_SECONDS)
        self.repo.set_lock(username, fail_count, locked_until)

    def _clear_fail(self, username: str) -> None:
        self.repo.set_lock(username, 0, None)

    def write_audit(
        self,
        action: str,
        *,
        actor_id: str | None = None,
        actor_username: str | None = None,
        object_: str | None = None,
        ip: str | None = None,
        detail: dict | None = None,
        **extra: Any,
    ) -> bool:
        """尽力写入：失败只记日志，不影响调用方。"""
        try:
            self.repo.insert_audit(self._audit_row(action, actor_id, actor_username, object_, ip, detail, extra))
            return True
        except Exception as exc:  # noqa: BLE001
            log.warning("insert audit failed: %s", exc)
            return False

    def _audit_row(
        self,
        action: str,
        actor_id: str | None,
        actor_username: str | None,
        object_: str | None,
        ip: str | None,
        detail: dict | None,
        extra: dict,
    ) -> dict:
        safe = dict(detail or {})
        for key in list(safe.keys()):
            if "password" in key.lower() or "secret" in key.lower() or key.lower() in {"jwt", "token"}:
                safe.pop(key, None)
        row = {
            "id": uid("aud"),
            "actor_id": actor_id,
            "actor_username": actor_username,
            "action": action,
            "object": object_,
            "ip": ip or "",
            "created_at": self.now(),
            "detail": _safe_audit_value(safe),
        }
        for name in AUDIT_FIELDS:
            if extra.get(name) is not None:
                val = extra[name]
                row[name] = _safe_audit_value(val) if name in AUDIT_JSON_FIELDS else val
        return row

    # ---------- G-ADM-E07：高风险写两段记录 ----------

    audit_counters: dict[str, int] | None = None

    def _bump_counter(self, name: str) -> None:
        if self.audit_counters is None:
            self.audit_counters = {}
        self.audit_counters[name] = self.audit_counters.get(name, 0) + 1

    def audit_health(self) -> dict:
        """进程内审计失败计数（重启清零）。"""
        c = self.audit_counters or {}
        return {
            "read_audit_failures": c.get("read_audit_failures", 0),
            "result_audit_failures": c.get("result_audit_failures", 0),
            "blocked_high_risk": c.get("blocked_high_risk", 0),
        }

    def begin_audit(
        self,
        action: str,
        *,
        actor: dict | None,
        object_: str | None = None,
        ip: str | None = None,
        detail: dict | None = None,
        **extra: Any,
    ) -> str:
        """高风险写受理：先写一行 accepted，写不进去抛 AuditUnavailable，调用方须拒绝操作。"""
        actor = actor or {}
        extra.setdefault("actor_role", actor.get("role_name") or None)
        row = self._audit_row(
            action,
            str(actor.get("id") or "") or None,
            str(actor.get("username") or "") or None,
            object_,
            ip,
            detail,
            extra,
        )
        row["op_id"] = row["id"]
        row["result"] = "accepted"
        try:
            self.repo.insert_audit(row)
        except Exception as exc:  # noqa: BLE001
            log.warning("begin audit failed action=%s: %s", action, exc)
            self._bump_counter("blocked_high_risk")
            raise AuditUnavailable(str(exc)) from exc
        return row["id"]

    def finish_audit(self, op_id: str, result: str, **fields: Any) -> bool:
        """写结果：失败时该行停在 accepted（待核对），不重做操作。"""
        upd: dict[str, Any] = {"result": result if result in AUDIT_RESULTS else "unknown"}
        for key, value in fields.items():
            if value is None:
                continue
            if key == "detail":
                upd["detail"] = _safe_audit_value(dict(value))
            elif key in AUDIT_JSON_FIELDS:
                upd[key] = _safe_audit_value(value)
            elif key in AUDIT_FIELDS or key == "object":
                upd[key] = value
        try:
            ok = bool(self.repo.update_audit(op_id, upd))
        except Exception as exc:  # noqa: BLE001
            log.warning("finish audit failed op=%s: %s", op_id, exc)
            ok = False
        if not ok:
            self._bump_counter("result_audit_failures")
        return ok

    def record_sensitive_read(
        self,
        *,
        actor: dict | None,
        object_type: str,
        object_id: str,
        ip: str | None = None,
    ) -> bool:
        """敏感正文读取：尽力记录，不写被查看正文；失败不阻断读取。"""
        actor = actor or {}
        ok = self.write_audit(
            "sensitive_read",
            actor_id=str(actor.get("id") or "") or None,
            actor_username=str(actor.get("username") or "") or None,
            object_=object_id,
            ip=ip,
            detail={},
            object_type=object_type,
            actor_role=actor.get("role_name") or None,
            result="success",
        )
        if not ok:
            self._bump_counter("read_audit_failures")
        return ok

    def login(self, username: str, password: str, ip: str = "") -> dict:
        name = (username or "").strip()
        if self._locked(name):
            self.write_audit(
                "login_fail",
                actor_username=name,
                ip=ip,
                detail={"reason": "locked"},
            )
            return {"ok": False, "locked": True, "message": LOGIN_LOCK_MSG, "status": 401}
        account = self.hydrate_account(self.repo.get_account_by_username(name))
        if (
            not account
            or not account.get("enabled")
            or not verify_password(password or "", str(account.get("password_hash") or ""))
        ):
            self._bump_fail(name)
            self.write_audit(
                "login_fail",
                actor_id=(account or {}).get("id"),
                actor_username=name,
                ip=ip,
                detail={"reason": "bad_credentials"},
            )
            return {"ok": False, "locked": False, "message": LOGIN_FAIL_MSG, "status": 401}
        self._clear_fail(name)
        now = self.now()
        sid = secrets.token_urlsafe(32)
        self.repo.insert_session({
            "id": sid,
            "account_id": account["id"],
            "created_at": now,
            "expires_at": now + timedelta(seconds=settings.AUTH_SESSION_SECONDS),
            "revoked_at": None,
        })
        self.write_audit(
            "login_success",
            actor_id=str(account["id"]),
            actor_username=name,
            ip=ip,
            detail={},
        )
        return {"ok": True, "session_id": sid, "account": account, "status": 200}

    def logout(self, session_id: str | None) -> None:
        if not session_id:
            return
        try:
            self.repo.revoke_session(session_id, self.now())
        except Exception as exc:  # noqa: BLE001
            log.warning("logout revoke failed: %s", exc)

    def change_password(self, account: dict, old_password: str, new_password: str, ip: str = "") -> dict:
        if not verify_password(old_password or "", str(account.get("password_hash") or "")):
            return {"ok": False, "message": OLD_PASSWORD_MSG, "status": 400}
        if not (new_password or "").strip():
            return {"ok": False, "message": "新密码不能为空", "status": 400}
        now = self.now()
        self.repo.update_password_hash(str(account["id"]), hash_password(new_password), now)
        self.repo.revoke_account_sessions(str(account["id"]), now)
        self.write_audit(
            "password_change",
            actor_id=str(account["id"]),
            actor_username=str(account.get("username") or ""),
            ip=ip,
            detail={},
        )
        return {"ok": True, "status": 200}

    def public_account(self, account: dict) -> dict:
        hydrated = self.hydrate_account(account) or {}
        return {
            "id": hydrated.get("id"),
            "username": hydrated.get("username"),
            "role_id": hydrated.get("role_id"),
            "role_name": hydrated.get("role_name"),
            "is_super": bool(hydrated.get("is_super")),
            "enabled": bool(hydrated.get("enabled")),
            "permissions": sorted(hydrated.get("permissions") or []),
        }

    def list_accounts_public(self) -> list[dict]:
        return [self.public_account(a) for a in self.repo.list_accounts()]

    def list_roles_public(self) -> list[dict]:
        out = []
        counts: dict[str, int] = {}
        for acc in self.repo.list_accounts():
            rid = str(acc.get("role_id") or "")
            counts[rid] = counts.get(rid, 0) + 1
        for role in self.repo.list_roles():
            perms = self.repo.get_role_perms(str(role["id"]))
            out.append({
                "account_count": counts.get(str(role["id"]), 0),
                "id": role["id"],
                "name": role.get("name"),
                "is_super": bool(role.get("is_super")),
                "is_preset": bool(role.get("is_preset")),
                "permissions": sorted(p for p in perms if p not in RETIRED_PERMS),
                "retired_permissions": sorted(p for p in perms if p in RETIRED_PERMS),
            })
        return out

    def count_enabled_super(self) -> int:
        n = 0
        for acc in self.repo.list_accounts():
            if not acc.get("enabled"):
                continue
            role = self.repo.get_role(str(acc.get("role_id") or ""))
            if role and role.get("is_super"):
                n += 1
        return n

    def create_user(self, username: str, password: str, role_id: str) -> dict:
        if not username.strip() or not password:
            raise ValueError("用户名和初始密码必填")
        if self.repo.get_account_by_username(username.strip()):
            raise ValueError("用户名已存在")
        if not self.repo.get_role(role_id):
            raise ValueError("角色不存在")
        row = self.create_account(username.strip(), password, role_id, enabled=True)
        return self.public_account(row)

    def _ensure_super_left(self, account_id: str, restore: dict) -> None:
        """写后复核：没有启用中的超管就回滚本次修改（防并发各自通过前置检查）。"""
        if self.count_enabled_super() >= 1:
            return
        self.repo.update_account_fields(account_id, dict(restore, updated_at=self.now()))
        raise PermissionError("不能去掉最后一名启用超管")

    def set_account_enabled(self, account_id: str, enabled: bool) -> dict:
        with _SUPER_GUARD:
            acc = self.hydrate_account(self.repo.get_account(account_id))
            if not acc:
                raise KeyError("账号不存在")
            if acc.get("is_super") and acc.get("enabled") and not enabled and self.count_enabled_super() <= 1:
                raise PermissionError("不能去掉最后一名启用超管")
            self.repo.update_account_fields(account_id, {"enabled": 1 if enabled else 0, "updated_at": self.now()})
            if acc.get("is_super") and not enabled:
                self._ensure_super_left(account_id, {"enabled": 1 if acc.get("enabled") else 0})
            if not enabled:
                self.repo.revoke_account_sessions(account_id, self.now())
            return self.public_account(self.repo.get_account(account_id) or acc)

    def set_account_role(self, account_id: str, role_id: str) -> dict:
        with _SUPER_GUARD:
            acc = self.hydrate_account(self.repo.get_account(account_id))
            if not acc:
                raise KeyError("账号不存在")
            role = self.repo.get_role(role_id)
            if not role:
                raise ValueError("角色不存在")
            if acc.get("is_super") and not role.get("is_super") and self.count_enabled_super() <= 1:
                raise PermissionError("不能去掉最后一名启用超管")
            self.repo.update_account_fields(account_id, {"role_id": role_id, "updated_at": self.now()})
            if acc.get("is_super") and not role.get("is_super"):
                self._ensure_super_left(account_id, {"role_id": acc.get("role_id")})
            return self.public_account(self.repo.get_account(account_id) or acc)

    def lock_status(self, username: str) -> dict:
        """登录锁定状态：只读登录失败锁，不涉及问答会话保存阻塞。"""
        name = (username or "").strip()
        row = self.repo.get_lock(name) or {}
        until = _dt(row.get("locked_until"))
        locked = until is not None and until > self.now()
        return {
            "username": name,
            "exists": self.repo.get_account_by_username(name) is not None,
            "locked": locked,
            "locked_until": str(until) if locked else None,
            "fail_count": int(row.get("fail_count") or 0),
        }

    def unlock_username(self, username: str) -> None:
        self._clear_fail((username or "").strip())

    def create_custom_role(self, name: str, perms: list[str]) -> dict:
        role_id = uid("role")
        clean = [p for p in perms if p in PERM_CHECKBOX]
        self.repo.upsert_role({
            "id": role_id,
            "name": name.strip() or "未命名角色",
            "is_super": 0,
            "is_preset": 0,
            "created_at": self.now(),
        })
        self.repo.set_role_perms(role_id, clean)
        return {"id": role_id, "name": name.strip(), "permissions": sorted(clean), "is_super": False}

    def set_custom_role_perms(self, role_id: str, perms: list[str]) -> dict:
        role = self.repo.get_role(role_id)
        if not role:
            raise KeyError("角色不存在")
        if role.get("is_super"):
            raise PermissionError("超管角色权限清单不可改")
        clean = [p for p in perms if p in PERM_CHECKBOX]
        self.repo.set_role_perms(role_id, clean)
        return {"id": role_id, "permissions": sorted(clean)}

    def list_audits(self) -> list[dict]:
        try:
            return self.repo.list_audits()
        except Exception as exc:  # noqa: BLE001
            log.warning("list audits failed: %s", exc)
            return []
