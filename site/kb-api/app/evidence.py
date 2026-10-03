# -*- coding: utf-8 -*-
"""STEP-Q19：Evidence check 与最多一次修正（S01 §11.7）。
同一份本轮 c_gen 用于生成、检查、修正与复查；检查异常不放行；修正次数由后端维护。"""
from __future__ import annotations

import json
import re
from typing import Any

from . import settings
from .prompts import slot_text
from .models_ext import ModelError
from .util import extract_numbers, sha256_text, strip_citation_markers

CHECK_VER = "check-v1"
CHECK_FIELDS = ("check_status", "issues", "conflict")
MAX_ISSUES = 12
# G-E02（Q19）：修正需剩余时间覆盖一次修正与一次复查
REPAIR_MIN_REMAINING_SEC = 120

CHECK_FAIL_MESSAGE = "证据检查失败，本轮回答未交付。可重试。"
NOT_RELIABLE_MESSAGE = "该问题未能形成可靠回答：回答内容未通过本轮知识原文的核对{suffix}。可换个问法或打开出处阅读原文。"

_JSON_RE = re.compile(r"\{.*\}", re.S)
_SPACE_RE = re.compile(r"\s+")


class CheckError(Exception):
    """检查或修正执行异常：check_invalid / check_fail / repair_fail / missing_key。不当 pass。"""

    def __init__(self, code: str, detail: str, raw: str = "") -> None:
        super().__init__(detail)
        self.code = code
        self.detail = detail
        self.raw = raw or ""


def evidence_items(c_gen: list[dict]) -> list[dict]:
    """本轮临时证据 ID（E1…）映射到服务端来源身份；不建立长期 ID。"""
    out = []
    for i, b in enumerate(c_gen, 1):
        out.append({
            "evidence_id": f"E{i}",
            "path": b.get("path") or "",
            "chunk_id": b.get("chunk_id") or "",
            "content_hash": b.get("content_hash") or "",
            "content_scope": b.get("content_scope") or "full",
            "content": str(b.get("content") or ""),
        })
    return out


def _norm(text: str) -> str:
    return _SPACE_RE.sub("", text or "")


def number_issue(answer: str, c_gen: list[dict], original: str = "") -> dict | None:
    """G-E02（Q19）：旧数字规则并入检查——回答里的数字不在证据与问句中即为一条问题。"""
    allowed: set[str] = set()
    for b in c_gen:
        allowed |= extract_numbers(b.get("content") or "")
    allowed |= extract_numbers(original or "")
    leaked = sorted(extract_numbers(strip_citation_markers(answer or "")) - allowed)
    if not leaked:
        return None
    return {
        "answer_span": "",
        "evidence_ids": [],
        "reason": f"回答中的数字 {'、'.join(leaked)} 不在本轮证据中",
        "source": "numbers",
    }


def parse_check(raw: str, evidence_ids: list[str], draft: str) -> dict:
    """S01 §11.7.2：pass ⇔ issues 为空；来源 ID 必须属于本轮；answer_span 不能编造草稿里没有的原句。"""
    text = (raw or "").strip()
    if not text:
        raise CheckError("check_fail", "empty_response")
    try:
        obj: Any = json.loads(text)
    except json.JSONDecodeError:
        m = _JSON_RE.search(text)
        try:
            obj = json.loads(m.group(0)) if m else None
        except json.JSONDecodeError:
            obj = None
        if obj is None:
            raise CheckError("check_invalid", "not_json", text)
    if not isinstance(obj, dict):
        raise CheckError("check_invalid", "not_object", text)
    for key in CHECK_FIELDS:
        if key not in obj:
            raise CheckError("check_invalid", f"missing:{key}", text)
    status = obj["check_status"]
    if status not in ("pass", "fail"):
        raise CheckError("check_invalid", "check_status", text)
    if not isinstance(obj["conflict"], bool):
        raise CheckError("check_invalid", "conflict", text)
    issues_raw = obj["issues"]
    if not isinstance(issues_raw, list) or len(issues_raw) > MAX_ISSUES:
        raise CheckError("check_invalid", "issues", text)
    if (status == "pass") != (not issues_raw):
        raise CheckError("check_invalid", "status_issues_mismatch", text)
    known = set(evidence_ids)
    body = _norm(draft)
    issues = []
    for it in issues_raw:
        if not isinstance(it, dict):
            raise CheckError("check_invalid", "issue", text)
        span, ids, reason = it.get("answer_span", ""), it.get("evidence_ids", []), it.get("reason")
        if not isinstance(span, str) or not isinstance(reason, str) or not reason.strip():
            raise CheckError("check_invalid", "issue_fields", text)
        if not isinstance(ids, list) or any(not isinstance(x, str) or x not in known for x in ids):
            raise CheckError("check_invalid", "evidence_ids", text)
        if span.strip() and _norm(span) not in body:
            raise CheckError("check_invalid", "answer_span", text)
        issues.append({"answer_span": span.strip()[:300], "evidence_ids": ids, "reason": reason.strip()[:300]})
    return {"check_status": status, "issues": issues, "conflict": obj["conflict"]}


def _evidence_text(evidence: list[dict]) -> str:
    parts = []
    for e in evidence:
        scope = " 正文范围：片段（非全文）" if e["content_scope"] == "excerpt" else ""
        parts.append(f"[{e['evidence_id']}] path={e['path']} chunk_id={e['chunk_id']}{scope}\n{e['content']}")
    return "\n\n".join(parts) or "（无）"


def _context_text(original: str, brief: str | None, query: str, constraint: str) -> str:
    return "\n".join([
        f"当前原句：{original}",
        brief or "本轮任务：按原句作答",
        f"独立问句：{query}",
        f"回答约束：{constraint or '（无）'}",
    ])


def build_check_messages(
    original: str, brief: str | None, query: str, constraint: str, draft: str, evidence: list[dict],
) -> list[dict]:
    user = (
        f"{_context_text(original, brief, query, constraint)}\n\n"
        f"本轮知识原文：\n{_evidence_text(evidence)}\n\n"
        f"待检查答案：\n{draft}\n\n只输出 JSON。"
    )
    return [{"role": "system", "content": settings.CHECK_PROMPT}, {"role": "user", "content": user}]


def build_repair_messages(
    original: str, brief: str | None, query: str, constraint: str, draft: str, issues: list[dict],
    evidence: list[dict],
) -> list[dict]:
    lines = []
    for it in issues:
        span = f"「{it['answer_span']}」" if it.get("answer_span") else "（遗漏或整体问题）"
        ids = "、".join(it.get("evidence_ids") or []) or "无对应来源"
        lines.append(f"- {span}：{it['reason']}（{ids}）")
    user = (
        f"{_context_text(original, brief, query, constraint)}\n\n"
        f"本轮知识原文：\n{_evidence_text(evidence)}\n\n"
        f"原答案草稿：\n{draft}\n\n检查发现的问题：\n" + "\n".join(lines) + "\n\n只输出修正后的答案正文。"
    )
    return [{"role": "system", "content": settings.REPAIR_PROMPT}, {"role": "user", "content": user}]


class EvidenceChecker:
    def __init__(self, models: Any) -> None:
        self.models = models

    async def _call(self, messages: list[dict], cfg: dict, fail_code: str) -> str:
        try:
            return await self.models.rewrite(messages, temperature=0.0)
        except ModelError as exc:
            if exc.code == "missing_key":
                raise CheckError("missing_key", exc.message) from exc
            raise CheckError(fail_code, exc.message) from exc
        except Exception as exc:  # noqa: BLE001
            raise CheckError(fail_code, str(exc)) from exc

    async def check(
        self, original: str, brief: str | None, query: str, constraint: str, draft: str, evidence: list[dict],
        cfg: dict,
    ) -> dict:
        messages = build_check_messages(original, brief, query, constraint, draft, evidence)
        messages[0]['content'] = slot_text('check', cfg)
        raw = await self._call(messages, cfg, "check_fail")
        return parse_check(raw, [e["evidence_id"] for e in evidence], draft)

    async def repair(
        self, original: str, brief: str | None, query: str, constraint: str, draft: str, issues: list[dict],
        evidence: list[dict], cfg: dict,
    ) -> str:
        messages = build_repair_messages(original, brief, query, constraint, draft, issues, evidence)
        messages[0]['content'] = slot_text('repair', cfg)
        text = (await self._call(messages, cfg, "repair_fail") or "").strip()
        if not text:
            raise CheckError("repair_fail", "empty_response")
        return text


def draft_hash(text: str) -> str:
    """草稿关联：检查结论只对这份正文有效（AT-36）。"""
    return sha256_text(text or "")
