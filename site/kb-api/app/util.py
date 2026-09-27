# -*- coding: utf-8 -*-
"""通用小函数：哈希、ID、数字抽取、摘录。"""
from __future__ import annotations

import hashlib
import json
import re
import time
import uuid
from typing import Any, Iterable


NUMBER_RE = re.compile(r"\d+(?:\.\d+)?")
# 千分位：10,000 → 10000；不处理小数点后的数字。
THOUSANDS_RE = re.compile(r"(\d),(\d{3})\b")
# 出处序号：[1]、块2、块[3]，不当作回答里发明的规则数字。
CITATION_MARK_RE = re.compile(r"\[\d+\]|块\s*\[?\d+\]?")
NUMBER_LEAK_NOTE = "含块外数字，请打开出处核对原文，不要把问答当需求合同。"


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def estimate_tokens(text: str) -> int:
    """保守估计：按字符数，超过 embedding 8192 上限则不入库。"""
    return len(text or "")


def uid(prefix: str) -> str:
    return f"{prefix}-{int(time.time() * 1000):x}-{uuid.uuid4().hex[:8]}"


def excerpt(text: str, limit: int = 500) -> str:
    t = (text or "").strip()
    return t[:limit]


def join_thousands(text: str) -> str:
    """把正文里的千分位逗号拼回完整数字，便于 10,000 与 10000 视为同一数字。"""
    prev = text or ""
    while True:
        nxt = THOUSANDS_RE.sub(r"\1\2", prev)
        if nxt == prev:
            return nxt
        prev = nxt


def strip_citation_markers(text: str) -> str:
    """去掉回答里的出处序号，避免 [2] 触发数字门禁。"""
    return CITATION_MARK_RE.sub(" ", text or "")


def extract_numbers(text: str) -> set[str]:
    return set(NUMBER_RE.findall(join_thousands(text or "")))


def json_dumps(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False)


def json_loads(raw: Any, default: Any = None) -> Any:
    if raw is None or raw == "":
        return default
    if isinstance(raw, (dict, list)):
        return raw
    try:
        return json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        return default


def stable_point_id(path: str, chunk_id: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"{path}::{chunk_id}"))


def truncate18(text: str) -> str:
    t = re.sub(r"\s+", " ", str(text or "")).strip()
    if len(t) > 18:
        return t[:18]
    return t or "新对话"


def unique_keep_order(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out
