# -*- coding: utf-8 -*-
"""STEP-Q13：最小任务准备、逐任务检查、部分交付、混合越界与跨轮承接。
只整理本轮要做什么；不检索、不改写知识 Query、不回答业务。结构见 G-E01（任务/缺口部分）。"""
from __future__ import annotations

import json
import re
from typing import Any, Callable

from . import settings
from .prompts import slot_text
from .models_ext import ModelError
from .router import format_l1

TASK_PREP_VER = "task-prep-v1"
TASK_MODES = ("查询", "解释", "对照", "整理", "核验", "回看", "重述")
# S01 §8.2 八类检查结果；后两类由执行阶段写入，任务准备只能给前六类
TASK_CHECKS = (
    "ready", "needs_history", "needs_user_input", "ambiguous",
    "blocked_by_dependency", "out_of_scope", "knowledge_insufficient", "error",
)
PREP_CHECKS = TASK_CHECKS[:6]
GAP_TYPES = ("history_object", "user_condition", "candidate_choice")
GAP_STATUS = ("open", "resolved", "unresolvable")
PREP_FIELDS = ("tasks", "excluded", "information_gaps", "response_constraint")
MAX_TASKS = 6
MAX_TEXT = 500
# 只承接这两类结果的上一轮（G-E01 ⑤）
CARRY_RESULTS = ("clarify", "partial")

TASK_PREP_FAIL_MESSAGE = "任务整理失败，本轮未检索、未生成。可重试。"
# G-E01 ④：Memory 查找在 M6 接入，此前如实说明
HISTORY_UNSUPPORTED = "需要更早的对话内容，当前暂不支持查找"
OUT_OF_SCOPE_REASON = "超出当前支持范围，未执行"

_JSON_RE = re.compile(r"\{.*\}", re.S)
_TASK_ID_RE = re.compile(r"^T\d{1,3}$")
_GAP_ID_RE = re.compile(r"^G\d{1,3}$")


class TaskPrepError(Exception):
    """任务准备执行异常：task_prep_invalid / task_prep_fail / missing_key。不降级为单任务。"""

    def __init__(self, code: str, detail: str, raw: str = "", message: str = "") -> None:
        super().__init__(detail)
        self.code = code
        self.detail = detail
        self.raw = raw or ""
        self.message = message or TASK_PREP_FAIL_MESSAGE


def _invalid(detail: str, raw: str) -> TaskPrepError:
    return TaskPrepError("task_prep_invalid", detail, raw)


def _text(value: Any, field: str, raw: str, allow_empty: bool = False) -> str:
    if not isinstance(value, str):
        raise _invalid(field, raw)
    value = value.strip()
    if not value and not allow_empty:
        raise _invalid(field, raw)
    return value[:MAX_TEXT]


def _str_list(value: Any, field: str, raw: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(x, str) for x in value):
        raise _invalid(field, raw)
    return [x.strip()[:MAX_TEXT] for x in value if x.strip()]


def _has_cycle(deps: dict[str, list[str]]) -> bool:
    state: dict[str, int] = {}

    def visit(node: str) -> bool:
        if state.get(node) == 1:
            return True
        if state.get(node) == 2:
            return False
        state[node] = 1
        if any(visit(d) for d in deps.get(node, [])):
            return True
        state[node] = 2
        return False

    return any(visit(n) for n in deps)


def parse_task_prep(raw: str) -> dict:
    """按 G-E01 任务/缺口结构校验；必需字段缺失或任一处非法即 task_prep_invalid，不猜。
    只有可为空的列表/文本（scope、constraints、depends_on、gap_ids、candidates、clue）缺省按空。"""
    text = (raw or "").strip()
    if not text:
        raise TaskPrepError("task_prep_fail", "empty_response", raw or "")
    try:
        obj: Any = json.loads(text)
    except json.JSONDecodeError:
        m = _JSON_RE.search(text)
        try:
            obj = json.loads(m.group(0)) if m else None
        except json.JSONDecodeError:
            obj = None
        if obj is None:
            raise _invalid("not_json", text)
    if not isinstance(obj, dict):
        raise _invalid("not_object", text)
    for key in PREP_FIELDS:
        if key not in obj:
            raise _invalid(f"missing:{key}", text)
    raw_tasks, raw_excluded, raw_gaps = obj["tasks"], obj["excluded"], obj["information_gaps"]
    if not isinstance(raw_tasks, list) or not isinstance(raw_excluded, list) or not isinstance(raw_gaps, list):
        raise _invalid("lists", text)
    if len(raw_tasks) > MAX_TASKS:
        raise _invalid("too_many_tasks", text)
    if not raw_tasks and not raw_excluded:
        raise _invalid("no_task", text)

    tasks: list[dict] = []
    for t in raw_tasks:
        if not isinstance(t, dict):
            raise _invalid("task", text)
        tid = t.get("task_id")
        if not isinstance(tid, str) or not _TASK_ID_RE.match(tid) or any(x["task_id"] == tid for x in tasks):
            raise _invalid("task_id", text)
        mode = t.get("mode")
        if mode not in TASK_MODES:
            raise _invalid("mode", text)
        check = t.get("check")
        if check not in PREP_CHECKS:
            raise _invalid("check", text)
        tasks.append({
            "task_id": tid,
            "goal": _text(t.get("goal"), "goal", text),
            "mode": mode,
            "scope": _text(t.get("scope", ""), "scope", text, allow_empty=True),
            "constraints": _str_list(t.get("constraints", []), "constraints", text),
            "depends_on": _str_list(t.get("depends_on", []), "depends_on", text),
            "check": check,
            "gap_ids": _str_list(t.get("gap_ids", []), "gap_ids", text),
        })

    gaps: list[dict] = []
    task_ids = {t["task_id"] for t in tasks}
    for g in raw_gaps:
        if not isinstance(g, dict):
            raise _invalid("gap", text)
        gid = g.get("gap_id")
        if not isinstance(gid, str) or not _GAP_ID_RE.match(gid) or any(x["gap_id"] == gid for x in gaps):
            raise _invalid("gap_id", text)
        if g.get("type") not in GAP_TYPES:
            raise _invalid("gap_type", text)
        if g.get("status") not in GAP_STATUS:
            raise _invalid("gap_status", text)
        if not isinstance(g.get("required"), bool):
            raise _invalid("gap_required", text)
        linked = _str_list(g.get("task_ids", []), "gap_task_ids", text)
        if any(x not in task_ids for x in linked):
            raise _invalid("gap_task_ids", text)
        gaps.append({
            "gap_id": gid,
            "task_ids": linked,
            "type": g["type"],
            "required": g["required"],
            "status": g["status"],
            "candidates": _str_list(g.get("candidates", []), "candidates", text),
            "clue": _text(g.get("clue", ""), "clue", text, allow_empty=True),
        })

    gap_ids = {g["gap_id"] for g in gaps}
    for t in tasks:
        if any(d not in task_ids or d == t["task_id"] for d in t["depends_on"]):
            raise _invalid("depends_on", text)
        if any(x not in gap_ids for x in t["gap_ids"]):
            raise _invalid("gap_ids", text)
    if _has_cycle({t["task_id"]: t["depends_on"] for t in tasks}):
        raise _invalid("depends_cycle", text)

    excluded: list[dict] = []
    for e in raw_excluded:
        if not isinstance(e, dict):
            raise _invalid("excluded", text)
        excluded.append({
            "text": _text(e.get("text"), "excluded_text", text),
            "reason": _text(e.get("reason"), "excluded_reason", text),
        })

    return {
        "tasks": tasks,
        "excluded": excluded,
        "information_gaps": gaps,
        "response_constraint": _text(obj["response_constraint"], "response_constraint", text, allow_empty=True),
        # 多余字段不使用，只记字段名
        "extra_keys": sorted(str(k) for k in obj if k not in PREP_FIELDS),
    }


def _gap_note(task: dict, gaps: dict[str, dict]) -> str:
    clues = [gaps[g]["clue"] for g in task["gap_ids"] if gaps.get(g) and gaps[g]["clue"]]
    return "；".join(clues)


def _candidates(task: dict, gaps: dict[str, dict]) -> list[str]:
    out: list[str] = []
    for g in task["gap_ids"]:
        for c in (gaps.get(g) or {}).get("candidates") or []:
            if c not in out:
                out.append(c)
    return out


def task_reason(task: dict, by_id: dict[str, dict], gaps: dict[str, dict]) -> str | None:
    """未完成/不执行原因，面向用户如实说明；可执行任务返回 None。"""
    check = task["check"]
    if check == "ready":
        return None
    if check == "needs_history":
        # STEP-Q16：追溯工作流给出的真实原因优先；未进入追溯（如预算未配置）时保持原说明
        return task.get("recall_reason") or HISTORY_UNSUPPORTED
    if check == "needs_user_input":
        note = _gap_note(task, gaps)
        return f"需要你补充：{note}" if note else "需要你补充必要条件"
    if check == "ambiguous":
        cands = _candidates(task, gaps)
        return f"有多个可能的对象（{'、'.join(cands)}），需要你确认" if cands else "指向不明确，需要你确认"
    if check == "blocked_by_dependency":
        waiting = [by_id[d]["goal"] for d in task["depends_on"] if by_id[d]["check"] != "ready"]
        return f"依赖的「{'」「'.join(waiting)}」尚未完成" if waiting else "依赖的任务尚未完成"
    if check == "out_of_scope":
        return OUT_OF_SCOPE_REASON
    return "未完成"


def settle(prep: dict) -> dict:
    """服务端逐任务复核：依赖未就绪的任务不执行；汇总出口，不把部分完成写成全部完成。"""
    tasks = [dict(t) for t in prep["tasks"]]
    by_id = {t["task_id"]: t for t in tasks}
    gaps = {g["gap_id"]: g for g in prep["information_gaps"]}
    changed = True
    while changed:
        changed = False
        for t in tasks:
            if t["check"] == "ready" and any(by_id[d]["check"] != "ready" for d in t["depends_on"]):
                t["check"] = "blocked_by_dependency"
                changed = True
    for t in tasks:
        t["reason"] = task_reason(t, by_id, gaps)
    ready = [t for t in tasks if t["check"] == "ready"]
    unfinished = [t for t in tasks if t["check"] != "ready"]
    if ready:
        outcome = "run"
    elif any(t["check"] in ("needs_user_input", "ambiguous") for t in tasks):
        outcome = "clarify"
    elif any(t["check"] != "out_of_scope" for t in tasks):
        outcome = "unfinished"
    else:
        outcome = "refused"
    return {
        **prep,
        "tasks": tasks,
        "outcome": outcome,
        "partial": bool(ready and (unfinished or prep["excluded"])),
    }


def task_brief(settled: dict) -> str:
    """交给现有 Rewrite / Generate 的任务说明（Q17、Q18 接手后改为正式交接）。"""
    lines = ["本轮任务（来自任务准备；只执行标「执行」的项）："]
    for t in settled["tasks"]:
        head = f"{t['task_id']} {t['mode']}：{t['goal']}"
        if t["check"] == "ready":
            extra = []
            if t["scope"]:
                extra.append(f"范围：{t['scope']}")
            if t["constraints"]:
                extra.append(f"约束：{'；'.join(t['constraints'])}")
            lines.append(f"- [执行] {head}" + (f"（{'；'.join(extra)}）" if extra else ""))
        else:
            lines.append(f"- [未完成] {head}：{t['reason']}")
    for e in settled["excluded"]:
        lines.append(f"- [不执行] {e['text']}：{OUT_OF_SCOPE_REASON}")
    if settled["response_constraint"]:
        lines.append(f"回答约束：{settled['response_constraint']}")
    if settled["partial"]:
        lines.append(
            "要求：只回答「执行」项；在回答末尾逐项如实说明「未完成」「不执行」项及原因，"
            "不得写成已完成，也不得把未知的一方写成没有规则。"
        )
    return "\n".join(lines)


def pending_text(settled: dict) -> str:
    """交给 Clarification Generator 的「尚未解决的信息点」与候选。"""
    gaps = {g["gap_id"]: g for g in settled["information_gaps"]}
    lines = []
    for t in settled["tasks"]:
        if t["check"] not in ("needs_user_input", "ambiguous"):
            continue
        line = f"- {t['goal']}"
        note = _gap_note(t, gaps)
        if note:
            line += f"：{note}"
        cands = _candidates(t, gaps)
        if cands:
            line += f"；候选：{'、'.join(cands)}"
        lines.append(line)
    return "\n".join(lines)


def unfinished_text(settled: dict) -> str:
    """没有可执行任务、也不需要用户补充时的如实说明（不调用模型）。"""
    lines = ["本轮未能完成："]
    for t in settled["tasks"]:
        lines.append(f"- {t['goal']}：{t['reason']}")
    for e in settled["excluded"]:
        lines.append(f"- {e['text']}：{OUT_OF_SCOPE_REASON}")
    return "\n".join(lines)


def prep_record(settled: dict | None, carry: dict | None, error: TaskPrepError | None = None) -> dict:
    """写入 Runtime task_prep 列；只写一次。"""
    base = {
        "ver": TASK_PREP_VER,
        "carry": None if not carry else {
            "from_exec_id": carry["from_exec_id"],
            "from_logical_round_id": carry["from_logical_round_id"],
        },
    }
    if settled is None:
        err = error or TaskPrepError("task_prep_fail", "unknown")
        base.update({"valid": False, "error": err.code, "detail": err.detail})
        if err.code == "task_prep_invalid" and err.raw:
            base["raw"] = err.raw[:500]
        return base
    base.update({
        "valid": True,
        "error": None,
        "tasks": settled["tasks"],
        "excluded": settled["excluded"],
        "information_gaps": settled["information_gaps"],
        "response_constraint": settled["response_constraint"],
        "outcome": settled["outcome"],
        "partial": settled["partial"],
        "extra_keys": settled.get("extra_keys") or [],
    })
    return base


# ---------- 跨轮承接（S01 §18.8；G-E01 ⑤） ----------

def find_carry(rows: list[dict], before_seq: int, get_round: Callable[[str], dict | None]) -> dict | None:
    """rows 须已过清空边界（effective_messages）。只看 before_seq 之前最近一个逻辑回合的当前版本执行，
    且其结果为澄清或部分完成；否则无承接。不受 L1 窗口限制。"""
    users = [r for r in rows if r.get("role") == "user" and int(r.get("seq") or 0) < int(before_seq)]
    if not users:
        return None
    last = users[-1]
    current = [
        r for r in rows
        if r.get("role") == "assistant" and r.get("round_id") == last.get("round_id") and r.get("is_current")
    ]
    if not current:
        return None
    reply = current[-1]
    run = get_round(str(reply.get("exec_id") or "")) or {}
    if run.get("biz_result") not in CARRY_RESULTS:
        return None
    prep = run.get("task_prep") if isinstance(run.get("task_prep"), dict) else None
    tasks = (prep or {}).get("tasks") if (prep or {}).get("valid") else None
    gaps = {g["gap_id"]: g for g in ((prep or {}).get("information_gaps") or [])}
    return {
        "from_exec_id": str(reply.get("exec_id") or ""),
        "from_logical_round_id": last.get("round_id"),
        "biz_result": run.get("biz_result"),
        "original": str(last.get("content") or ""),
        "reply": str(reply.get("content") or "")[:1000],
        "unfinished": [
            {
                "goal": t["goal"],
                "reason": t.get("reason") or "",
                "candidates": _candidates(t, gaps),
            }
            for t in (tasks or []) if t.get("check") not in ("ready", "out_of_scope")
        ],
        "delivered": [t["goal"] for t in (tasks or []) if t.get("check") == "ready"],
        "excluded": [e["text"] for e in ((prep or {}).get("excluded") or [])]
        + [t["goal"] for t in (tasks or []) if t.get("check") == "out_of_scope"],
    }


def carry_text(carry: dict) -> str:
    label = "澄清" if carry["biz_result"] == "clarify" else "部分完成"
    lines = [
        f"上一轮结果：{label}",
        f"原任务原句：{carry['original']}",
        f"上一轮回复：{carry['reply']}",
    ]
    if carry["unfinished"]:
        lines.append("未完成项：")
        for u in carry["unfinished"]:
            line = f"- {u['goal']}"
            if u["reason"]:
                line += f"（{u['reason']}）"
            if u["candidates"]:
                line += f"；候选：{'、'.join(u['candidates'])}"
            lines.append(line)
    if carry["delivered"]:
        lines.append("已交付项（不要重做）：" + "；".join(carry["delivered"]))
    if carry["excluded"]:
        lines.append("已标越界（不自动执行）：" + "；".join(carry["excluded"]))
    return "\n".join(lines)


def build_prep_messages(
    original: str, l1_turns: list[dict], route: str, requires_history: bool, carry: str | None = None,
) -> list[dict]:
    parts = [
        format_l1(l1_turns),
        f"Router：route={route}，requires_history={'true' if requires_history else 'false'}",
        f"承接线索：\n{carry}" if carry else "承接线索：（无）",
        f"当前原句：{original}",
        "只输出 JSON。",
    ]
    return [
        {"role": "system", "content": settings.TASK_PREP_PROMPT},
        {"role": "user", "content": "\n\n".join(parts)},
    ]


class TaskPreparer:
    def __init__(self, models: Any) -> None:
        self.models = models

    async def prepare(
        self, original: str, l1_turns: list[dict], route: str, requires_history: bool, cfg: dict,
        carry: str | None = None,
    ) -> dict:
        messages = build_prep_messages(original, l1_turns, route, requires_history, carry)
        messages[0]['content'] = slot_text('task_prep', cfg)
        try:
            raw = await self.models.rewrite(messages, temperature=float(cfg.get("temperature") or 0))
        except ModelError as exc:
            if exc.code == "missing_key":
                raise TaskPrepError("missing_key", exc.message, message=exc.message) from exc
            raise TaskPrepError("task_prep_fail", exc.message) from exc
        except Exception as exc:  # noqa: BLE001
            raise TaskPrepError("task_prep_fail", str(exc)) from exc
        return parse_task_prep(raw)
