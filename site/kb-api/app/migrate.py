# -*- coding: utf-8 -*-
"""STEP-Q06：旧云端历史迁移（G-E04-5）。
旧 kb_conversations.payload.messages 与 qa_rounds 是不同记录：能按执行 id + 原句对上的才按执行记录时间迁为完整回合；
对不上的也迁入，但标「来源受限」，不进 L1、不参与精确时间查找。不补造清空边界、原话、时间与版本。"""
from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from . import settings
from .util import json_loads, uid

log = logging.getLogger("kb-api.migrate")

MIGRATED = "migrated"
# 来源受限：对不上执行记录或缺少配对，created_at 只是占位（会话创建时间），不是可靠的消息时间
MIGRATED_LIMITED = "migrated_ltd"
REPORT_NAME = "q06-report.json"


def _as_dt(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("T", " ").replace("Z", ""))
    except ValueError:
        return None


def _norm(text: Any) -> str:
    return " ".join(str(text or "").split())


def pair_messages(messages: list[dict]) -> tuple[list[dict], list[dict]]:
    """按旧前端顺序配对：每条 User 与紧随其后的第一条 Assistant/System 组成一个回合。
    没有 User 可挂的回答不补造回合，列入丢弃清单。"""
    rounds: list[dict] = []
    dropped: list[dict] = []
    current: dict | None = None
    for i, m in enumerate(messages or []):
        if not isinstance(m, dict) or m.get("pending"):
            continue
        role = m.get("role")
        if role == "user":
            if current is not None:
                rounds.append(current)
            current = {"user": m, "answer": None, "index": i}
        elif role in ("assistant", "system"):
            if current is not None and current["answer"] is None:
                current["answer"] = m
                rounds.append(current)
                current = None
            else:
                dropped.append({"index": i, "reason": "no_user", "round_id": m.get("round_id")})
    if current is not None:
        rounds.append(current)
    return rounds, dropped


def _match(logs: Any, conv_id: str, user: dict, answer: dict | None) -> dict | None:
    """回答的执行 id 在同会话执行记录里存在且原句一致才算可靠对应。"""
    if not answer or not answer.get("round_id"):
        return None
    try:
        rt = logs.get_round(str(answer["round_id"]))
    except Exception:  # noqa: BLE001
        return None
    if not rt or str(rt.get("conv_id") or "") != conv_id:
        return None
    if _norm(rt.get("original_query")) != _norm(user.get("text") or user.get("query")):
        return None
    if _as_dt(rt.get("created_at")) is None:
        return None
    return rt


def build_rows(conv: dict, messages: list[dict], logs: Any, next_seq) -> tuple[list[dict], dict]:
    """生成待写入的消息行与本会话报告；seq 按旧顺序服务端取号。"""
    conv_id = str(conv["id"])
    rounds, dropped = pair_messages(messages)
    placeholder = _as_dt(conv.get("created_at")) or datetime.utcnow()
    rows: list[dict] = []
    report = {"conv_id": conv_id, "hidden": bool(conv.get("hidden_at")), "rounds": 0, "reliable": 0,
              "limited": [], "dropped": dropped}
    for r in rounds:
        user, answer = r["user"], r["answer"]
        rt = _match(logs, conv_id, user, answer)
        source = MIGRATED if rt else MIGRATED_LIMITED
        if rt:
            u_at = _as_dt(rt.get("created_at"))
            a_at = _as_dt(rt.get("finished_at")) or _as_dt(rt.get("updated_at")) or u_at
        else:
            u_at = a_at = placeholder
        round_id = uid("lr")
        u_seq = next_seq(conv_id)
        rows.append({
            "id": uid("m"), "conv_id": conv_id, "seq": u_seq, "round_id": round_id, "round_seq": u_seq,
            "exec_id": str(answer["round_id"]) if rt else None, "role": "user",
            "content": str(user.get("text") or user.get("query") or ""), "op_type": "send",
            "version_no": None, "is_current": 1, "completeness": "complete", "client_request_id": None,
            "source": source, "created_at": u_at,
        })
        if answer is not None:
            text = str(answer.get("text") or "")
            if answer.get("role") == "system":
                completeness = "error_notice"
            else:
                completeness = "complete" if text.strip() else "partial"
            rows.append({
                "id": uid("m"), "conv_id": conv_id, "seq": next_seq(conv_id), "round_id": round_id,
                "round_seq": u_seq, "exec_id": str(answer["round_id"]) if rt else None, "role": "assistant",
                "content": text, "op_type": "send", "version_no": 1, "is_current": 1,
                "completeness": completeness, "client_request_id": None, "source": source, "created_at": a_at,
            })
        report["rounds"] += 1
        if rt:
            report["reliable"] += 1
        else:
            reason = "no_answer" if answer is None else ("no_round_id" if not answer.get("round_id") else "unmatched")
            report["limited"].append({"index": r["index"], "reason": reason})
    return rows, report


def migrate_legacy(convs: Any, msgs: Any, logs: Any, report_dir: Path | None = None) -> dict:
    """服务启动时执行；消息表里已有任何记录的会话一律跳过，可重复执行、不重复写入。
    单个会话失败只记报告，不影响其他会话，也不阻断启动。"""
    summary = {"at": datetime.utcnow().isoformat(timespec="seconds"), "scanned": 0, "migrated": 0,
               "skipped_has_messages": 0, "skipped_empty": 0, "failed": 0, "items": []}
    try:
        rows_all = convs.repo.list_all()
    except Exception as exc:  # noqa: BLE001
        log.warning("q06 list conversations failed: %s", exc)
        summary["error"] = "list_failed"
        return summary
    for conv in rows_all:
        summary["scanned"] += 1
        conv_id = str(conv.get("id") or "")
        payload = json_loads(conv.get("payload"), {}) or {}
        messages = payload.get("messages") or []
        try:
            if msgs.has_messages(conv_id):
                summary["skipped_has_messages"] += 1
                if messages:
                    # 已有新消息的会话，其旧缓存不再迁入，避免与服务端事实交错
                    summary["items"].append({"conv_id": conv_id, "status": "skipped_has_messages"})
                continue
            if not messages:
                summary["skipped_empty"] += 1
                continue
            rows, report = build_rows(conv, messages, logs, msgs.next_seq)
            if not rows:
                summary["skipped_empty"] += 1
                summary["items"].append(dict(report, status="nothing_to_migrate"))
                continue
            msgs.insert_migrated(rows)
            summary["migrated"] += 1
            summary["items"].append(dict(report, status="migrated"))
        except Exception as exc:  # noqa: BLE001
            log.warning("q06 migrate %s failed: %s", conv_id, exc)
            summary["failed"] += 1
            summary["items"].append({"conv_id": conv_id, "status": "failed", "error": type(exc).__name__})
    _write_report(summary, report_dir)
    return summary


def _write_report(summary: dict, report_dir: Path | None) -> None:
    """报告只含 id、计数与原因，不含原文。写失败只记日志。"""
    try:
        base = Path(report_dir or settings.DATA_DIR / "migrate")
        base.mkdir(parents=True, exist_ok=True)
        (base / REPORT_NAME).write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    except Exception as exc:  # noqa: BLE001
        log.warning("q06 report write failed: %s", exc)
