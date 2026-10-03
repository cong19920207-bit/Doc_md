# -*- coding: utf-8 -*-
"""STEP-A18（G-E06-6）：旁路诊断事件。只记事件类型、模块、错误码、关联 id、时间，
不含问句、回答、Prompt 与凭据。写 DATA_DIR/diag/events.jsonl（追加、5 MB 轮转、保留 3 份）；
文件写失败时退回进程内最近 500 条，并对外标「观察受限」。"""
from __future__ import annotations

import json
import logging
import threading
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Any

from . import settings
from .util import uid

log = logging.getLogger("kb-api.diag")

MAX_BYTES = 5 * 1024 * 1024
KEEP_FILES = 3
FALLBACK_MAX = 500

# 事件类型 → 所属模块（诊断快照按模块汇总）
EVENT_MODULES: dict[str, str] = {
    "user_save_fail": "messages",
    "assistant_save_fail": "messages",
    "assistant_save_blocked": "messages",
    "retry_save_fail": "messages",
    "runtime_insert_fail": "runtime",
    "runtime_update_fail": "runtime",
    "audit_write_fail": "audit",
    "retrieve_error": "knowledge",
    "model_error": "model",
}
SAVE_KINDS = {
    "user_save_fail": "user",
    "assistant_save_fail": "assistant",
    "assistant_save_blocked": "assistant",
    "retry_save_fail": "assistant",
    "runtime_insert_fail": "runtime",
    "runtime_update_fail": "runtime",
}
ID_KEYS = ("conv_id", "exec_id", "msg_id", "op_id")


def _now_text() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]


class DiagLog:
    def __init__(self, root: Path | None = None) -> None:
        self._root = Path(root) if root else None
        self._lock = threading.Lock()
        self._fallback: deque = deque(maxlen=FALLBACK_MAX)
        self.limited = False
        self.last_write_error: str | None = None

    @property
    def dir(self) -> Path:
        return (self._root or settings.DATA_DIR) / "diag"

    @property
    def path(self) -> Path:
        return self.dir / "events.jsonl"

    def _rotate(self) -> None:
        p = self.path
        if not p.is_file() or p.stat().st_size < MAX_BYTES:
            return
        oldest = self.dir / f"events.jsonl.{KEEP_FILES}"
        if oldest.exists():
            oldest.unlink()
        for i in range(KEEP_FILES - 1, 0, -1):
            src = self.dir / f"events.jsonl.{i}"
            if src.exists():
                src.rename(self.dir / f"events.jsonl.{i + 1}")
        p.rename(self.dir / "events.jsonl.1")

    def _append(self, event: dict) -> bool:
        line = json.dumps(event, ensure_ascii=False) + "\n"
        with self._lock:
            try:
                self.dir.mkdir(parents=True, exist_ok=True)
                self._rotate()
                with self.path.open("a", encoding="utf-8") as fh:
                    fh.write(line)
                self.last_write_error = None
                return True
            except Exception as exc:  # noqa: BLE001
                self.limited = True
                self.last_write_error = str(exc)
                self._fallback.append(event)
                log.warning("diag write failed: %s", exc)
                return False

    def record(self, type_: str, code: str | None = None, **ids: Any) -> dict:
        """在已有失败分支追加一行；本身失败只落进程内，不抛出、不影响原处理。"""
        event = {
            "id": uid("dg"),
            "ts": _now_text(),
            "type": type_,
            "module": EVENT_MODULES.get(type_, "service"),
            "code": (str(code)[:64] if code else None),
        }
        for k in ID_KEYS:
            if ids.get(k):
                event[k] = str(ids[k])[:64]
        self._append(event)
        return event

    def ack(self, event_id: str, actor: dict | None) -> dict:
        """「标记已查看」：追加一条 ack 事件，不改原事件，不解除任何阻塞。"""
        actor = actor or {}
        event = {
            "id": uid("dg"),
            "ts": _now_text(),
            "type": "ack",
            "module": "diag",
            "ref": str(event_id)[:64],
            "actor_id": str(actor.get("id") or "") or None,
            "actor_username": str(actor.get("username") or "") or None,
        }
        event["written"] = self._append(event)
        return event

    def _read_all(self) -> tuple[list[dict], bool]:
        """读文件（含轮转）与进程内备份。第二项表示是否有读不出的部分。"""
        rows: list[dict] = []
        broken = False
        files = [self.dir / f"events.jsonl.{i}" for i in range(KEEP_FILES, 0, -1)] + [self.path]
        for f in files:
            if not f.is_file():
                continue
            try:
                for line in f.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        rows.append(json.loads(line))
                    except ValueError:
                        broken = True
            except Exception:  # noqa: BLE001
                broken = True
        seen = {r.get("id") for r in rows}
        rows.extend(e for e in list(self._fallback) if e.get("id") not in seen)
        return rows, broken

    def events(self) -> tuple[list[dict], bool]:
        """异常事件（不含 ack），每条带已查看信息。"""
        rows, broken = self._read_all()
        acks: dict[str, list[dict]] = {}
        for r in rows:
            if r.get("type") == "ack" and r.get("ref"):
                acks.setdefault(r["ref"], []).append(
                    {"actor_id": r.get("actor_id"), "actor_username": r.get("actor_username"), "ts": r.get("ts")}
                )
        out = []
        for r in rows:
            if r.get("type") == "ack":
                continue
            item = dict(r)
            item["acks"] = acks.get(r.get("id"), [])
            item["acked"] = bool(item["acks"])
            item["save_kind"] = SAVE_KINDS.get(r.get("type"))
            out.append(item)
        return out, broken

    def state(self) -> dict:
        return {
            "limited": bool(self.limited),
            "last_write_error": self.last_write_error,
            "fallback_count": len(self._fallback),
        }
