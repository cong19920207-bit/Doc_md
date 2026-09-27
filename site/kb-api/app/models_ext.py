# -*- coding: utf-8 -*-
"""DashScope embedding / 重排，DeepSeek 改写与流式回答。Key 为空时不打外网。"""
from __future__ import annotations

import json
import logging
from typing import Any, AsyncIterator

import httpx

from . import settings

log = logging.getLogger("kb-api.models")


class ModelError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 502) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


def key_status() -> dict[str, str]:
    return {
        "dashscope": "已配置" if settings.DASHSCOPE_API_KEY else "未配置",
        "deepseek": "已配置" if settings.DEEPSEEK_API_KEY else "未配置",
    }


def missing_keys() -> list[str]:
    missing = []
    if not settings.DASHSCOPE_API_KEY:
        missing.append("DASHSCOPE_API_KEY")
    if not settings.DEEPSEEK_API_KEY:
        missing.append("DEEPSEEK_API_KEY")
    return missing


class ModelClients:
    def __init__(self) -> None:
        self.timeout = httpx.Timeout(60.0, connect=10.0)

    async def embed(self, texts: list[str]) -> list[list[float]]:
        if not settings.DASHSCOPE_API_KEY:
            raise ModelError("missing_key", "缺 Key：未配置 DASHSCOPE_API_KEY", 400)
        url = f"{settings.DASHSCOPE_BASE}/compatible-mode/v1/embeddings"
        headers = {
            "Authorization": f"Bearer {settings.DASHSCOPE_API_KEY}",
            "Content-Type": "application/json",
        }
        vectors: list[list[float]] = []
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for i in range(0, len(texts), 8):
                batch = texts[i:i + 8]
                payload = {
                    "model": settings.EMBED_MODEL,
                    "input": batch,
                    "dimensions": settings.EMBED_DIM,
                }
                try:
                    resp = await client.post(url, headers=headers, json=payload)
                except httpx.HTTPError as exc:
                    raise ModelError("embed_fail", f"embedding 请求失败：{exc}", 502) from exc
                if resp.status_code >= 500:
                    raise ModelError("embed_fail", f"embedding {resp.status_code}", 502)
                if resp.status_code >= 400:
                    raise ModelError("embed_fail", f"embedding {resp.status_code}: {resp.text[:200]}", resp.status_code)
                data = resp.json()
                items = sorted(data.get("data") or [], key=lambda x: x.get("index", 0))
                if len(items) != len(batch):
                    raise ModelError("embed_fail", "embedding 返回条数不匹配", 502)
                for item in items:
                    vec = item.get("embedding") or []
                    if len(vec) != settings.EMBED_DIM:
                        raise ModelError("embed_fail", "embedding 维度不是 1024", 502)
                    vectors.append(vec)
        return vectors

    async def rerank(self, query: str, documents: list[str], top_n: int) -> list[int]:
        if not settings.DASHSCOPE_API_KEY:
            raise ModelError("missing_key", "缺 Key：未配置 DASHSCOPE_API_KEY", 400)
        if not documents:
            return []
        url = f"{settings.DASHSCOPE_BASE}/api/v1/services/rerank/text-rerank/text-rerank"
        headers = {
            "Authorization": f"Bearer {settings.DASHSCOPE_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": settings.RERANK_MODEL,
            "input": {"query": query, "documents": documents},
            "parameters": {"top_n": min(top_n, len(documents)), "return_documents": False},
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                resp = await client.post(url, headers=headers, json=payload)
            except httpx.HTTPError as exc:
                raise ModelError("rerank_fail", f"重排请求失败：{exc}", 502) from exc
        if resp.status_code >= 500:
            raise ModelError("rerank_fail", f"重排 {resp.status_code}", 502)
        if resp.status_code >= 400:
            raise ModelError("rerank_fail", f"重排 {resp.status_code}: {resp.text[:200]}", resp.status_code)
        body = resp.json()
        results = (
            (body.get("output") or {}).get("results")
            or body.get("results")
            or []
        )
        order: list[int] = []
        for row in results:
            idx = row.get("index")
            if isinstance(idx, int) and 0 <= idx < len(documents):
                order.append(idx)
        if not order:
            raise ModelError("rerank_fail", "重排未返回有效 index", 502)
        return order

    async def rewrite(self, messages: list[dict], temperature: float) -> str:
        if not settings.DEEPSEEK_API_KEY:
            raise ModelError("missing_key", "缺 Key：未配置 DEEPSEEK_API_KEY", 400)
        return await self._chat(messages, temperature=temperature, stream=False)

    async def stream_chat(self, messages: list[dict], temperature: float) -> AsyncIterator[str]:
        if not settings.DEEPSEEK_API_KEY:
            raise ModelError("missing_key", "缺 Key：未配置 DEEPSEEK_API_KEY", 400)
        async for part in self._stream(messages, temperature):
            yield part

    async def _chat(self, messages: list[dict], temperature: float, stream: bool) -> str:
        url = f"{settings.DEEPSEEK_BASE}/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}",
            "Content-Type": "application/json",
        }
        payload: dict[str, Any] = {
            "model": settings.LLM_MODEL,
            "messages": messages,
            "temperature": temperature,
            "stream": False,
            "thinking": {"type": "disabled"},
        }
        async with httpx.AsyncClient(timeout=httpx.Timeout(90.0, connect=10.0)) as client:
            try:
                resp = await client.post(url, headers=headers, json=payload)
            except httpx.HTTPError as exc:
                raise ModelError("llm_fail", f"模型请求失败：{exc}", 502) from exc
        if resp.status_code >= 400:
            # 部分网关不认 thinking 字段，去掉再试一次
            if resp.status_code == 400 and "thinking" in payload:
                payload.pop("thinking", None)
                async with httpx.AsyncClient(timeout=httpx.Timeout(90.0, connect=10.0)) as client:
                    resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code >= 500:
                raise ModelError("llm_fail", f"模型 {resp.status_code}", 502)
            if resp.status_code >= 400:
                raise ModelError("llm_fail", f"模型 {resp.status_code}: {resp.text[:200]}", resp.status_code)
        data = resp.json()
        try:
            return data["choices"][0]["message"]["content"] or ""
        except (KeyError, IndexError, TypeError) as exc:
            raise ModelError("llm_fail", "模型返回无法解析", 502) from exc

    async def _stream(self, messages: list[dict], temperature: float) -> AsyncIterator[str]:
        url = f"{settings.DEEPSEEK_BASE}/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}",
            "Content-Type": "application/json",
        }
        payload: dict[str, Any] = {
            "model": settings.LLM_MODEL,
            "messages": messages,
            "temperature": temperature,
            "stream": True,
            "thinking": {"type": "disabled"},
        }
        async with httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=10.0)) as client:
            try:
                async with client.stream("POST", url, headers=headers, json=payload) as resp:
                    if resp.status_code == 400:
                        await resp.aread()
                        payload.pop("thinking", None)
                    elif resp.status_code >= 500:
                        raise ModelError("gen_fail", f"生成 {resp.status_code}", 502)
                    elif resp.status_code >= 400:
                        text = (await resp.aread()).decode("utf-8", "ignore")
                        raise ModelError("gen_fail", f"生成 {resp.status_code}: {text[:200]}", resp.status_code)
                    if resp.status_code == 400:
                        async with client.stream("POST", url, headers=headers, json=payload) as resp2:
                            if resp2.status_code >= 500:
                                raise ModelError("gen_fail", f"生成 {resp2.status_code}", 502)
                            if resp2.status_code >= 400:
                                text = (await resp2.aread()).decode("utf-8", "ignore")
                                raise ModelError("gen_fail", f"生成 {resp2.status_code}: {text[:200]}", resp2.status_code)
                            async for piece in self._iter_sse(resp2):
                                yield piece
                        return
                    async for piece in self._iter_sse(resp):
                        yield piece
            except ModelError:
                raise
            except httpx.HTTPError as exc:
                raise ModelError("gen_fail", f"生成请求失败：{exc}", 502) from exc

    async def _iter_sse(self, resp: httpx.Response) -> AsyncIterator[str]:
        async for line in resp.aiter_lines():
            if not line:
                continue
            if line.startswith("data:"):
                data = line[5:].strip()
                if data == "[DONE]":
                    break
                try:
                    obj = json.loads(data)
                    delta = (((obj.get("choices") or [{}])[0]).get("delta") or {}).get("content") or ""
                    if delta:
                        yield delta
                except json.JSONDecodeError:
                    continue
