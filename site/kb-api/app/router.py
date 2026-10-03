# -*- coding: utf-8 -*-
"""STEP-Q11：Conversation Router v3。只分类 route 与 requires_history，不检索、不改写、不回答。"""
from __future__ import annotations

import json
import math
import re
from typing import Any

from . import settings
from .models_ext import ModelError
from .prompts import router_text
from .util import excerpt

# S01 §7.2 已确认的六类主入口
ROUTES = (
    "knowledge_query",
    "conversation_task",
    "ack",
    "smalltalk",
    "out_of_scope",
    "unclear",
)
ROUTER_FIELDS = ("route", "requires_history", "confidence", "reason")
ROUTER_PROMPT_VER = "router-v3"
ROUTER_FAIL_MESSAGE = "问题分类失败，本轮未检索、未生成。可重试。"

_JSON_RE = re.compile(r"\{.*\}", re.S)


class RouterError(Exception):
    """分类执行异常，不是业务 unclear。code：router_invalid / router_fail / missing_key。"""

    def __init__(self, code: str, detail: str, raw: str = "", message: str = "") -> None:
        super().__init__(detail)
        self.code = code
        self.detail = detail
        self.raw = raw or ""
        self.message = message or ROUTER_FAIL_MESSAGE


def _invalid(detail: str, raw: str) -> RouterError:
    return RouterError("router_invalid", detail, raw)


def parse_router_output(raw: str) -> dict:
    """按 G-E01 Router Schema 校验；任一字段非法即 router_invalid，不猜、不补默认值。"""
    text = (raw or "").strip()
    if not text:
        raise RouterError("router_fail", "empty_response", raw or "")
    try:
        obj: Any = json.loads(text)
    except json.JSONDecodeError:
        m = _JSON_RE.search(text)
        if not m:
            raise _invalid("not_json", text)
        try:
            obj = json.loads(m.group(0))
        except json.JSONDecodeError:
            raise _invalid("not_json", text)
    if not isinstance(obj, dict):
        raise _invalid("not_object", text)
    for key in ROUTER_FIELDS:
        if key not in obj:
            raise _invalid(f"missing:{key}", text)
    route = obj["route"]
    if not isinstance(route, str) or route not in ROUTES:
        raise _invalid("route", text)
    requires_history = obj["requires_history"]
    # 只认 JSON 布尔值；"true"、0/1 都不能替代
    if not isinstance(requires_history, bool):
        raise _invalid("requires_history", text)
    confidence = obj["confidence"]
    if (
        isinstance(confidence, bool)
        or not isinstance(confidence, (int, float))
        or not math.isfinite(float(confidence))
        or not 0 <= float(confidence) <= 1
    ):
        raise _invalid("confidence", text)
    reason = obj["reason"]
    if not isinstance(reason, str) or not reason.strip():
        raise _invalid("reason", text)
    return {
        "route": route,
        "requires_history": requires_history,
        "confidence": float(confidence),
        "reason": reason.strip(),
        # 多余字段不使用，只记字段名
        "extra_keys": sorted(str(k) for k in obj if k not in ROUTER_FIELDS),
    }


def format_l1(l1_turns: list[dict]) -> str:
    """L1 完整回合按旧→新列出；为空时明确写「（无）」，不让模型以为漏传。"""
    lines: list[str] = []
    for i, t in enumerate(l1_turns or [], 1):
        lines.append(f"[回合{i}] User: {t.get('user') or ''}\nAssistant: {t.get('assistant') or ''}")
    return f"相关 L1（旧→新，共 {len(lines)} 个完整回合）：\n" + ("\n\n".join(lines) or "（无）")


def build_router_messages(original: str, l1_turns: list[dict], carry: str | None = None, prompt: str | None = None) -> list[dict]:
    """输入：服务端 L1 全部完整回合（已受 10 回合 / 5000 tokens 限制）+ 当前原句；承接线索由 Q13 提供。"""
    parts = [format_l1(l1_turns)]
    if carry:
        parts.append(f"承接线索：\n{carry}")
    parts.append(f"当前输入：{original}")
    parts.append("只输出 JSON。")
    return [
        {"role": "system", "content": prompt or settings.ROUTER_PROMPT},
        {"role": "user", "content": "\n\n".join(parts)},
    ]


def router_runtime(result: dict | None, error: RouterError | None = None) -> dict:
    """写入 Runtime 的原始分类。只在 Router 这一步写一次，后续恢复不改写。"""
    if result is not None:
        return {
            "route": result["route"],
            "requires_history": result["requires_history"],
            "router": {
                "confidence": result["confidence"],
                "reason": result["reason"],
                "valid": True,
                "error": None,
                "extra_keys": result.get("extra_keys") or [],
                "prompt_ver": ROUTER_PROMPT_VER,
            },
        }
    err = error or RouterError("router_fail", "unknown")
    info: dict = {
        "confidence": None,
        "reason": None,
        "valid": False,
        "error": err.code,
        "detail": err.detail,
        "extra_keys": [],
        "prompt_ver": ROUTER_PROMPT_VER,
    }
    if err.code == "router_invalid" and err.raw:
        info["raw"] = excerpt(err.raw)
    return {"route": None, "requires_history": None, "router": info}


class ConversationRouter:
    def __init__(self, models: Any) -> None:
        self.models = models

    async def route(self, original: str, l1_turns: list[dict], cfg: dict, carry: str | None = None) -> dict:
        messages = build_router_messages(original, l1_turns, carry, prompt=router_text(cfg))
        try:
            raw = await self.models.rewrite(messages, temperature=float(cfg.get("temperature") or 0))
        except ModelError as exc:
            if exc.code == "missing_key":
                raise RouterError("missing_key", exc.message, message=exc.message) from exc
            raise RouterError("router_fail", exc.message) from exc
        except Exception as exc:  # noqa: BLE001
            raise RouterError("router_fail", str(exc)) from exc
        return parse_router_output(raw)
