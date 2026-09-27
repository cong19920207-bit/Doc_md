# -*- coding: utf-8 -*-
"""简易中英 BM25，用于与向量结果做 RRF 混合召回。"""
from __future__ import annotations

import math
import re
from collections import defaultdict
from typing import Callable

WORD_RE = re.compile(r"[A-Za-z0-9_\-]+|[\u4e00-\u9fff]")


def tokenize(text: str) -> list[str]:
    raw = (text or "").lower()
    toks: list[str] = []
    buf: list[str] = []
    for m in WORD_RE.finditer(raw):
        t = m.group(0)
        if re.fullmatch(r"[\u4e00-\u9fff]", t):
            buf.append(t)
        else:
            if buf:
                toks.extend(_cjk_grams(buf))
                buf = []
            toks.append(t)
    if buf:
        toks.extend(_cjk_grams(buf))
    return toks


def _cjk_grams(chars: list[str]) -> list[str]:
    grams = list(chars)
    for i in range(len(chars) - 1):
        grams.append(chars[i] + chars[i + 1])
    return grams


class Bm25Index:
    def __init__(self, k1: float = 1.5, b: float = 0.75) -> None:
        self.k1 = k1
        self.b = b
        self.docs: dict[str, dict] = {}
        self.df: dict[str, int] = defaultdict(int)
        self.avgdl = 0.0

    def clear(self) -> None:
        self.docs.clear()
        self.df = defaultdict(int)
        self.avgdl = 0.0

    def add(self, key: str, text: str, meta: dict) -> None:
        if key in self.docs:
            self.remove(key)
        tf: dict[str, int] = defaultdict(int)
        toks = tokenize(text)
        for t in toks:
            tf[t] += 1
        self.docs[key] = {"tf": dict(tf), "dl": max(1, len(toks)), "meta": meta, "text": text}
        for t in tf:
            self.df[t] += 1
        self._refresh_avg()

    def remove(self, key: str) -> None:
        old = self.docs.pop(key, None)
        if not old:
            return
        for t in old["tf"]:
            self.df[t] -= 1
            if self.df[t] <= 0:
                self.df.pop(t, None)
        self._refresh_avg()

    def _refresh_avg(self) -> None:
        if not self.docs:
            self.avgdl = 0.0
            return
        self.avgdl = sum(d["dl"] for d in self.docs.values()) / len(self.docs)

    def search(self, query: str, k: int, accept: Callable[[dict], bool] | None = None) -> list[tuple[str, float, dict]]:
        q_toks = tokenize(query)
        if not q_toks or not self.docs:
            return []
        n = len(self.docs)
        scores: dict[str, float] = {}
        for key, doc in self.docs.items():
            if accept and not accept(doc["meta"]):
                continue
            score = 0.0
            dl = doc["dl"]
            for t in q_toks:
                tf = doc["tf"].get(t)
                if not tf:
                    continue
                df = self.df.get(t, 0)
                idf = math.log(1 + (n - df + 0.5) / (df + 0.5))
                denom = tf + self.k1 * (1 - self.b + self.b * dl / max(self.avgdl, 1.0))
                score += idf * (tf * (self.k1 + 1)) / denom
            if score > 0:
                scores[key] = score
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:k]
        return [(key, score, self.docs[key]["meta"]) for key, score in ranked]


def rrf_merge(lists: list[list[str]], k: int, k_rrf: int = 60) -> list[str]:
    scores: dict[str, float] = {}
    for items in lists:
        for rank, key in enumerate(items, start=1):
            scores[key] = scores.get(key, 0.0) + 1.0 / (k_rrf + rank)
    return [key for key, _ in sorted(scores.items(), key=lambda x: x[1], reverse=True)[:k]]
