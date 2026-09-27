# -*- coding: utf-8 -*-
"""轮次日志存法 B。写失败不阻断问答。"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

import pymysql

from . import settings
from .util import json_dumps, json_loads

log = logging.getLogger("kb-api.logs")

ALLOWED_STATUS = {
    "running", "success", "refuse", "rewrite_fail", "gen_fail", "empty", "interrupted",
}


class LogStore:
    def __init__(self) -> None:
        self.last_error: str | None = None

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

    def ping(self) -> bool:
        try:
            with self._conn() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                    cur.fetchone()
            self.last_error = None
            return True
        except Exception as exc:  # noqa: BLE001
            self.last_error = str(exc)
            return False

    def insert_running(self, row: dict) -> bool:
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        sql = (
            "INSERT INTO qa_rounds (round_id, conv_id, created_at, updated_at, original_query,"
            " rewrite_query, same_topic, named_feature_ids, lanes, c_gen, answer, status, models,"
            " user_id, owner_id, tenant_id, role) VALUES ("
            "%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        )
        args = (
            row["round_id"],
            row["conv_id"],
            now,
            now,
            row.get("original_query") or "",
            None,
            None,
            None,
            None,
            None,
            None,
            "running",
            json_dumps(row.get("models") or {}),
            row.get("user_id"),
            row.get("owner_id"),
            row.get("tenant_id"),
            row.get("role"),
        )
        try:
            with self._conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(sql, args)
            return True
        except Exception as exc:  # noqa: BLE001
            log.warning("insert running failed: %s", exc)
            self.last_error = str(exc)
            return False

    def update_round(self, round_id: str, fields: dict[str, Any]) -> bool:
        if not fields:
            return True
        allowed = {
            "rewrite_query", "same_topic", "named_feature_ids", "lanes", "c_gen",
            "answer", "status", "models",
        }
        sets = ["updated_at=%s"]
        args: list[Any] = [datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]]
        for key, value in fields.items():
            if key not in allowed:
                continue
            if key == "status" and value not in ALLOWED_STATUS:
                continue
            if key in {"named_feature_ids", "lanes", "c_gen", "models"}:
                value = json_dumps(value)
            sets.append(f"{key}=%s")
            args.append(value)
        args.append(round_id)
        sql = f"UPDATE qa_rounds SET {', '.join(sets)} WHERE round_id=%s"
        try:
            with self._conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(sql, args)
            return True
        except Exception as exc:  # noqa: BLE001
            log.warning("update round failed: %s", exc)
            self.last_error = str(exc)
            return False

    def ensure_feedback_columns(self) -> bool:
        """已有数据卷补 feedback / feedback_at；新库由 init.sql 建列。"""
        try:
            with self._conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS "
                        "WHERE TABLE_SCHEMA=%s AND TABLE_NAME='qa_rounds' "
                        "AND COLUMN_NAME IN ('feedback', 'feedback_at')",
                        (settings.MYSQL_DATABASE,),
                    )
                    have = {row["COLUMN_NAME"] for row in (cur.fetchall() or [])}
                    if "feedback" not in have:
                        cur.execute(
                            "ALTER TABLE qa_rounds ADD COLUMN feedback VARCHAR(16) NULL"
                        )
                    if "feedback_at" not in have:
                        cur.execute(
                            "ALTER TABLE qa_rounds ADD COLUMN feedback_at DATETIME(3) NULL"
                        )
            self.last_error = None
            return True
        except Exception as exc:  # noqa: BLE001
            log.warning("ensure feedback columns failed: %s", exc)
            self.last_error = str(exc)
            return False

    def set_feedback(self, round_id: str, feedback: str | None) -> str:
        """更新一轮反馈。返回 ok / not_found / invalid / error。"""
        if feedback not in (None, "up", "down"):
            return "invalid"
        row = self.get_round(round_id)
        if not row:
            return "error" if self.last_error else "not_found"
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        sql = (
            "UPDATE qa_rounds SET feedback=%s, feedback_at=%s, updated_at=%s "
            "WHERE round_id=%s"
        )
        try:
            with self._conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(sql, (feedback, now, now, round_id))
            return "ok"
        except Exception as exc:  # noqa: BLE001
            log.warning("set feedback failed: %s", exc)
            self.last_error = str(exc)
            return "error"

    def get_round(self, round_id: str) -> dict | None:
        try:
            with self._conn() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT * FROM qa_rounds WHERE round_id=%s", (round_id,))
                    row = cur.fetchone()
            return self._decode(row) if row else None
        except Exception as exc:  # noqa: BLE001
            self.last_error = str(exc)
            return None

    def list_rounds(
        self,
        q: str = "",
        feature_id: str = "",
        status: str = "",
        limit: int = 100,
    ) -> list[dict]:
        sql = "SELECT * FROM qa_rounds WHERE 1=1"
        args: list[Any] = []
        if status:
            sql += " AND status=%s"
            args.append(status)
        if q:
            sql += " AND original_query LIKE %s"
            args.append(f"%{q}%")
        sql += " ORDER BY created_at DESC LIMIT %s"
        args.append(int(limit))
        try:
            with self._conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(sql, args)
                    rows = cur.fetchall() or []
        except Exception as exc:  # noqa: BLE001
            self.last_error = str(exc)
            return []
        items = [self._decode(r) for r in rows]
        if feature_id == "未归类":
            return [r for r in items if not self._hit_features(r)]
        if feature_id:
            return [r for r in items if feature_id in self._hit_features(r)]
        return items

    def heatmap(self) -> dict:
        rows = self.list_rounds(limit=5000)
        counts: dict[str, int] = {}
        unclassified = 0
        for row in rows:
            feats = self._hit_features(row)
            if not feats:
                unclassified += 1
                continue
            for fid in feats:
                counts[fid] = counts.get(fid, 0) + 1
        ranked = sorted(
            [{"feature_id": k, "count": v} for k, v in counts.items()],
            key=lambda x: (-x["count"], x["feature_id"]),
        )
        return {
            "items": ranked,
            "unclassified": unclassified,
        }

    @staticmethod
    def _hit_features(row: dict) -> list[str]:
        c_gen = row.get("c_gen") or []
        seen: set[str] = set()
        out: list[str] = []
        for block in c_gen:
            fid = (block or {}).get("feature_id")
            if fid and fid not in seen:
                seen.add(fid)
                out.append(fid)
        return out

    @staticmethod
    def _decode(row: dict) -> dict:
        item = dict(row)
        for key in ("named_feature_ids", "lanes", "c_gen", "models"):
            item[key] = json_loads(item.get(key), [] if key != "models" else {})
        if item.get("same_topic") is not None:
            item["same_topic"] = bool(item["same_topic"])
        for ts in ("created_at", "updated_at", "feedback_at"):
            if item.get(ts) is not None:
                item[ts] = str(item[ts])
        return item
