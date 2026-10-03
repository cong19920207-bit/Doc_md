# -*- coding: utf-8 -*-
"""服务端组装 L1：按完整逻辑回合，最多 10 回合、最多 5000 tokens，整回合保留或淘汰。"""
from __future__ import annotations

import math
import re

MAX_TURNS = 10
MAX_HISTORY_TOKENS = 5000

_CJK_RE = re.compile(r"[\u3000-\u303f\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uac00-\ud7af\uff00-\uffef]")


def count_tokens(text: str) -> int:
    """字符估算：中日韩字符 1 字 = 1 token，其余约 4 字符 = 1 token。"""
    t = text or ""
    cjk = len(_CJK_RE.findall(t))
    other = len(t) - cjk
    return cjk + math.ceil(other / 4)


def _complete_rounds(messages: list[dict], exclude_round_id: str | None) -> tuple[list[dict], int]:
    """按 round_seq 分组；只有 User + 当前采用且完整的 Assistant 才算完整回合。"""
    groups: dict[str, dict] = {}
    order: list[str] = []
    for m in sorted(messages, key=lambda r: int(r["seq"])):
        rid = m["round_id"]
        if rid == exclude_round_id:
            continue
        if rid not in groups:
            groups[rid] = {"round_id": rid, "round_seq": int(m["round_seq"]), "user": None, "assistant": None}
            order.append(rid)
        g = groups[rid]
        if m["role"] == "user" and g["user"] is None:
            g["user"] = m
        elif m["role"] == "assistant" and int(m.get("is_current", 1) or 0):
            g["assistant"] = m
    complete, incomplete = [], 0
    for rid in sorted(order, key=lambda r: groups[r]["round_seq"]):
        g = groups[rid]
        a = g["assistant"]
        if g["user"] is None or a is None or (a.get("completeness") or "complete") != "complete":
            incomplete += 1
            continue
        # STEP-Q06：来源受限的迁移回合对不上执行记录，不能伪装成完整 L1 回合
        if "migrated_ltd" in (g["user"].get("source"), a.get("source")):
            incomplete += 1
            continue
        complete.append(g)
    return complete, incomplete


def assemble_l1(
    messages: list[dict],
    exclude_round_id: str | None = None,
    max_turns: int = MAX_TURNS,
    max_tokens: int = MAX_HISTORY_TOKENS,
) -> dict:
    """messages 必须已经过清空边界过滤（MsgStore.effective_messages）；当前回合通过 exclude_round_id 排除。"""
    complete, incomplete = _complete_rounds(messages, exclude_round_id)
    picked: list[dict] = []
    used = 0
    reason = None
    for g in reversed(complete):
        if len(picked) >= max_turns:
            reason = reason or "turn_limit"
            break
        cost = count_tokens(g["user"].get("content") or "") + count_tokens(g["assistant"].get("content") or "")
        if used + cost > max_tokens:
            # 超预算整轮不载入，不截半轮；更早的回合也不越过它补进来
            reason = "over_budget"
            break
        picked.append({
            "round_id": g["round_id"],
            "user_msg_id": g["user"]["id"],
            "assistant_msg_id": g["assistant"]["id"],
            "exec_id": g["assistant"].get("exec_id"),
            "created_at": str(g["user"].get("created_at") or ""),
            "user": g["user"].get("content") or "",
            "assistant": g["assistant"].get("content") or "",
            "tokens": cost,
        })
        used += cost
    picked.reverse()
    not_loaded = len(complete) - len(picked)
    if not complete:
        reason = "empty"
    return {
        "turns": picked,
        "tokens": used,
        "window": [t["round_id"] for t in picked],
        "reason": reason,
        "not_loaded": not_loaded,
        "incomplete": incomplete,
    }


def as_history(l1: dict) -> list[dict]:
    """转成旧 Pipeline.rewrite 认识的 {role, text} 列表，旧 → 新。"""
    out: list[dict] = []
    for t in l1["turns"]:
        out.append({"role": "user", "text": t["user"]})
        out.append({"role": "assistant", "text": t["assistant"]})
    return out


def snapshot_meta(l1: dict) -> dict:
    """写入 Runtime 的 L1 摘要：只记标识与用量，不存正文。
    STEP-Q08：l1_msg_ids 记当时实际采用的消息 id 对，刷新按它读回原文，不受之后版本切换影响。"""
    turns = l1["turns"]
    return {
        "l1_round_ids": list(l1["window"]),
        "l1_tokens": l1["tokens"],
        "l1_reason": l1["reason"],
        "l1_not_loaded": l1["not_loaded"],
        "l1_incomplete": l1["incomplete"],
        "l1_msg_ids": [[t["user_msg_id"], t["assistant_msg_id"]] for t in turns],
        "prev_exec_id": turns[-1].get("exec_id") if turns else None,
    }


def assemble_from_ids(rows: list[dict], pairs: list[list[str]]) -> dict:
    """STEP-Q08：按原快照的消息 id 对重建 L1；读不回的对计入 missing，不用其他消息补位。"""
    by_id = {r["id"]: r for r in rows}
    turns: list[dict] = []
    missing = 0
    used = 0
    for pair in pairs or []:
        if not isinstance(pair, (list, tuple)) or len(pair) != 2:
            missing += 1
            continue
        u, a = by_id.get(pair[0]), by_id.get(pair[1])
        if u is None or a is None:
            missing += 1
            continue
        cost = count_tokens(u.get("content") or "") + count_tokens(a.get("content") or "")
        turns.append({
            "round_id": u["round_id"],
            "user_msg_id": u["id"],
            "assistant_msg_id": a["id"],
            "exec_id": a.get("exec_id"),
            "created_at": str(u.get("created_at") or ""),
            "user": u.get("content") or "",
            "assistant": a.get("content") or "",
            "tokens": cost,
        })
        used += cost
    return {
        "turns": turns,
        "tokens": used,
        "window": [t["round_id"] for t in turns],
        "reason": "snapshot" if turns else "empty",
        "not_loaded": 0,
        "incomplete": 0,
        "missing": missing,
    }
