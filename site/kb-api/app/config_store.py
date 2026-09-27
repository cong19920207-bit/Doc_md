# -*- coding: utf-8 -*-
"""本机配置分层：只读项不可改，可改项只对后续轮生效。"""
from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

from . import settings

READONLY_FIELDS = [
    "embedding 型号",
    "embedding 维度",
    "重排型号",
    "改写/回答型号",
    "thinking=关闭",
    "Key 状态",
    "collection 名称",
    "切块口径",
]

WRITABLE_FIELDS = [
    "召回 K",
    "重排 n",
    "历史轮数",
    "temperature",
    "系统 Prompt",
    "改写 Prompt",
]

CHUNK_POLICY = "仅 chunk:default；默认两库都搜；点名多功能时另走分路，不是用户勾选过滤"


def _defaults() -> dict:
    return {
        "recall_k": settings.DEFAULT_K,
        "rerank_n": settings.DEFAULT_N,
        "history_turns": settings.DEFAULT_HISTORY,
        "temperature": settings.DEFAULT_TEMPERATURE,
        "system_prompt": settings.SYSTEM_PROMPT,
        "rewrite_prompt": settings.REWRITE_PROMPT,
    }


class ConfigStore:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or settings.CONFIG_PATH
        self.data = _defaults()
        self.load()

    def load(self) -> None:
        if not self.path.exists():
            return
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return
        writable_keys = {
            "recall_k",
            "rerank_n",
            "history_turns",
            "temperature",
            "system_prompt",
            "rewrite_prompt",
        }
        for key in writable_keys:
            if key in raw and raw[key] is not None and raw[key] != "":
                self.data[key] = raw[key]
        self._normalize()
        # 未手工改过的旧默认 Prompt 迁到现行文案，避免配置卷卡住拒答口径。
        changed = False
        if self.data.get("system_prompt") in settings.LEGACY_SYSTEM_PROMPTS:
            self.data["system_prompt"] = settings.SYSTEM_PROMPT
            changed = True
        if self.data.get("rewrite_prompt") in settings.LEGACY_REWRITE_PROMPTS:
            self.data["rewrite_prompt"] = settings.REWRITE_PROMPT
            changed = True
        if changed:
            self.save()

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {k: self.data[k] for k in (
            "recall_k", "rerank_n", "history_turns", "temperature",
            "system_prompt", "rewrite_prompt",
        )}
        self.path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def _normalize(self) -> None:
        self.data["recall_k"] = max(1, int(self.data.get("recall_k") or settings.DEFAULT_K))
        self.data["rerank_n"] = max(1, int(self.data.get("rerank_n") or settings.DEFAULT_N))
        self.data["history_turns"] = max(0, int(self.data.get("history_turns") or 0))
        self.data["temperature"] = float(self.data.get("temperature") or 0)
        self.data["system_prompt"] = str(self.data.get("system_prompt") or settings.SYSTEM_PROMPT)
        self.data["rewrite_prompt"] = str(self.data.get("rewrite_prompt") or settings.REWRITE_PROMPT)

    def update_writable(self, body: dict) -> dict:
        mapping = {
            "召回 K": "recall_k",
            "重排 n": "rerank_n",
            "历史轮数": "history_turns",
            "temperature": "temperature",
            "系统 Prompt": "system_prompt",
            "改写 Prompt": "rewrite_prompt",
            "recall_k": "recall_k",
            "rerank_n": "rerank_n",
            "history_turns": "history_turns",
            "system_prompt": "system_prompt",
            "rewrite_prompt": "rewrite_prompt",
        }
        for src, dest in mapping.items():
            if src in body and body[src] is not None:
                self.data[dest] = body[src]
        self._normalize()
        self.save()
        return self.snapshot()

    def snapshot(self) -> dict:
        dash = "已配置" if settings.DASHSCOPE_API_KEY else "未配置"
        deep = "已配置" if settings.DEEPSEEK_API_KEY else "未配置"
        return {
            "writable": deepcopy(self.data),
            "readonly": {
                "embedding 型号": settings.EMBED_MODEL,
                "embedding 维度": settings.EMBED_DIM,
                "重排型号": settings.RERANK_MODEL,
                "改写/回答型号": settings.LLM_MODEL,
                "thinking=关闭": settings.THINKING,
                "Key 状态": {"DashScope": dash, "DeepSeek": deep},
                "collection 名称": [settings.COLLECTION_CLIENT, settings.COLLECTION_ADMIN],
                "切块口径": CHUNK_POLICY,
            },
            "readonly_fields": READONLY_FIELDS,
            "writable_fields": WRITABLE_FIELDS,
        }
