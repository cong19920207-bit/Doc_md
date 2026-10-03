# -*- coding: utf-8 -*-
"""STEP-Q15：Conversation Memory Tool（S01 §19，G-E03/G-E08 M6 部分）。
只在本人当前有效 Conversation 内 search / read；账号、会话、清空边界、本轮快照由服务端绑定，模型不能放宽。
所有候选都回源消息表复核，对不上的残留命中剔除；返回原文与来源，不返回「记忆印象」。"""
from __future__ import annotations

import asyncio
import logging
import re
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from . import settings
from .listing import display_tz
from .memory_index import indexable
from .migrate import MIGRATED_LIMITED

log = logging.getLogger("kb-api.memory_tool")

# G-E03（M6）：每个缺口关键词、向量各召回 20，融合去重后重排，最多交 5 个候选；不设分数阈值
RECALL_EACH = 20
MAX_CANDIDATES = 5
# G-E02（M6）：单次读取最多 3 个回合；单次记忆调用 15 秒
MAX_READ_ROUNDS = 3
CALL_TIMEOUT_SEC = 15.0
# 单条消息返回上限；超出按片段返回并标范围（C38）
MAX_MSG_CHARS = 1500
MAX_QUERY_CHARS = 200

_CN_NUM = {"一": 1, "二": 2, "两": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9, "十": 10}
_TOKEN_RE = re.compile(r"[A-Za-z0-9_]+|[\u4e00-\u9fff]")


@dataclass(frozen=True)
class MemoryScope:
    """服务端绑定的范围：模型只能提查询与来源标识，不能改这里的任何字段。"""

    account_id: str
    conv_id: str
    before_seq: int
    exclude_round_id: str | None
    time_base: str | None


# ---------------- 时间线索（G-E08） ----------------

def _as_utc(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        dt = value
    else:
        text = str(value or "").strip()
        if not text:
            return None
        try:
            dt = datetime.fromisoformat(text.replace("T", " ").replace("Z", "")[:26])
        except ValueError:
            return None
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def local_text(value: Any) -> str:
    dt = _as_utc(value)
    if dt is None:
        return ""
    return dt.replace(tzinfo=timezone.utc).astimezone(display_tz()).strftime("%Y-%m-%d %H:%M")


def _num(text: str) -> int | None:
    if text.isdigit():
        return int(text)
    return _CN_NUM.get(text)


def resolve_time(hint: Any, time_base: Any) -> dict | None:
    """把「昨天」「上周」「2026-09-01」等按显示时区与本轮提问时间换成 UTC 半开区间；认不出返回 None。
    刷新沿用原快照的提问时间（time_base 由服务端给），不按刷新当天重算。"""
    if not isinstance(hint, dict):
        return None
    expr = str(hint.get("expression") or "").strip()
    certainty = "approximate" if hint.get("certainty") == "approximate" else "explicit"
    base = _as_utc(time_base)
    if not expr or base is None:
        return None
    tz = display_tz()
    now = base.replace(tzinfo=timezone.utc).astimezone(tz)
    day0 = now.replace(hour=0, minute=0, second=0, microsecond=0)
    start = end = None
    m = re.search(r"(\d{4})[-/年](\d{1,2})[-/月](\d{1,2})", expr)
    m2 = re.search(r"(\d{1,2})月(\d{1,2})[日号]", expr)
    m3 = re.search(r"(\d+|[一二两三四五六七八九十])天前", expr)
    if m:
        start = day0.replace(year=int(m.group(1)), month=int(m.group(2)), day=int(m.group(3)))
        end = start + timedelta(days=1)
    elif m2:
        start = day0.replace(month=int(m2.group(1)), day=int(m2.group(2)))
        end = start + timedelta(days=1)
    elif m3 and _num(m3.group(1)):
        start = day0 - timedelta(days=_num(m3.group(1)))
        end = start + timedelta(days=1)
    elif "前天" in expr:
        start, end = day0 - timedelta(days=2), day0 - timedelta(days=1)
    elif "昨天" in expr or "昨日" in expr:
        start, end = day0 - timedelta(days=1), day0
    elif "今天" in expr or "今日" in expr:
        start, end = day0, day0 + timedelta(days=1)
    elif "上周" in expr or "上星期" in expr or "上个星期" in expr:
        week0 = day0 - timedelta(days=day0.weekday())
        start, end = week0 - timedelta(days=7), week0
    elif "这周" in expr or "本周" in expr or "这星期" in expr:
        week0 = day0 - timedelta(days=day0.weekday())
        start, end = week0, week0 + timedelta(days=7)
    elif "上个月" in expr or "上月" in expr:
        first = day0.replace(day=1)
        prev_last = first - timedelta(days=1)
        start, end = prev_last.replace(day=1), first
    elif "这个月" in expr or "本月" in expr:
        first = day0.replace(day=1)
        nxt = (first + timedelta(days=32)).replace(day=1)
        start, end = first, nxt
    if start is None or end is None:
        return None

    def to_utc(dt: datetime) -> datetime:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)

    return {
        "expression": expr, "certainty": certainty,
        "start": to_utc(start), "end": to_utc(end),
        "label": f"{start.strftime('%Y-%m-%d %H:%M')}～{end.strftime('%Y-%m-%d %H:%M')}（{settings.DISPLAY_TZ}）",
    }


def relax_window(win: dict) -> dict:
    """模糊时间最多放宽一次：前后各加一个同等长度区间，并记录。"""
    span = win["end"] - win["start"]
    tz = display_tz()
    s, e = win["start"] - span, win["end"] + span

    def loc(dt: datetime) -> str:
        return dt.replace(tzinfo=timezone.utc).astimezone(tz).strftime("%Y-%m-%d %H:%M")

    return dict(win, start=s, end=e, relaxed=True, label=f"{loc(s)}～{loc(e)}（{settings.DISPLAY_TZ}，已放宽）")


def _in_window(row: dict, win: dict | None) -> bool:
    if win is None:
        return True
    if row.get("source") == MIGRATED_LIMITED:
        # 来源受限的迁移消息没有可靠时间，不参与按时间定位
        return False
    dt = _as_utc(row.get("created_at"))
    return dt is not None and win["start"] <= dt < win["end"]


# ---------------- 召回 ----------------

def _tokens(text: str) -> set[str]:
    parts = _TOKEN_RE.findall((text or "").lower())
    out: set[str] = set()
    cjk = [p for p in parts if len(p) == 1 and "\u4e00" <= p <= "\u9fff"]
    for p in parts:
        if not (len(p) == 1 and "\u4e00" <= p <= "\u9fff"):
            out.add(p)
    text_l = (text or "").lower()
    for a, b in zip(text_l, text_l[1:]):
        if "\u4e00" <= a <= "\u9fff" and "\u4e00" <= b <= "\u9fff":
            out.add(a + b)
    if not out:
        out |= set(cjk)
    return out


def keyword_hits(query: str, rows: list[dict], limit: int = RECALL_EACH) -> list[dict]:
    """在消息表原文里按关键词匹配（中文按相邻两字），只在已限定范围的行里找。"""
    q = _tokens(query)
    if not q:
        return []
    scored = []
    for r in rows:
        content = str(r.get("content") or "").lower()
        score = sum(1 for t in q if t in content)
        if score:
            scored.append((score, int(r["seq"]), r))
    scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
    return [dict(r, _kw=s) for s, _, r in scored[:limit]]


def rrf(lists: list[list[str]], k: int = 60) -> list[str]:
    score: dict[str, float] = {}
    for items in lists:
        for rank, key in enumerate(items):
            score[key] = score.get(key, 0.0) + 1.0 / (k + rank + 1)
    return sorted(score, key=lambda x: score[x], reverse=True)


class MemoryTool:
    def __init__(self, msgs: Any, convs: Any, mem_index: Any, embed: Any, rerank: Any) -> None:
        self.msgs = msgs
        self.convs = convs
        self.mem_index = mem_index
        self.embed = embed
        self.rerank = rerank

    # ---------- 范围与回源 ----------

    def _accessible(self, scope: MemoryScope) -> bool:
        return self.convs.get_owned(scope.account_id, scope.conv_id) is not None

    def scope_rows(self, scope: MemoryScope) -> list[dict]:
        """本轮有效历史：清空边界之后、本轮快照之前、不含本回合（C22）。"""
        rows = self.msgs.effective_messages(scope.conv_id)
        return [
            r for r in rows
            if int(r["seq"]) < int(scope.before_seq) and r["round_id"] != scope.exclude_round_id
        ]

    def _rounds(self, rows: list[dict]) -> tuple[dict[str, list[dict]], list[str]]:
        groups: dict[str, list[dict]] = {}
        for r in sorted(rows, key=lambda x: int(x["seq"])):
            groups.setdefault(r["round_id"], []).append(r)
        order = sorted(groups, key=lambda rid: int(groups[rid][0]["round_seq"]))
        return groups, order

    @staticmethod
    def _msg_view(row: dict, hit: dict | None = None) -> dict:
        text = str(row.get("content") or "")
        view = {
            "message_id": row["id"], "role": row["role"], "version_no": row.get("version_no"),
            "is_current": bool(row.get("is_current", 1)), "seq": int(row["seq"]),
            "time": local_text(row.get("created_at")), "time_reliable": row.get("source") != MIGRATED_LIMITED,
            "source": row.get("source") or "live", "total_chars": len(text),
        }
        if len(text) <= MAX_MSG_CHARS:
            return dict(view, text=text, completeness="full", range=[0, len(text)])
        start = 0
        if hit and hit.get("msg_id") == row["id"] and hit.get("char_start") is not None:
            center = (int(hit["char_start"]) + int(hit.get("char_end") or hit["char_start"])) // 2
            start = max(0, min(len(text) - MAX_MSG_CHARS, center - MAX_MSG_CHARS // 2))
        end = start + MAX_MSG_CHARS
        return dict(view, text=text[start:end], completeness="fragment", range=[start, end])

    def _round_view(self, rows: list[dict], hit_msg_id: str | None = None, hit: dict | None = None,
                    win: dict | None = None) -> dict:
        """恢复命中所在完整回合：User + 当前采用版本；命中的是旧版本时给那个版本并标出。"""
        user = next((r for r in rows if r["role"] == "user"), None)
        answers = [r for r in rows if r["role"] == "assistant" and (r.get("completeness") or "complete") == "complete"]
        pick = next((a for a in answers if a["id"] == hit_msg_id), None) or next(
            (a for a in answers if int(a.get("is_current", 1) or 0)), None)
        views = [self._msg_view(m, hit) for m in (user, pick) if m is not None]
        return {
            "round_id": rows[0]["round_id"], "round_seq": int(rows[0]["round_seq"]),
            "exec_id": (pick or {}).get("exec_id"), "messages": views,
            "complete_round": user is not None and pick is not None,
            "in_time_window": None if win is None else all(_in_window(m, win) for m in (user, pick) if m),
        }

    # ---------- search ----------

    async def search(self, scope: MemoryScope, queries: list[dict]) -> dict:
        started = time.monotonic()
        if not self._accessible(scope):
            return {"status": "access_changed", "items": [], "usage": {"search_queries": 0, "reads": 0, "ms": 0}}
        rows = self.scope_rows(scope)
        coverage = self.mem_index.coverage(scope.conv_id, rows)
        items = []
        for q in queries or []:
            try:
                item = await asyncio.wait_for(self._search_one(scope, rows, q), timeout=CALL_TIMEOUT_SEC)
            except asyncio.TimeoutError:
                # C30：超时是服务异常，不当零命中
                item = {"gap_id": (q or {}).get("gap_id"), "status": "timeout", "candidates": []}
            except Exception as exc:  # noqa: BLE001
                log.warning("memory search failed: %s", exc)
                item = {"gap_id": (q or {}).get("gap_id"), "status": "error",
                        "error": getattr(exc, "code", None) or type(exc).__name__, "candidates": []}
            items.append(item)
        statuses = {i["status"] for i in items}
        overall = "ok" if statuses <= {"ok", "empty"} else ("partial" if statuses & {"ok", "empty"} else "error")
        returned = sum(len(m["text"]) for i in items for c in i.get("candidates", []) for m in c["messages"])
        return {
            "status": overall, "items": items, "index_coverage": coverage,
            "usage": {"search_queries": len(items), "reads": 0, "returned_chars": returned,
                      "ms": int((time.monotonic() - started) * 1000)},
        }

    async def _search_one(self, scope: MemoryScope, rows: list[dict], q: dict) -> dict:
        gap_id = str((q or {}).get("gap_id") or "").strip()
        query = str((q or {}).get("query") or "").strip()
        if not gap_id or not query or len(query) > MAX_QUERY_CHARS:
            return {"gap_id": gap_id or None, "status": "invalid", "candidates": []}
        win = None
        if (q or {}).get("time_hint"):
            win = resolve_time(q["time_hint"], scope.time_base)
            if win is None:
                return {"gap_id": gap_id, "status": "time_unresolved", "candidates": [],
                        "applied_scope": {"time": None, "expression": str(q["time_hint"].get("expression") or "")}}
        item = await self._recall(scope, rows, query, win)
        if not item["candidates"] and win is not None and win["certainty"] == "approximate":
            win = relax_window(win)
            item = await self._recall(scope, rows, query, win)
        # C31：明确时间未命中不扩到其他日期
        item.update({
            "gap_id": gap_id,
            "status": "ok" if item["candidates"] else "empty",
            "applied_scope": {
                "conversation_id": scope.conv_id, "before_seq": int(scope.before_seq),
                "time": None if win is None else {"label": win["label"], "certainty": win["certainty"],
                                                  "relaxed": bool(win.get("relaxed"))},
            },
        })
        return item

    async def _recall(self, scope: MemoryScope, rows: list[dict], query: str, win: dict | None) -> dict:
        pool = [r for r in rows if indexable(r) and _in_window(r, win)]
        by_id = {r["id"]: r for r in pool}
        kw = [r["id"] for r in keyword_hits(query, pool)]
        channels = {"keyword": "ok", "vector": "not_connected"}
        vec_ids: list[str] = []
        vec_hits: dict[str, dict] = {}
        if getattr(self.mem_index, "connected", False):
            try:
                vector = (await self.embed([f"用户：{query}"]))[0]
                for h in self.mem_index.vec.search(vector, scope.conv_id, RECALL_EACH * 2):
                    mid = h.get("msg_id")
                    # 残留或越界的命中：不在本轮有效范围内就不用（隐藏、清空、快照之后）
                    if mid in by_id and mid not in vec_hits:
                        vec_hits[mid] = h
                        vec_ids.append(mid)
                    if len(vec_ids) >= RECALL_EACH:
                        break
                channels["vector"] = "ok"
            except Exception as exc:  # noqa: BLE001
                log.warning("memory vector recall failed: %s", exc)
                channels["vector"] = "error"
        fused = rrf([kw, vec_ids])
        ranking = "fused"
        order = fused
        if len(fused) > 1:
            docs = [str(by_id[mid].get("content") or "")[:MAX_MSG_CHARS] for mid in fused]
            try:
                idx = await self.rerank(query, docs, min(MAX_CANDIDATES, len(docs)))
                order = [fused[i] for i in idx if 0 <= i < len(fused)] or fused
                ranking = "reranked"
            except Exception as exc:  # noqa: BLE001
                log.warning("memory rerank failed: %s", exc)
                ranking = "fused_rerank_unavailable"
        groups, _ = self._rounds(rows)
        candidates, seen_rounds, dropped = [], set(), 0
        for mid in order:
            if len(candidates) >= MAX_CANDIDATES:
                break
            fresh = self._recheck(scope, mid)
            if fresh is None:
                dropped += 1
                continue
            if fresh["round_id"] in seen_rounds:
                continue
            seen_rounds.add(fresh["round_id"])
            view = self._round_view(groups.get(fresh["round_id"], [fresh]), mid, vec_hits.get(mid), win)
            view.update({"rank": len(candidates) + 1, "hit_message_id": mid,
                         "matched": [c for c, ids in (("keyword", kw), ("vector", vec_ids)) if mid in ids]})
            candidates.append(view)
        return {"candidates": candidates, "channels": channels, "ranking": ranking, "dropped_stale": dropped}

    def _recheck(self, scope: MemoryScope, msg_id: str) -> dict | None:
        """回源复核：重读消息表并再次确认会话可访问、在清空边界之后、在本轮快照之前。"""
        if not self._accessible(scope):
            return None
        got = self.msgs.get_by_ids(scope.conv_id, [msg_id])
        if not got:
            return None
        row = got[0]
        if int(row["round_seq"]) <= int(self.msgs.clear_seq(scope.conv_id)):
            return None
        if int(row["seq"]) >= int(scope.before_seq) or row["round_id"] == scope.exclude_round_id:
            return None
        return row

    # ---------- STEP-Q20：回看与旧版本 ----------

    def round_views(self, scope: MemoryScope, round_ids: list[str]) -> list[dict]:
        """按回合取原文视图（本轮有效范围内、会话仍可访问）；不在范围的回合不返回。"""
        if not self._accessible(scope):
            return []
        groups, order = self._rounds(self.scope_rows(scope))
        return [self._round_view(groups[r]) for r in order if r in set(round_ids)]

    def versions(self, scope: MemoryScope, round_id: str) -> list[dict]:
        """某回合全部已保存的完整回答版本（旧→新），只读，不改当前采用版本。"""
        if not self._accessible(scope):
            return []
        rows = [r for r in self.scope_rows(scope) if r["round_id"] == round_id]
        answers = [r for r in rows if r["role"] == "assistant" and (r.get("completeness") or "complete") == "complete"]
        answers.sort(key=lambda r: (int(r.get("version_no") or 0), int(r["seq"])))
        return [self._msg_view(a) for a in answers]

    # ---------- read ----------

    async def read(self, scope: MemoryScope, requests: list[dict]) -> dict:
        """已知准确消息或回合标识时直接读，不做语义检索（C14）；可读相邻回合（C15）。
        标识必须属于本会话本轮有效范围，伪造他人或越界的一律拒绝（C28）。"""
        started = time.monotonic()
        if not self._accessible(scope):
            return {"status": "access_changed", "items": [], "usage": {"search_queries": 0, "reads": 0, "ms": 0}}
        rows = self.scope_rows(scope)
        groups, order = self._rounds(rows)
        by_msg = {r["id"]: r for r in rows}
        items = []
        for req in requests or []:
            req = req or {}
            gap_id = str(req.get("gap_id") or "").strip() or None
            mid, rid = str(req.get("message_id") or ""), str(req.get("round_id") or "")
            if mid:
                row = by_msg.get(mid)
                rid = row["round_id"] if row else ""
            if not rid or rid not in groups:
                items.append({"gap_id": gap_id, "status": "rejected", "rounds": []})
                continue
            direction = req.get("direction") or "self"
            count = max(1, min(MAX_READ_ROUNDS, int(req.get("count") or 1)))
            pos = order.index(rid)
            if direction == "next":
                pick = order[pos + 1: pos + 1 + count]
            elif direction == "prev":
                pick = order[max(0, pos - count): pos]
            elif direction == "around":
                pick = order[max(0, pos - 1): pos + 2][:MAX_READ_ROUNDS]
            else:
                pick = [rid]
            win = None
            if isinstance(req.get("time_window"), dict):
                win = resolve_time(req["time_window"], scope.time_base)
            views = [self._round_view(groups[r], mid or None, None, win) for r in pick]
            items.append({
                "gap_id": gap_id, "status": "ok" if views else "empty", "anchor_round_id": rid,
                "direction": direction, "rounds": views,
                "read_options": {
                    "prev_round_id": order[order.index(pick[0]) - 1] if pick and order.index(pick[0]) > 0 else None,
                    "next_round_id": (order[order.index(pick[-1]) + 1]
                                      if pick and order.index(pick[-1]) + 1 < len(order) else None),
                },
            })
        returned = sum(len(m["text"]) for i in items for r in i.get("rounds", []) for m in r["messages"])
        statuses = {i["status"] for i in items}
        return {
            "status": "ok" if statuses <= {"ok", "empty"} else ("partial" if statuses & {"ok", "empty"} else "rejected"),
            "items": items,
            "usage": {"search_queries": 0, "reads": len(items), "returned_chars": returned,
                      "ms": int((time.monotonic() - started) * 1000)},
        }
