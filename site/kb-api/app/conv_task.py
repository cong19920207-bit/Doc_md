# -*- coding: utf-8 -*-
"""STEP-Q20：conversation_task 的回看、旧版本找回、仅重述（S01 §7.4、§6.16、§20.2）。
回看与找回版本不调模型，原样返回已保存原文并标出处；仅重述只把原文交给模型换表达并标「未重新核验」。
三者都不调用 Knowledge RAG，找回旧版本不改当前采用版本。"""
from __future__ import annotations

import re
from typing import Any

from . import settings
from .prompts import slot_text
from .models_ext import ModelError

CONV_MODES = ("回看", "重述")
REPLAY_HEAD = "以下是此前对话中保存的原文（原样返回，未重新核验）："
RESTATE_HEAD = "以下是对此前回答的重述（只调整表达，未重新核验）："
RESTATE_FAIL_MESSAGE = "重述生成失败，可重试。"
NO_TARGET = "没有找到可回看或重述的此前内容"

_VERSION_RE = re.compile(r"版本|第\s*([0-9一二三四五六七八九十]+)\s*版|上一版|上个版|旧版|之前那版|原来那版")
_CN = {"一": 1, "二": 2, "两": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9, "十": 10}


class RestateError(Exception):
    def __init__(self, code: str, detail: str) -> None:
        super().__init__(detail)
        self.code = code
        self.detail = detail


def is_conversation_only(route: str, ready_tasks: list[dict]) -> bool:
    """所有就绪任务都是回看/重述才走本执行；夹杂查询、核验等仍走知识链路（「哪个版本符合现行规则」属 Q18）。"""
    return route == "conversation_task" and bool(ready_tasks) and all(t["mode"] in CONV_MODES for t in ready_tasks)


def wants_version(text: str) -> bool:
    return bool(_VERSION_RE.search(text or ""))


def pick_versions(text: str, versions: list[dict]) -> list[dict]:
    """「第一版」取该号；「上个版本」取当前采用版本的前一个；其余列出全部版本。"""
    if not versions:
        return []
    m = re.search(r"第\s*([0-9一二三四五六七八九十]+)\s*版", text or "")
    if m:
        raw = m.group(1)
        n = int(raw) if raw.isdigit() else _CN.get(raw)
        return [v for v in versions if v.get("version_no") == n]
    if re.search(r"上一版|上个版|之前那版|原来那版|旧版", text or ""):
        cur = next((i for i, v in enumerate(versions) if v.get("is_current")), len(versions) - 1)
        return [versions[cur - 1]] if cur > 0 else []
    return list(versions)


def _ref(conv_id: str, round_id: str, m: dict) -> dict:
    """历史引用：定位到会话、逻辑回合、消息、版本、时间与范围；与知识引用区分类型。"""
    return {
        "type": "history", "conversation_id": conv_id, "round_id": round_id, "message_id": m["message_id"],
        "role": m["role"], "version_no": m.get("version_no"), "time": m.get("time") or "",
        "time_reliable": m.get("time_reliable", True), "range": m.get("range"),
        "completeness": m.get("completeness"),
    }


def _label(m: dict) -> str:
    who = "用户" if m["role"] == "user" else ("回答" + (f"（第 {m['version_no']} 版）" if m.get("version_no") else ""))
    extra = []
    if m.get("time"):
        extra.append(m["time"] + ("" if m.get("time_reliable", True) else "，时间不可靠"))
    if m.get("completeness") == "fragment":
        extra.append(f"片段 {m['range'][0]}～{m['range'][1]}/{m['total_chars']} 字")
    return who + (f"［{'；'.join(extra)}］" if extra else "")


def replay(conv_id: str, views: list[dict]) -> tuple[str, list[dict]]:
    """回看：原样拼出已保存原文与出处，不调模型。"""
    lines = [REPLAY_HEAD]
    refs: list[dict] = []
    for v in views:
        lines.append(f"【此前对话·回合 {v['round_id']}】")
        for m in v["messages"]:
            lines.append(f"{_label(m)}：{m['text']}")
            refs.append(_ref(conv_id, v["round_id"], m))
    return "\n".join(lines), refs


def replay_versions(conv_id: str, round_view: dict, picked: list[dict], all_versions: list[dict]) -> tuple[str, list[dict]]:
    """找回旧版本：只读原文与时间，不重新生成，也不设为默认版本。"""
    user = next((m for m in round_view["messages"] if m["role"] == "user"), None)
    lines = [REPLAY_HEAD]
    refs: list[dict] = []
    if user:
        lines.append(f"{_label(user)}：{user['text']}")
        refs.append(_ref(conv_id, round_view["round_id"], user))
    for m in picked:
        tag = "（当前采用版本）" if m.get("is_current") else "（非当前采用版本，找回不会改变默认显示）"
        lines.append(f"{_label(m)}{tag}：{m['text']}")
        refs.append(_ref(conv_id, round_view["round_id"], m))
    lines.append(f"该问题共保存 {len(all_versions)} 个回答版本。")
    return "\n".join(lines), refs


def restate_source(views: list[dict]) -> list[dict]:
    """重述只针对回答原文；取给定回合中的回答（当前采用版本）。"""
    return [m for v in views for m in v["messages"] if m["role"] == "assistant"]


def restate_refs(conv_id: str, views: list[dict]) -> list[dict]:
    """重述的出处：被重述的那条回答原文。"""
    return [_ref(conv_id, v["round_id"], m) for v in views for m in v["messages"] if m["role"] == "assistant"]


async def restate(models: Any, original: str, answers: list[dict], cfg: dict) -> str:
    texts = [m["text"] for m in answers]
    # 一条原文不加编号；多条只用分隔线隔开，避免模型把「原文 N」写进正文
    body = texts[0] if len(texts) == 1 else "\n\n——\n\n".join(texts)
    messages = [
        {"role": "system", "content": slot_text('restate', cfg)},
        {"role": "user", "content": f"用户的表达要求：{original}\n\n此前回答原文：\n{body}"},
    ]
    try:
        raw = await models.rewrite(messages, temperature=float(cfg.get("temperature") or 0))
    except ModelError as exc:
        raise RestateError("missing_key" if exc.code == "missing_key" else "restate_fail", exc.message) from exc
    except Exception as exc:  # noqa: BLE001
        raise RestateError("restate_fail", str(exc)) from exc
    text = (raw or "").strip()
    if not text:
        raise RestateError("restate_fail", "empty_response")
    return f"{RESTATE_HEAD}\n{text}"
