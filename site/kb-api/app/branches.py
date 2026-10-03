# -*- coding: utf-8 -*-
"""STEP-Q12：非知识分支。ack / out_of_scope 取话术池；smalltalk 简短回应；unclear 生成一句澄清。
这些分支不调用 Memory / Knowledge，只依赖各自实际用到的模型或配置。"""
from __future__ import annotations

import json
import random
import re
from datetime import datetime, timezone
from typing import Any, Sequence

from . import settings
from .prompts import slot_text
from .listing import display_tz
from .models_ext import ModelError
from .router import format_l1

# 非知识分支：不检查知识索引
NON_KNOWLEDGE_ROUTES = ("ack", "out_of_scope", "smalltalk", "unclear")
# 各分支的业务结果（Runtime biz_result）
ROUTE_BIZ_RESULT = {
    "ack": "not_applicable",
    "smalltalk": "not_applicable",
    "out_of_scope": "refused",
    "unclear": "clarify",
}

_JSON_RE = re.compile(r"\{.*\}", re.S)
SMALLTALK_FAIL_MESSAGE = "回复生成失败，可重试。"
# 生成失败不等于用户没说清楚（§7.9 规则 6），不写成反问
CLARIFY_FAIL_MESSAGE = "澄清问题生成失败，本轮未检索、未生成。可重试。"


class BranchError(Exception):
    """分支执行异常；不伪装成正常回复。"""

    def __init__(self, code: str, detail: str, message: str) -> None:
        super().__init__(detail)
        self.code = code
        self.detail = detail
        self.message = message


def pick_reply(pool: Sequence[str], rng: Any = random) -> str:
    items = [str(x).strip() for x in pool or () if str(x).strip()]
    if not items:
        raise BranchError("reply_pool_empty", "empty_pool", "暂时无法回复，请稍后再试。")
    return rng.choice(items)


def local_time_text(time_base: Any) -> str | None:
    """STEP-Q18（G-E08）：UTC 存储的提问时间换成显示时区（KB_DISPLAY_TZ）的本地时间；不用服务器本地时区。"""
    if not time_base:
        return None
    if isinstance(time_base, datetime):
        value = time_base
    else:
        try:
            value = datetime.fromisoformat(str(time_base).strip().replace("T", " ")[:26])
        except ValueError:
            return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    local = value.astimezone(display_tz())
    return f"{local.strftime('%Y-%m-%d %H:%M')}（{settings.DISPLAY_TZ}）"


def time_context(time_base: Any) -> str:
    """本轮时间基准：原问题的提问时间；刷新沿用原问题时间。"""
    text = local_time_text(time_base)
    if not text:
        return "本轮提问时间：未知（相对时间无法换算时如实说明）"
    return f"本轮提问时间：{text}；“昨天”“上周”等相对时间以此为基准，不以当前日期代替。"


async def smalltalk_reply(models: Any, original: str, l1_turns: list[dict], cfg: dict) -> str:
    messages = [
        {"role": "system", "content": slot_text('smalltalk', cfg)},
        {"role": "user", "content": f"{format_l1(l1_turns)}\n\n当前输入：{original}"},
    ]
    fail = SMALLTALK_FAIL_MESSAGE
    try:
        raw = await models.rewrite(messages, temperature=float(cfg.get("temperature") or 0))
    except ModelError as exc:
        if exc.code == "missing_key":
            raise BranchError("missing_key", exc.message, exc.message) from exc
        raise BranchError("smalltalk_fail", exc.message, fail) from exc
    except Exception as exc:  # noqa: BLE001
        raise BranchError("smalltalk_fail", str(exc), fail) from exc
    text = (raw or "").strip()
    if not text:
        raise BranchError("smalltalk_fail", "empty_response", fail)
    return text


def parse_clarification(raw: str) -> str:
    """S01 §7.9：合法 JSON，唯一字段 clarification，值为非空字符串。"""
    fail = CLARIFY_FAIL_MESSAGE
    text = (raw or "").strip()
    if not text:
        raise BranchError("clarify_fail", "empty_response", fail)
    try:
        obj: Any = json.loads(text)
    except json.JSONDecodeError:
        m = _JSON_RE.search(text)
        try:
            obj = json.loads(m.group(0)) if m else None
        except json.JSONDecodeError:
            obj = None
    if not isinstance(obj, dict) or set(obj) != {"clarification"}:
        raise BranchError("clarify_invalid", "schema", fail)
    value = obj["clarification"]
    if not isinstance(value, str) or not value.strip():
        raise BranchError("clarify_invalid", "clarification", fail)
    return value.strip()


def build_clarify_messages(
    original: str, l1_turns: list[dict], stop_reason: str, time_base: str | None,
    pending: str | None = None, recovered: str | None = None,
) -> list[dict]:
    # STEP-Q13：任务准备给出的待补信息点与候选、承接线索按 §7.9 输入项传入；Router unclear 时均为空
    parts = [
        format_l1(l1_turns),
        f"已恢复的必要历史：\n{recovered}" if recovered else "已恢复的必要历史：（无）",
    ]
    if pending:
        parts.append(f"尚未解决的信息点：\n{pending}")
    parts += [
        f"停止原因：{stop_reason}",
        time_context(time_base),
        f"当前原句：{original}",
        "只输出 JSON。",
    ]
    return [
        {"role": "system", "content": settings.CLARIFY_PROMPT},
        {"role": "user", "content": "\n\n".join(parts)},
    ]


async def clarify(
    models: Any, original: str, l1_turns: list[dict], cfg: dict, stop_reason: str, time_base: str | None,
    pending: str | None = None, recovered: str | None = None,
) -> str:
    messages = build_clarify_messages(original, l1_turns, stop_reason, time_base, pending, recovered)
    messages[0]['content'] = slot_text('clarify', cfg)
    fail = CLARIFY_FAIL_MESSAGE
    try:
        raw = await models.rewrite(messages, temperature=float(cfg.get("temperature") or 0))
    except ModelError as exc:
        if exc.code == "missing_key":
            raise BranchError("missing_key", exc.message, exc.message) from exc
        raise BranchError("clarify_fail", exc.message, fail) from exc
    except Exception as exc:  # noqa: BLE001
        raise BranchError("clarify_fail", str(exc), fail) from exc
    return parse_clarification(raw)
