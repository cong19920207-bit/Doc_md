# -*- coding: utf-8 -*-
"""改写 → 分路/单路召回 → 重排 → 流式回答。"""
from __future__ import annotations

import json
import logging
import re
from typing import Any, AsyncIterator, Callable

from . import settings
from .prompts import slot_text
from .aliases import collection_for, filter_named_ids, format_alias_hint, known_feature_ids
from .models_ext import ModelClients, ModelError
from .store import VectorStore
from .util import excerpt, extract_numbers, strip_citation_markers

log = logging.getLogger("kb-api.pipeline")

JSON_RE = re.compile(r"\{.*\}", re.S)


def parse_rewrite(raw: str) -> dict:
    text = (raw or "").strip()
    try:
        obj = json.loads(text)
    except json.JSONDecodeError:
        m = JSON_RE.search(text)
        if not m:
            raise ValueError("改写结果不是 JSON")
        obj = json.loads(m.group(0))
    query = str(obj.get("rewrite_query") or obj.get("query") or "").strip()
    if not query:
        raise ValueError("改写独立问句为空")
    same = bool(obj.get("same_topic"))
    named = filter_named_ids(obj.get("named_feature_ids") or [])
    return {"rewrite_query": query, "same_topic": same, "named_feature_ids": named}


REWRITE_V3_VER = "rewrite-v3"
REWRITE_V3_FIELDS = (
    "status", "standalone_query", "response_constraint", "missing_context", "confidence",
    "named_feature_ids", "same_topic",
)
MISSING_CONTEXT_TYPES = ("history_object", "user_condition")


class RewriteInvalid(ValueError):
    """STEP-Q17：Rewriter v3 输出不合 Schema；按改写失败处理，不猜 Query。"""

    def __init__(self, detail: str, raw: str = "") -> None:
        super().__init__(detail)
        self.detail = detail
        self.raw = raw or ""


def parse_rewrite_v3(raw: str, task_ids: list[str] | None = None) -> dict:
    """G-E01/G-E05：新输出按 Schema 校验，再映射旧 Pipeline 字段（rewrite_query、same_topic、named_feature_ids）。
    需要知识结论的多余字段（如「知识库没有规则」）一律不采信，只记字段名。"""
    text = (raw or "").strip()
    if not text:
        raise RewriteInvalid("empty_response", raw or "")
    try:
        obj = json.loads(text)
    except json.JSONDecodeError:
        m = JSON_RE.search(text)
        try:
            obj = json.loads(m.group(0)) if m else None
        except json.JSONDecodeError:
            obj = None
        if obj is None:
            raise RewriteInvalid("not_json", text)
    if not isinstance(obj, dict):
        raise RewriteInvalid("not_object", text)
    for key in REWRITE_V3_FIELDS:
        if key not in obj:
            raise RewriteInvalid(f"missing:{key}", text)
    status = obj["status"]
    if status not in ("ready", "needs_context"):
        raise RewriteInvalid("status", text)
    query = obj["standalone_query"]
    if not isinstance(query, str):
        raise RewriteInvalid("standalone_query", text)
    query = query.strip()
    constraint = obj["response_constraint"]
    if not isinstance(constraint, str):
        raise RewriteInvalid("response_constraint", text)
    confidence = obj["confidence"]
    if isinstance(confidence, bool) or not isinstance(confidence, (int, float)) or not 0 <= float(confidence) <= 1:
        raise RewriteInvalid("confidence", text)
    if not isinstance(obj["same_topic"], bool):
        raise RewriteInvalid("same_topic", text)
    named = obj["named_feature_ids"]
    if not isinstance(named, list) or not all(isinstance(x, str) for x in named):
        raise RewriteInvalid("named_feature_ids", text)
    missing_raw = obj["missing_context"]
    if not isinstance(missing_raw, list):
        raise RewriteInvalid("missing_context", text)
    missing: list[dict] = []
    for item in missing_raw:
        if not isinstance(item, dict) or item.get("type") not in MISSING_CONTEXT_TYPES:
            raise RewriteInvalid("missing_context", text)
        tid = item.get("task_id")
        clue = item.get("clue")
        if not isinstance(tid, str) or not isinstance(clue, str) or not clue.strip():
            raise RewriteInvalid("missing_context", text)
        if task_ids is not None and tid not in task_ids:
            raise RewriteInvalid("missing_context_task", text)
        missing.append({"task_id": tid, "type": item["type"], "clue": clue.strip()[:300]})
    if status == "ready":
        # ready 必须能独立检索；不检索空串
        if not query:
            raise RewriteInvalid("empty_query", text)
        if missing:
            raise RewriteInvalid("ready_with_missing", text)
    else:
        if not missing:
            raise RewriteInvalid("needs_context_without_gap", text)
        query = ""
    return {
        "status": status,
        "standalone_query": query,
        "rewrite_query": query,
        "same_topic": obj["same_topic"],
        "named_feature_ids": filter_named_ids(named),
        "response_constraint": constraint.strip()[:500],
        "missing_context": missing,
        "confidence": float(confidence),
        "extra_keys": sorted(str(k) for k in obj if k not in REWRITE_V3_FIELDS),
        "prompt_ver": REWRITE_V3_VER,
    }


def block_identity(block: dict) -> dict:
    return {
        "path": block.get("path") or "",
        "chunk_id": block.get("chunk_id") or "",
        "anchor": block.get("anchor") or "",
        "feature_id": block.get("feature_id") or "",
        "collection": block.get("collection") or "",
        "heading": block.get("heading") or "",
        "excerpt": excerpt(block.get("content") or ""),
        "content": block.get("content") or "",
        "content_hash": block.get("content_hash") or "",
        # STEP-Q18：full = 入库全文；excerpt = 只能读到片段（hash 已清空，不对应这段文字）
        "content_scope": block.get("content_scope") or "full",
    }


def block_key(block: dict) -> str:
    return f"{block.get('path') or ''}::{block.get('chunk_id') or ''}"


def fill_block_content(block: dict, store: Any = None) -> dict | None:
    """给上轮公开身份卡补回正文。库存与 excerpt 都空则丢弃，避免重排吃空文档。"""
    if not block:
        return None
    out = dict(block)
    content = str(out.get("content") or "").strip()
    if content:
        out["content"] = content
        return out
    path = str(out.get("path") or "")
    chunk_id = str(out.get("chunk_id") or "")
    lookup = getattr(store, "lookup_payload", None) if store is not None else None
    stored = lookup(path, chunk_id) if lookup and path and chunk_id else None
    if stored:
        stored_content = str(stored.get("content") or "").strip()
        if stored_content:
            for key, value in stored.items():
                if str(key).startswith("_"):
                    continue
                # STEP-Q18：hash 必须对应本次正文，不能带着上轮旧 hash 拼上新正文
                if key in ("content", "content_hash") or not out.get(key):
                    out[key] = value
            out["content"] = stored_content
            out["content_scope"] = "full"
            return out
    excerpt_text = str(out.get("excerpt") or "").strip()
    if excerpt_text:
        # 回源失败只剩片段：明确标为片段，清掉不对应这段文字的 hash
        out["content"] = excerpt_text
        out["content_scope"] = "excerpt"
        out["content_hash"] = ""
        return out
    return None


def apply_floor(ordered: list[dict], named_ids: list[str], n: int) -> list[dict]:
    """C18′：点名功能非空时每路至少 1 块；点名数 > n 则 n' = 点名功能数。"""
    n_prime = max(n, len(named_ids)) if len(named_ids) >= 2 else n
    picked: list[dict] = []
    seen: set[str] = set()

    def add(block: dict) -> bool:
        key = f"{block.get('path')}::{block.get('chunk_id')}"
        if key in seen:
            return False
        seen.add(key)
        picked.append(block)
        return True

    if len(named_ids) >= 2:
        for fid in named_ids:
            for block in ordered:
                if block.get("feature_id") == fid:
                    add(block)
                    break
    for block in ordered:
        if len(picked) >= n_prime:
            break
        add(block)
    return picked[:n_prime]


def numbers_ok(answer: str, blocks: list[dict], original: str = "") -> bool:
    """回答数字 ⊆ 生成块数字 ∪ 问句数字；出处序号不计入回答数字。"""
    allowed: set[str] = set()
    for b in blocks:
        allowed |= extract_numbers(b.get("content") or "")
    allowed |= extract_numbers(original or "")
    found = extract_numbers(strip_citation_markers(answer or ""))
    return found <= allowed


def build_rewrite_user(original: str, history_lines: list[str], repo_root=None, task_brief: str | None = None) -> str:
    """改写用户消息：功能 ID 列表 + 口语对照。最终点名仍经 filter_named_ids。
    STEP-Q13：有任务说明时附上，独立问句只覆盖「执行」项（Q17 接手后改为正式交接）。"""
    ids = known_feature_ids(repo_root)
    brief = (
        f"{task_brief}\n独立问句只为「执行」项生成，不写入「未完成」「不执行」项。\n" if task_brief else ""
    )
    return (
        f"已有功能 ID：{json.dumps(ids, ensure_ascii=False)}\n"
        f"口语→功能 ID：\n{format_alias_hint(repo_root)}\n"
        f"上一轮摘要：\n" + ("\n".join(history_lines) or "（无）") + "\n"
        f"本轮原句：{original}\n"
        f"{brief}"
        "只输出 JSON。"
    )


class Pipeline:
    def __init__(self, store: VectorStore, models: ModelClients, config_getter: Callable[[], dict]) -> None:
        self.store = store
        self.models = models
        self.config_getter = config_getter

    async def rewrite(self, original: str, history: list[dict], cfg: dict) -> dict:
        hist_lines = []
        # history 已由 L1 按完整回合和 token 上限组装；旧 history_turns 不得再次截半轮。
        for h in history:
            hist_lines.append(f"{h.get('role')}: {h.get('text')}")
        user = build_rewrite_user(original, hist_lines, task_brief=cfg.get("_task_brief"))
        # STEP-Q17：唯一 Rewriter v3；Prompt 与解析器成套生效，/config 旧 rewrite_prompt 照存不用（后台编辑随 A10）
        messages = [
            {"role": "system", "content": slot_text('rewriter', cfg)},
            {"role": "user", "content": user},
        ]
        raw = await self.models.rewrite(messages, temperature=float(cfg.get("temperature") or 0))
        return parse_rewrite_v3(raw, cfg.get("_task_ids"))

    async def retrieve(
        self,
        original: str,
        rewrite_query: str,
        named_ids: list[str],
        cfg: dict,
    ) -> dict:
        k = int(cfg.get("recall_k") or settings.DEFAULT_K)
        query_text = f"{original}\n{rewrite_query}"
        vectors = await self.models.embed([query_text])
        vector = vectors[0]
        lanes: list[dict] = []
        merged: list[dict] = []
        seen: set[str] = set()

        def absorb(items: list[dict]) -> int:
            count = 0
            for item in items:
                key = item.get("_key") or f"{item.get('path')}::{item.get('chunk_id')}"
                if key in seen:
                    continue
                seen.add(key)
                merged.append(item)
                count += 1
            return count

        if len(named_ids) >= 2:
            for fid in named_ids:
                col = collection_for(fid)
                hits = self.store.hybrid_search(
                    query_text, vector, k, collections=[col], feature_id=fid,
                )
                n = absorb(hits)
                lanes.append({"feature_id": fid, "count": n, "empty": n == 0})
            mode = "multi"
        else:
            hits = self.store.hybrid_search(
                query_text,
                vector,
                k,
                collections=[settings.COLLECTION_CLIENT, settings.COLLECTION_ADMIN],
                feature_id=None,
            )
            absorb(hits)
            mode = "single"
        return {"mode": mode, "candidates": merged, "lanes": lanes, "query_text": query_text}

    async def rerank(
        self,
        rewrite_query: str,
        candidates: list[dict],
        named_ids: list[str],
        prev_blocks: list[dict],
        same_topic: bool,
        cfg: dict,
    ) -> list[dict]:
        pool: list[dict] = []
        seen: set[str] = set()

        def absorb(block: dict) -> None:
            filled = fill_block_content(block, self.store)
            if not filled:
                return
            key = block_key(filled)
            if not key or key == "::" or key in seen:
                return
            if not str(filled.get("content") or "").strip():
                return
            seen.add(key)
            pool.append(filled)

        for item in candidates:
            absorb(item)
        if same_topic:
            for block in prev_blocks or []:
                absorb(block)
        if not pool:
            return []
        n = int(cfg.get("rerank_n") or settings.DEFAULT_N)
        docs = [str(b.get("content") or "")[:4000] for b in pool]
        order = await self.models.rerank(rewrite_query, docs, top_n=min(max(n, len(named_ids), 16), len(docs)))
        ordered = [pool[i] for i in order if 0 <= i < len(pool)]
        leftover = [b for i, b in enumerate(pool) if i not in set(order)]
        return apply_floor(ordered + leftover, named_ids, n)

    def generate_messages(self, original: str, rewrite: dict, c_gen: list[dict], cfg: dict) -> list[dict]:
        empty_named = []
        if len(rewrite.get("named_feature_ids") or []) >= 2:
            present = {b.get("feature_id") for b in c_gen}
            empty_named = [fid for fid in rewrite["named_feature_ids"] if fid not in present]
        parts = []
        for b in c_gen:
            ident = block_identity(b)
            # STEP-Q18：hash 只在对应本次正文时给出；片段明确标注
            meta = f" content_hash={ident['content_hash']}" if ident["content_hash"] else ""
            if ident["content_scope"] == "excerpt":
                meta += " 正文范围：片段（非全文）"
            parts.append(
                f"chunk_id={ident['chunk_id']} path={ident['path']} "
                f"feature_id={ident['feature_id']} collection={ident['collection']} "
                f"anchor={ident['anchor']}{meta}\n{ident['content']}"
            )
        extra = ""
        if empty_named:
            extra = "以下点名功能本轮无块，必须声明这些功能文档未写：" + ", ".join(empty_named) + "。\n"
        # STEP-Q13：任务说明（执行/未完成/不执行与回答约束）送达 Generate；无任务准备时不加
        brief = f"{cfg['_task_brief']}\n" if cfg.get("_task_brief") else ""
        # STEP-Q18：Rewriter 的回答约束、时间、知识版本、相关历史回答与核验目标实际送达
        handoff = self._handoff_text(rewrite, cfg.get("_handoff"))
        user = (
            f"原句：{original}\n独立问句：{rewrite.get('rewrite_query')}\n"
            f"{brief}{handoff}{extra}本轮生成集：\n" + "\n\n".join(parts)
        )
        return [
            {"role": "system", "content": cfg.get("system_prompt") or settings.SYSTEM_PROMPT},
            {"role": "user", "content": user},
        ]

    @staticmethod
    def _handoff_text(rewrite: dict, handoff: dict | None) -> str:
        if not handoff:
            return ""
        lines: list[str] = []
        constraint = str(rewrite.get("response_constraint") or "").strip()
        if constraint:
            lines.append(f"改写给出的回答约束：{constraint}")
        lines.append(f"本轮提问时间：{handoff.get('time_text') or '未知'}")
        lines.append(settings.KNOWLEDGE_VERSION_NOTE)
        history = handoff.get("history") or []
        if history:
            lines.append("相关历史对话（旧→新；只用于理解指代与避免重复，不是知识证据）：\n" + "\n\n".join(history))
        target = handoff.get("verification_target")
        if target:
            lines.append(f"核验目标（被核验的此前回答原文）：\n{target}")
        lines.append(settings.GENERATE_HANDOFF_RULES)
        return "\n".join(lines) + "\n"

    async def stream_answer(
        self, original: str, rewrite: dict, c_gen: list[dict], cfg: dict
    ) -> AsyncIterator[str]:
        messages = self.generate_messages(original, rewrite, c_gen, cfg)
        async for part in self.models.stream_chat(messages, temperature=float(cfg.get("temperature") or 0)):
            yield part


_SENTENCE_SPLIT = re.compile(r"(?<=[。！？\n])")
# 去掉「文档未写」句后仍有足够正文，视为已回答主问题。
_POSITIVE_ANSWER_MIN = 40


def remainder_without_unwritten(text: str) -> str:
    """去掉含「文档未写」的句子，保留其余主回答。"""
    parts = _SENTENCE_SPLIT.split(text or "")
    return "".join(p for p in parts if "文档未写" not in p).strip()


def post_check_answer(text: str, c_gen: list[dict], original: str = "") -> dict:
    """「文档未写」拒答判定；不改写正文。
    STEP-Q19（G-E02）：去掉「块外数字附提示后照常交付」，数字越界只给 numbers_ok=False，由证据检查并入 fail。"""
    t = text or ""
    nums_ok = numbers_ok(t, c_gen, original)
    if "文档未写" not in t:
        return {"text": t, "refused": False, "conflict": False, "numbers_ok": nums_ok}
    remainder = remainder_without_unwritten(t)
    # 有生成块且去掉未写声明后仍有主回答：附带一句未写不把整轮标成拒答。
    if c_gen and len(remainder) >= _POSITIVE_ANSWER_MIN:
        return {"text": t, "refused": False, "conflict": False, "numbers_ok": nums_ok}
    return {"text": t, "refused": True, "conflict": False, "numbers_ok": nums_ok}


def public_c_gen(blocks: list[dict]) -> list[dict]:
    out = []
    for b in blocks:
        ident = block_identity(b)
        ident.pop("content", None)
        out.append(ident)
    return out
