# -*- coding: utf-8 -*-
"""STEP-A07：把一次执行的 Runtime 收成七组只读字段。
缺记录标「旧版未记录」或「未知」，不补造步骤、耗时或推理；不把当次证据 hash 写成当前来源。"""
from __future__ import annotations

from datetime import datetime
from typing import Any

LEGACY = "旧版未记录"
UNKNOWN = "未知"

_STATUS_KEYS = (
    ("biz_result", "业务结果"),
    ("exec_state", "执行状态"),
    ("check_status", "检查"),
    ("text_integrity", "文本完整性"),
    ("msg_save", "消息保存"),
    ("runtime_save", "Runtime 保存"),
)


def _legacy(row: dict) -> bool:
    return not row.get("schema_ver")


def _show(row: dict, key: str, *, absent: str = UNKNOWN) -> str:
    """新执行缺值标未知；旧执行整列没记过的标旧版未记录。已有的旧字段照实显示。"""
    val = row.get(key)
    if val is None or val == "" or val == [] or val == {}:
        return LEGACY if _legacy(row) else absent
    if isinstance(val, bool):
        return "是" if val else "否"
    return str(val)


def _item(label: str, text: str) -> dict:
    return {"label": label, "text": text}


def referenced_msg_ids(row: dict) -> set[str]:
    """本执行快照里点到的消息 id。历史正文只允许这些 id，且还要对话审计。"""
    ids: set[str] = set()
    for key in ("user_msg_id", "assistant_msg_id"):
        if row.get(key):
            ids.add(str(row[key]))
    snap = row.get("snapshot") if isinstance(row.get("snapshot"), dict) else {}
    for pair in snap.get("l1_msg_ids") or []:
        if isinstance(pair, (list, tuple)):
            ids.update(str(x) for x in pair if x)
    for ref in row.get("history_refs") or []:
        if isinstance(ref, dict) and ref.get("message_id"):
            ids.add(str(ref["message_id"]))
    return ids


def _duration(row: dict) -> str:
    if _legacy(row) and not row.get("finished_at"):
        return LEGACY
    start, end = row.get("created_at"), row.get("finished_at")
    if not start or not end:
        return UNKNOWN
    try:
        a = datetime.fromisoformat(str(start).replace("Z", ""))
        b = datetime.fromisoformat(str(end).replace("Z", ""))
    except ValueError:
        return UNKNOWN
    return f"{max(0, int((b - a).total_seconds()))} 秒"


def _input_group(row: dict) -> list[dict]:
    snap = row.get("snapshot") if isinstance(row.get("snapshot"), dict) else {}
    not_loaded = snap.get("l1_not_loaded") or snap.get("l1_reason") or ""
    loaded = "未载入：" + str(not_loaded) if not_loaded else (
        LEGACY if _legacy(row) and not snap else ("已载入" if snap.get("l1_round_ids") else "本轮没有更早的完整回合")
    )
    if not_loaded and "没有历史" in loaded:
        loaded = "未载入：" + str(not_loaded).replace("没有历史", "未载入")
    ids = snap.get("l1_msg_ids") or []
    return [
        _item("当前原句", _show(row, "original_query", absent="（空）")),
        _item("逻辑回合", _show(row, "logical_round_id")),
        _item("L1", loaded),
        _item("L1 用量", str(snap.get("l1_tokens")) if snap.get("l1_tokens") is not None else (LEGACY if _legacy(row) else UNKNOWN)),
        _item("L1 消息", f"{len(ids)} 对标识，正文需对话审计" if ids else (LEGACY if _legacy(row) else "无")),
    ]


def _route_group(row: dict) -> list[dict]:
    router = row.get("router") if isinstance(row.get("router"), dict) else {}
    prep = row.get("task_prep") if isinstance(row.get("task_prep"), dict) else {}
    tasks = prep.get("tasks") or []
    lines = []
    for t in tasks:
        if not isinstance(t, dict):
            continue
        lines.append(f"{t.get('task_id') or ''} {t.get('mode') or ''} {t.get('check') or ''} {t.get('goal') or ''}".strip())
    reason = str(router.get("reason") or "")[:80]
    return [
        _item("原始 Route", _show(row, "route")),
        _item("需要历史", _show(row, "requires_history")),
        _item("置信度", str(router.get("confidence")) if router.get("confidence") is not None else (LEGACY if _legacy(row) else UNKNOWN)),
        _item("原因摘要", reason or (LEGACY if _legacy(row) else "（无）")),
        _item("任务", "\n".join(lines) if lines else (LEGACY if _legacy(row) else "（无）")),
    ]


def _recall_group(row: dict) -> list[dict]:
    recall = row.get("recall") if isinstance(row.get("recall"), dict) else None
    if recall is None:
        note = LEGACY if _legacy(row) else "本轮未调用记忆，这是正常路径，不要当成少了步骤"
        return [_item("记忆", note)]
    bits = []
    status = recall.get("gap_status") or {}
    for gid, st in status.items():
        bits.append(f"{gid}：{st}")
    items = recall.get("items") or []
    for it in items:
        if isinstance(it, dict) and it.get("gap_id"):
            bits.append(f"{it.get('gap_id')} 调用 {it.get('status')}")
    return [
        _item("逐缺口", "\n".join(bits) if bits else "（无缺口记录）"),
        _item("停止原因", str(recall.get("stop_reason") or UNKNOWN)),
        _item("覆盖", str((recall.get("coverage") or UNKNOWN))),
    ]


def _rewrite_group(row: dict) -> list[dict]:
    rewrite = row.get("rewrite") if isinstance(row.get("rewrite"), dict) else {}
    cgen = row.get("c_gen") if isinstance(row.get("c_gen"), list) else []
    lanes = row.get("lanes") if isinstance(row.get("lanes"), list) else []
    return [
        _item("改写状态", str(rewrite.get("status") or rewrite.get("valid") or (LEGACY if _legacy(row) else UNKNOWN))),
        _item("独立问句", _show(row, "rewrite_query", absent="（空）")),
        _item("命中候选", f"{len(lanes)} 路" if lanes else (LEGACY if _legacy(row) else "未另记候选，不把送入生成的材料当成候选")),
        _item("实际送入生成", f"{len(cgen)} 条" if cgen else (LEGACY if _legacy(row) else "（无）")),
    ]


def _check_group(row: dict) -> list[dict]:
    ev = row.get("evidence_check") if isinstance(row.get("evidence_check"), dict) else None
    if ev is None:
        return [_item("检查", LEGACY if _legacy(row) else _show(row, "check_status", absent="未跑"))]
    rounds = []
    for i, rd in enumerate(ev.get("rounds") or [], 1):
        if not isinstance(rd, dict):
            continue
        rounds.append(f"第 {i} 份草稿 {rd.get('check_status') or UNKNOWN}，问题 {len(rd.get('issues') or [])} 条")
    return [
        _item("检查记录", "\n".join(rounds) if rounds else UNKNOWN),
        _item("修正次数", str(ev.get("repair_count") if ev.get("repair_count") is not None else UNKNOWN)),
        _item("通过的含义", "pass 只表示该次检查没有未解决的问题，不等于已保存或任务都已回答"),
    ]


def _budget_group(row: dict) -> list[dict]:
    usage = row.get("call_usage") if isinstance(row.get("call_usage"), dict) else None
    if usage is None:
        text = LEGACY if _legacy(row) else UNKNOWN
    else:
        text = "、".join(f"{k} {v}" for k, v in usage.items())
    recall = row.get("recall") if isinstance(row.get("recall"), dict) else {}
    budget = recall.get("budget") if isinstance(recall.get("budget"), dict) else None
    return [
        _item("调用计数", text),
        _item("追溯预算", str(budget) if budget else (LEGACY if _legacy(row) else "本轮无追溯预算")),
        _item("耗时", _duration(row)),
    ]


def _delivery_group(row: dict) -> list[dict]:
    return [
        _item("业务结果", _show(row, "biz_result")),
        _item("执行状态", _show(row, "exec_state")),
        _item("检查", _show(row, "check_status")),
        _item("消息保存", _show(row, "msg_save")),
        _item("Runtime 保存", _show(row, "runtime_save")),
        _item("最终文本", _show(row, "answer", absent="（无）")),
        _item("当次证据", "见检查记录中的 hash。当前来源另列，本页不把当次 hash 当作当前来源，相同也不表示规则适用日期。"),
    ]


def build(row: dict) -> dict:
    """详情用的只读视图。不含模型推理，不含历史消息正文。"""
    groups = [
        ("input", "输入与上下文", _input_group(row)),
        ("route", "路由与任务", _route_group(row)),
        ("recall", "历史恢复", _recall_group(row)),
        ("rewrite", "改写与知识", _rewrite_group(row)),
        ("check", "生成、检查与修正", _check_group(row)),
        ("budget", "预算与异常", _budget_group(row)),
        ("delivery", "交付与保存", _delivery_group(row)),
    ]
    return {
        "legacy": _legacy(row),
        "statuses": [{"key": k, "label": label, "text": _show(row, k)} for k, label in _STATUS_KEYS],
        "groups": [{"id": i, "title": title, "items": items} for i, title, items in groups],
    }
