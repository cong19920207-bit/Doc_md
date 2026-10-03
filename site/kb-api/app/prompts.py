# -*- coding: utf-8 -*-
"""STEP-A10：只登记代码里已经有的职责槽位。未接入的槽位不能保存正文。"""
from __future__ import annotations

from . import settings

# 已接入：运行时有对应模板。Generate 的完整可部署文本尚未接入。
_SLOTS = (
    {"id": "router", "title": "Router", "connected": True, "text": lambda: settings.ROUTER_PROMPT,
     "need": ("route", "requires_history", "当前输入"), "forbid": ("tool_call", "function_call", "tools")},
    {"id": "task_prep", "title": "任务准备/追溯", "connected": True, "text": lambda: settings.TASK_PREP_PROMPT,
     "need": ("tasks", "excluded", "information_gaps", "response_constraint"), "forbid": ()},
    {"id": "rewriter", "title": "唯一 Rewriter", "connected": True, "text": lambda: settings.REWRITE_V3_PROMPT,
     "need": ("ready",), "forbid": ()},
    {"id": "check", "title": "Evidence check", "connected": True, "text": lambda: settings.CHECK_PROMPT,
     "need": ("pass",), "forbid": ()},
    {"id": "repair", "title": "单次修正", "connected": True, "text": lambda: settings.REPAIR_PROMPT,
     "need": ("修正",), "forbid": ()},
    {"id": "smalltalk", "title": "Smalltalk", "connected": True, "text": lambda: settings.SMALLTALK_PROMPT,
     "need": ("Hayyo",), "forbid": ()},
    {"id": "clarify", "title": "Clarification", "connected": True, "text": lambda: settings.CLARIFY_PROMPT,
     "need": ("澄清",), "forbid": ()},
    {"id": "restate", "title": "仅重述", "connected": True, "text": lambda: settings.RESTATE_PROMPT,
     "need": ("重述",), "forbid": ()},
    {"id": "recall", "title": "追溯动作", "connected": True, "text": lambda: settings.RECALL_PROMPT,
     "need": ("search",), "forbid": ()},
    {"id": "generate", "title": "Generate", "connected": False, "text": lambda: "",
     "need": (), "forbid": ()},
)


def slot_map() -> dict:
    return {row["id"]: row for row in _SLOTS}


def list_slots(saved: dict | None) -> list[dict]:
    """详情只返回登记槽位和已存草稿正文，不调用模型。"""
    saved = saved or {}
    out = []
    for row in _SLOTS:
        text = saved.get(row["id"])
        if text is None and row["connected"]:
            text = row["text"]()
        out.append({
            "id": row["id"],
            "title": row["title"],
            "connected": row["connected"],
            "status": "已接入" if row["connected"] else "未接入",
            "text": text if row["connected"] else "",
        })
    return out


def check_prompts(body: dict) -> str | None:
    """静态检查。通过不代表已经调用过模型。"""
    if not isinstance(body, dict):
        return "Prompt 格式不正确"
    known = slot_map()
    for slot, text in body.items():
        row = known.get(slot)
        if row is None:
            return f"未登记的槽位：{slot}"
        if not row["connected"]:
            return f"{row['title']}未接入，不能保存正文"
        raw = str(text or "")
        if not raw.strip():
            return f"{row['title']}正文为空"
        for word in row["forbid"]:
            if word in raw:
                return f"{row['title']}不能包含 {word}"
        missing = [w for w in row["need"] if w not in raw]
        if missing:
            return f"{row['title']}缺少必需内容：{'、'.join(missing)}"
    return None


def router_text(cfg: dict | None) -> str:
    return slot_text('router', cfg)


def slot_text(slot: str, cfg: dict | None) -> str:
    row = slot_map().get(slot)
    if not row or not row['connected']:
        raise ValueError('未接入的 Prompt 槽位：' + slot)
    saved = ((cfg or {}).get('prompts') or {}).get(slot)
    return str(saved or row['text']())
