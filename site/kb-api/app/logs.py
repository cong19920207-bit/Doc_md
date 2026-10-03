# -*- coding: utf-8 -*-
"""轮次日志存法 B。写失败不阻断问答。"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

import pymysql

from . import settings
from .router import ROUTES
from .util import json_dumps, json_loads

log = logging.getLogger("kb-api.logs")

ALLOWED_STATUS = {
    "running", "success", "refuse", "rewrite_fail", "gen_fail", "empty", "interrupted",
}

# STEP-Q02：Runtime 多维状态。空值 = 未知，不得默认成功
RUNTIME_SCHEMA_VER = 2
STATUS_ENUMS: dict[str, set[str]] = {
    # STEP-Q18（G-E08 门）：增加证据冲突 conflict、缺少上下文 missing_context
    "biz_result": {
        "answered", "partial", "insufficient", "refused", "clarify", "not_applicable", "conflict", "missing_context",
    },
    "exec_state": {"running", "completed", "failed", "interrupted"},
    "check_status": {"pass", "fail", "error", "not_run"},
    "text_integrity": {"complete", "truncated", "empty"},
    "msg_save": {"saved", "failed", "pending", "not_applicable"},
    "runtime_save": {"saved", "partial", "failed"},
}
STATUS_KEYS = tuple(STATUS_ENUMS)
RUNTIME_TEXT_FIELDS = (
    "logical_round_id", "op_type", "user_msg_id", "assistant_msg_id", "error_type", "client_request_id",
)
# JSON 列：snapshot（Q05/Q08 快照）、pending_reply（Q09 补写承载）、router（Q11 分类记录）、task_prep（Q13 任务集）、
# rewrite（Q17 改写记录）、call_usage（Q17 本执行模型调用计数，后端维护、不归零）、evidence_check（Q19 检查与修正）、
# recall（Q16 追溯：逐缺口状态、来源标识、停止原因、预算用量；不存原文）、history_refs（Q20 回看/重述的历史引用）
RUNTIME_JSON_FIELDS = (
    "snapshot", "pending_reply", "router", "task_prep", "rewrite", "call_usage", "evidence_check", "recall",
    "history_refs", "answer_process",
)

# 已有数据卷补列；新库由 init.sql 建列
RUNTIME_COLUMNS = (
    ("schema_ver", "INT NULL"),
    ("logical_round_id", "VARCHAR(64) NULL"),
    ("op_type", "VARCHAR(16) NULL"),
    ("user_msg_id", "VARCHAR(64) NULL"),
    ("assistant_msg_id", "VARCHAR(64) NULL"),
    ("used_knowledge_rag", "TINYINT NULL"),
    ("snapshot", "JSON NULL"),
    ("error_type", "VARCHAR(32) NULL"),
    ("biz_result", "VARCHAR(24) NULL"),
    ("exec_state", "VARCHAR(16) NULL"),
    ("check_status", "VARCHAR(16) NULL"),
    ("text_integrity", "VARCHAR(16) NULL"),
    ("msg_save", "VARCHAR(16) NULL"),
    ("runtime_save", "VARCHAR(16) NULL"),
    ("client_request_id", "VARCHAR(64) NULL"),
    ("pending_reply", "JSON NULL"),
    ("route", "VARCHAR(24) NULL"),
    ("requires_history", "TINYINT NULL"),
    ("router", "JSON NULL"),
    ("finished_at", "DATETIME(3) NULL"),
    ("task_prep", "JSON NULL"),
    ("rewrite", "JSON NULL"),
    ("call_usage", "JSON NULL"),
    ("evidence_check", "JSON NULL"),
    ("recall", "JSON NULL"),
    ("history_refs", "JSON NULL"),
    ("answer_process", "JSON NULL"),
)
RUNTIME_INDEXES = (
    ("idx_qa_rounds_conv_req", "CREATE INDEX idx_qa_rounds_conv_req ON qa_rounds (conv_id, client_request_id)"),
)


def sanitize_runtime_fields(fields: dict[str, Any]) -> dict[str, Any]:
    """只保留合法的 Runtime 字段；枚举外的状态值丢弃，不写成成功。"""
    out: dict[str, Any] = {}
    for key, value in fields.items():
        if key in STATUS_ENUMS:
            if value is None or value in STATUS_ENUMS[key]:
                out[key] = value
        elif key in RUNTIME_TEXT_FIELDS:
            out[key] = None if value is None else str(value)[:64]
        elif key in ("used_knowledge_rag", "requires_history"):
            out[key] = None if value is None else (1 if value else 0)
        elif key == "route":
            # 只收六类 route；枚举外丢弃，不写成任何一类
            if value is None or value in ROUTES:
                out[key] = value
        elif key == "schema_ver":
            out[key] = None if value is None else int(value)
        elif key == "finished_at":
            # STEP-A15：执行终态时间，UTC 文本；补写与重试保存不带此键
            out[key] = None if value is None else str(value)[:23]
        elif key in RUNTIME_JSON_FIELDS:
            out[key] = None if value is None else json_dumps(value)
    return out


def runtime_statuses(row: dict) -> dict[str, Any]:
    """旧记录没有 schema_ver：六类状态一律返回 None（未知）。"""
    if not row.get("schema_ver"):
        return {k: None for k in STATUS_KEYS}
    return {k: row.get(k) for k in STATUS_KEYS}


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
        # 新列另起一句 UPDATE：老库尚未补列时不影响旧日志写入
        runtime = sanitize_runtime_fields({
            k: row[k] for k in (*STATUS_KEYS, *RUNTIME_TEXT_FIELDS, "schema_ver") if k in row
        })
        try:
            with self._conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(sql, args)
                    if runtime:
                        try:
                            sets = ", ".join(f"{k}=%s" for k in runtime)
                            cur.execute(
                                f"UPDATE qa_rounds SET {sets} WHERE round_id=%s",
                                (*runtime.values(), row["round_id"]),
                            )
                        except Exception as exc:  # noqa: BLE001
                            log.warning("insert runtime columns failed: %s", exc)
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
        legacy_sets, legacy_args = list(sets), list(args)
        # 最终状态与 runtime_save=saved 同句写入：这句失败时库里仍停在 partial
        runtime = sanitize_runtime_fields(fields)
        for key, value in runtime.items():
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
            if runtime and len(legacy_sets) > 1:
                # 新列不可写时保住旧字段，但仍返回失败，调用方按 Runtime 局部保存上报
                try:
                    with self._conn() as conn:
                        with conn.cursor() as cur:
                            cur.execute(
                                f"UPDATE qa_rounds SET {', '.join(legacy_sets)} WHERE round_id=%s",
                                (*legacy_args, round_id),
                            )
                except Exception:  # noqa: BLE001
                    pass
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
            # 同一启动点顺带补 Runtime 列；失败只记日志，不影响反馈列结果
            self.ensure_runtime_columns()
            return True
        except Exception as exc:  # noqa: BLE001
            log.warning("ensure feedback columns failed: %s", exc)
            self.last_error = str(exc)
            return False

    def ensure_runtime_columns(self) -> bool:
        """已有数据卷补 Runtime 多维状态列（STEP-Q02）。"""
        try:
            with self._conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS "
                        "WHERE TABLE_SCHEMA=%s AND TABLE_NAME='qa_rounds'",
                        (settings.MYSQL_DATABASE,),
                    )
                    have = {row["COLUMN_NAME"] for row in (cur.fetchall() or [])}
                    for name, ddl in RUNTIME_COLUMNS:
                        if name not in have:
                            cur.execute(f"ALTER TABLE qa_rounds ADD COLUMN {name} {ddl}")
                    cur.execute(
                        "SELECT DISTINCT INDEX_NAME FROM INFORMATION_SCHEMA.STATISTICS "
                        "WHERE TABLE_SCHEMA=%s AND TABLE_NAME='qa_rounds'",
                        (settings.MYSQL_DATABASE,),
                    )
                    idx = {row["INDEX_NAME"] for row in (cur.fetchall() or [])}
                    for name, ddl in RUNTIME_INDEXES:
                        if name not in idx:
                            cur.execute(ddl)
            return True
        except Exception as exc:  # noqa: BLE001
            # 不写 last_error：它被反馈接口用来区分「库故障」与「未找到」
            log.warning("ensure runtime columns failed: %s", exc)
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

    def find_by_request(self, conv_id: str, client_request_id: str) -> dict | None:
        """STEP-Q07：按会话 + 请求号找已被接受的执行（刷新幂等）。库异常抛出。"""
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM qa_rounds WHERE conv_id=%s AND client_request_id=%s "
                    "ORDER BY created_at ASC LIMIT 1",
                    (conv_id, client_request_id),
                )
                row = cur.fetchone()
        return self._decode(row) if row else None

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

    def page_rounds(
        self,
        *,
        q: str = "",
        status: str = "",
        feedback: str = "",
        pending: bool = False,
        before: tuple[str, str] | None = None,
        size: int = 50,
        op_type: str = "",
        route: str = "",
        biz_result: str = "",
        exec_state: str = "",
        check_status: str = "",
        msg_save: str = "",
        requires_history: str = "",
        used_knowledge_rag: str = "",
    ) -> tuple[list[dict], bool]:
        """G-ADM-E01：服务端筛选 + 游标分页（created_at 倒序、round_id 倒序）。查询失败直接抛出，不当成空结果。"""
        sql = "SELECT * FROM qa_rounds WHERE 1=1"
        args: list[Any] = []
        if status:
            sql += " AND status=%s"
            args.append(status)
        if feedback:
            sql += " AND feedback=%s"
            args.append(feedback)
        if pending:
            # 待处理：非成功的执行或被踩
            sql += " AND ((status IS NOT NULL AND status<>'success') OR feedback='down')"
        if q:
            sql += " AND original_query LIKE %s"
            args.append(f"%{q}%")
        for col, val in (
            ("op_type", op_type), ("route", route), ("biz_result", biz_result),
            ("exec_state", exec_state), ("check_status", check_status), ("msg_save", msg_save),
        ):
            if val:
                sql += f" AND {col}=%s"
                args.append(val)
        for col, val in (("requires_history", requires_history), ("used_knowledge_rag", used_knowledge_rag)):
            if val in ("0", "1"):
                sql += f" AND {col}=%s"
                args.append(int(val))
        if before:
            sql += " AND (created_at < %s OR (created_at = %s AND round_id < %s))"
            args.extend([before[0], before[0], before[1]])
        sql += " ORDER BY created_at DESC, round_id DESC LIMIT %s"
        args.append(int(size) + 1)
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, args)
                rows = cur.fetchall() or []
        items = [self._decode(r) for r in rows]
        return items[:size], len(items) > size

    def delete_conv(self, conv_id: str) -> None:
        """实际删除时清掉该会话的执行记录。"""
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM qa_rounds WHERE conv_id=%s", (conv_id,))

    def page_feedback(
        self,
        *,
        value: str = "down",
        time_col: str = "feedback_at",
        rng: dict | None = None,
        user_id: str = "",
        conv_id: str = "",
        exec_id: str = "",
        msg_id: str = "",
        route: str = "",
        handled: str = '',
        before: tuple[str, str] | None = None,
        size: int = 50,
    ) -> tuple[list[dict], bool]:
        """STEP-A16：已发生的反馈事件（feedback 非空），服务端筛选 + 游标分页。查询失败直接抛出。"""
        col = "created_at" if time_col == "created_at" else "feedback_at"
        sql = "SELECT * FROM qa_rounds WHERE feedback IS NOT NULL"
        args: list[Any] = []
        if handled:
            exists = "SELECT 1 FROM kb_issues i WHERE i.source_type='feedback' AND i.source_id=qa_rounds.round_id"
            if handled == 'no':
                sql += ' AND NOT EXISTS (' + exists + ')'
            else:
                if handled in ('open', 'doing', 'closed'):
                    exists += ' AND i.status=%s'
                    args.append(handled)
                sql += ' AND EXISTS (' + exists + ')'
        if value in ("up", "down"):
            sql += " AND feedback=%s"
            args.append(value)
        for column, v in (("user_id", user_id), ("conv_id", conv_id), ("round_id", exec_id),
                          ("assistant_msg_id", msg_id), ("route", route)):
            if v:
                sql += f" AND {column}=%s"
                args.append(v)
        if rng:
            sql += f" AND {col}>=%s AND {col}<%s"
            args.extend([rng["start"], rng["end"]])
        if before:
            sql += f" AND ({col} < %s OR ({col} = %s AND round_id < %s))"
            args.extend([before[0], before[0], before[1]])
        sql += f" ORDER BY {col} DESC, round_id DESC LIMIT %s"
        args.append(int(size) + 1)
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, args)
                rows = cur.fetchall() or []
        items = [self._decode(r) for r in rows]
        return items[:size], len(items) > size

    def overview_counts(self, start: Any, end: Any) -> dict:
        """STEP-A15：按执行开始时间 [start, end) 用 SQL 聚合概览计数。查询失败直接抛出。
        已接受执行 = 有 schema_ver 且有逻辑回合（被拒请求没有逻辑回合）。"""
        base = "FROM qa_rounds WHERE created_at>=%s AND created_at<%s"
        acc = "(schema_ver IS NOT NULL AND logical_round_id IS NOT NULL)"
        term = "exec_state IN ('completed','failed','interrupted')"
        queue = f"{acc} AND msg_save='saved' AND assistant_msg_id IS NOT NULL AND status IN ('success','refuse','empty')"
        scalars = (
            ("total", "COUNT(*)"),
            ("legacy_rows", "SUM(schema_ver IS NULL)"),
            ("rejected", "SUM(schema_ver IS NOT NULL AND logical_round_id IS NULL)"),
            ("execs", f"SUM({acc})"),
            ("refresh", f"SUM({acc} AND op_type='refresh')"),
            ("op_unknown", f"SUM({acc} AND op_type IS NULL)"),
            ("new_rounds", f"COUNT(DISTINCT CASE WHEN {acc} AND op_type='send' THEN logical_round_id END)"),
            ("active_accounts", f"COUNT(DISTINCT CASE WHEN {acc} AND op_type='send' THEN user_id END)"),
            ("kn_yes", f"SUM({acc} AND used_knowledge_rag=1)"),
            ("kn_no", f"SUM({acc} AND used_knowledge_rag=0)"),
            ("kn_unknown", f"SUM({acc} AND used_knowledge_rag IS NULL)"),
            ("ms_saved", f"SUM({acc} AND msg_save='saved')"),
            ("ms_failed_final", f"SUM({acc} AND msg_save='failed' AND pending_reply IS NULL)"),
            ("ms_failed_pending", f"SUM({acc} AND msg_save='failed' AND pending_reply IS NOT NULL)"),
            ("ms_pending", f"SUM({acc} AND msg_save='pending')"),
            ("ms_na", f"SUM({acc} AND msg_save='not_applicable')"),
            ("ms_unknown", f"SUM({acc} AND msg_save IS NULL)"),
            ("rt_partial", f"SUM({acc} AND runtime_save='partial')"),
            ("dur_unknown", f"SUM({acc} AND {term} AND finished_at IS NULL)"),
            ("fb_queue", f"SUM({queue})"),
            ("fb_up", f"SUM({queue} AND feedback='up')"),
            ("fb_down", f"SUM({queue} AND feedback='down')"),
        )
        args = (start, end)
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT " + ", ".join(f"{expr} AS {name}" for name, expr in scalars) + f" {base}", args)
                row = cur.fetchone() or {}
                out: dict[str, Any] = {name: int(row.get(name) or 0) for name, _ in scalars}
                for key, col, extra in (("route", "route", ""), ("exec_state", "exec_state", ""),
                                        ("biz", "biz_result", f" AND {term}"), ('checks', 'check_status', '')):
                    cur.execute(f"SELECT {col} AS k, COUNT(*) AS n {base} AND {acc}{extra} GROUP BY {col}", args)
                    out[key] = {r["k"]: int(r["n"]) for r in (cur.fetchall() or [])}
                usage_keys = ('router', 'task_prep', 'rewrite', 'smalltalk', 'clarify', 'generate', 'check', 'repair', 'recall', 'memory', 'restate')
                cur.execute('SELECT ' + ', '.join("SUM(CAST(JSON_UNQUOTE(JSON_EXTRACT(call_usage, '$." + key + "')) AS UNSIGNED)) AS `" + key + '`' for key in usage_keys)
                            + f' {base} AND {acc}', args)
                usage = cur.fetchone() or {}
                out['calls'] = {key: int(usage[key]) if usage.get(key) is not None else None for key in usage_keys}
                cur.execute(
                    f"SELECT TIMESTAMPDIFF(MICROSECOND, created_at, finished_at) AS us {base} "
                    f"AND {acc} AND {term} AND finished_at IS NOT NULL",
                    args,
                )
                out["durations_ms"] = [int(r["us"]) / 1000.0 for r in (cur.fetchall() or []) if r["us"] is not None]
        return out

    def heat_rows(self, start: Any, end: Any, limit: int) -> list[dict]:
        """STEP-A15：新热度扫描窗口，按执行开始时间倒序最多 limit+1 行；c_gen 保留原始空值以区分未采集。"""
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT round_id, schema_ver, used_knowledge_rag, c_gen, created_at FROM qa_rounds "
                    "WHERE created_at>=%s AND created_at<%s ORDER BY created_at DESC, round_id DESC LIMIT %s",
                    (start, end, int(limit) + 1),
                )
                rows = cur.fetchall() or []
        out = []
        for r in rows:
            raw = r.get("c_gen")
            out.append({
                "round_id": r["round_id"],
                "schema_ver": r.get("schema_ver"),
                "used_knowledge_rag": r.get("used_knowledge_rag"),
                "c_gen": None if raw is None else json_loads(raw, []),
                "created_at": r.get("created_at"),
            })
        return out

    def heatmap(self) -> dict:
        return self.aggregate_heat(self.list_rounds(limit=5000))

    @staticmethod
    def aggregate_heat(rows: list[dict]) -> dict:
        """STEP-Q21：新记录只统计实际调用 Knowledge RAG 的执行；旧记录无调用标记，按旧口径计入并单列。"""
        counts: dict[str, int] = {}
        legacy: dict[str, int] = {}
        unclassified = 0
        unclassified_legacy = 0
        legacy_rows = 0
        for row in rows:
            is_legacy = not row.get("schema_ver")
            if is_legacy:
                legacy_rows += 1
            elif not row.get("used_knowledge_rag"):
                continue
            feats = LogStore._hit_features(row)
            if not feats:
                unclassified += 1
                if is_legacy:
                    unclassified_legacy += 1
                continue
            for fid in feats:
                counts[fid] = counts.get(fid, 0) + 1
                if is_legacy:
                    legacy[fid] = legacy.get(fid, 0) + 1
        ranked = sorted(
            [{"feature_id": k, "count": v, "legacy_count": legacy.get(k, 0)} for k, v in counts.items()],
            key=lambda x: (-x["count"], x["feature_id"]),
        )
        return {
            "items": ranked,
            "unclassified": unclassified,
            "unclassified_legacy": unclassified_legacy,
            "legacy_rows": legacy_rows,
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
        if item.get("requires_history") is not None:
            item["requires_history"] = bool(item["requires_history"])
        for key in RUNTIME_JSON_FIELDS:
            if key in item:
                item[key] = json_loads(item.get(key), None)
        item["statuses"] = runtime_statuses(item)
        for ts in ("created_at", "updated_at", "feedback_at"):
            if item.get(ts) is not None:
                item[ts] = str(item[ts])
        return item
