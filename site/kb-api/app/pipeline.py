# -*- coding: utf-8 -*-
"""改写 → 分路/单路召回 → 重排 → 流式回答。"""
from __future__ import annotations

import json
import logging
import re
from typing import Any, AsyncIterator, Callable

from . import settings
from .aliases import collection_for, filter_named_ids, format_alias_hint, known_feature_ids
from .models_ext import ModelClients, ModelError
from .store import VectorStore
from .util import excerpt, extract_numbers, NUMBER_LEAK_NOTE, strip_citation_markers

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
                if key == "content" or not out.get(key):
                    out[key] = value
            out["content"] = stored_content
            return out
    excerpt_text = str(out.get("excerpt") or "").strip()
    if excerpt_text:
        out["content"] = excerpt_text
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


def build_rewrite_user(original: str, history_lines: list[str], repo_root=None) -> str:
    """改写用户消息：功能 ID 列表 + 口语对照。最终点名仍经 filter_named_ids。"""
    ids = known_feature_ids(repo_root)
    return (
        f"已有功能 ID：{json.dumps(ids, ensure_ascii=False)}\n"
        f"口语→功能 ID：\n{format_alias_hint(repo_root)}\n"
        f"上一轮摘要：\n" + ("\n".join(history_lines) or "（无）") + "\n"
        f"本轮原句：{original}\n"
        "只输出 JSON。"
    )


class Pipeline:
    def __init__(self, store: VectorStore, models: ModelClients, config_getter: Callable[[], dict]) -> None:
        self.store = store
        self.models = models
        self.config_getter = config_getter

    async def rewrite(self, original: str, history: list[dict], cfg: dict) -> dict:
        hist_lines = []
        for h in history[-int(cfg.get("history_turns") or 0):]:
            hist_lines.append(f"{h.get('role')}: {h.get('text')}")
        user = build_rewrite_user(original, hist_lines)
        messages = [
            {"role": "system", "content": cfg.get("rewrite_prompt") or settings.REWRITE_PROMPT},
            {"role": "user", "content": user},
        ]
        raw = await self.models.rewrite(messages, temperature=float(cfg.get("temperature") or 0))
        return parse_rewrite(raw)

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
            parts.append(
                f"chunk_id={ident['chunk_id']} path={ident['path']} "
                f"feature_id={ident['feature_id']} collection={ident['collection']} "
                f"anchor={ident['anchor']}\n{ident['content']}"
            )
        extra = ""
        if empty_named:
            extra = "以下点名功能本轮无块，必须声明这些功能文档未写：" + ", ".join(empty_named) + "。\n"
        user = (
            f"原句：{original}\n独立问句：{rewrite.get('rewrite_query')}\n"
            f"{extra}本轮生成集：\n" + "\n\n".join(parts)
        )
        return [
            {"role": "system", "content": cfg.get("system_prompt") or settings.SYSTEM_PROMPT},
            {"role": "user", "content": user},
        ]

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
    """数字必须 ⊆ C_gen∪问句；越界保留正文并标记，不再整段替换。"""
    t = text or ""
    if not numbers_ok(t, c_gen, original):
        if t.strip():
            note = NUMBER_LEAK_NOTE
            if note not in t:
                t = t.rstrip() + "\n" + note
            return {"text": t, "refused": True, "conflict": False}
        return {
            "text": "文档未写这些具体数字。请打开出处阅读原文，不要把问答当需求合同。",
            "refused": True,
            "conflict": False,
        }
    if "文档未写" not in t:
        return {"text": t, "refused": False, "conflict": False}
    remainder = remainder_without_unwritten(t)
    # 有生成块且去掉未写声明后仍有主回答：附带一句未写不把整轮标成拒答。
    if c_gen and len(remainder) >= _POSITIVE_ANSWER_MIN:
        return {"text": t, "refused": False, "conflict": False}
    return {"text": t, "refused": True, "conflict": False}


def public_c_gen(blocks: list[dict]) -> list[dict]:
    out = []
    for b in blocks:
        ident = block_identity(b)
        ident.pop("content", None)
        out.append(ident)
    return out
