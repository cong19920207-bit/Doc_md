# -*- coding: utf-8 -*-
"""本机配置分层：只读项不可改，可改项只对后续轮生效。"""
from __future__ import annotations

import json
import os
import tempfile
import threading
from copy import deepcopy
from pathlib import Path
from typing import Any

from . import settings
from .util import uid

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

_WRITABLE_KEYS = (
    "recall_k", "rerank_n", "history_turns", "temperature", "system_prompt", "rewrite_prompt",
)
# 固定规则不能从配置接口改。名称写进拒绝原因，方便对上页面上的只读项。
_FORBIDDEN = {
    "l1_rounds": "L1 完整回合上限",
    "l1_tokens": "L1 token 上限",
    "repair_max": "证据修正机会",
    "cross_session": "历史访问范围",
    "max_conversations": "消息保留",
}
_BUDGET_KEYS = ("calls", "steps", "parallel", "tokens")
_UNCONNECTED = ("故障重试", "分类兜底", "在线更换模型")
FIXED_RULES = (
    {"id": "l1_rounds", "title": "L1 完整回合上限", "value": "最多 10 个完整逻辑回合"},
    {"id": "l1_tokens", "title": "L1 token 上限", "value": "5000 tokens"},
    {"id": "repair_max", "title": "证据修正机会", "value": "本次执行最多 1 次"},
    {"id": "cross_session", "title": "历史访问范围", "value": "本人当前、有效会话"},
)


class ConfigConflict(Exception):
    """修订冲突或没有可发布的草稿。不切换当前生效包。"""

    def __init__(self, message: str = "", diff: dict | None = None) -> None:
        super().__init__(message)
        self.diff = diff or {}


def _defaults() -> dict:
    return {
        "recall_k": settings.DEFAULT_K,
        "rerank_n": settings.DEFAULT_N,
        "history_turns": settings.DEFAULT_HISTORY,
        "temperature": settings.DEFAULT_TEMPERATURE,
        "system_prompt": settings.SYSTEM_PROMPT,
        "rewrite_prompt": settings.REWRITE_PROMPT,
    }


def _blank_extra() -> dict:
    return {"history_recovery": True, "recall_budget": None, "pools": None, "prompts": {},
            "test_budget": {"calls": 16, "steps": 24, "tokens": 24000, "timeout_seconds": 120}}


def _merge_extra(raw: dict | None) -> dict:
    base = _blank_extra()
    if not isinstance(raw, dict):
        return base
    if "history_recovery" in raw:
        base["history_recovery"] = bool(raw.get("history_recovery"))
    if isinstance(raw.get("recall_budget"), dict):
        base["recall_budget"] = dict(raw["recall_budget"])
    if isinstance(raw.get("pools"), dict):
        base["pools"] = raw["pools"]
    if isinstance(raw.get("prompts"), dict):
        base["prompts"] = dict(raw["prompts"])
    if isinstance(raw.get('test_budget'), dict):
        base['test_budget'] = dict(raw['test_budget'])
    return base


def default_pools() -> dict:
    return {
        "ack": [{"id": f"ack-{i}", "text": t, "enabled": True} for i, t in enumerate(settings.ACK_REPLY_POOL, 1)],
        "scope": [{"id": f"scope-{i}", "text": t, "enabled": True} for i, t in enumerate(settings.OUT_OF_SCOPE_REPLY_POOL, 1)],
    }


def resolve_pools(extra: dict | None) -> dict:
    pools = (extra or {}).get("pools") if isinstance(extra, dict) else None
    base = default_pools()
    if not isinstance(pools, dict):
        return base
    out = {}
    for kind in ("ack", "scope"):
        items = pools.get(kind)
        out[kind] = list(items) if isinstance(items, list) else base[kind]
    return out


def enabled_texts(package: dict | None, kind: str) -> list[str]:
    """只取本池已启用的原文。另一个池有句子也不能拿来顶上。"""
    pools = package.get("pools") if isinstance(package, dict) else None
    if not isinstance(pools, dict) or not isinstance(pools.get(kind), list):
        src = settings.ACK_REPLY_POOL if kind == "ack" else settings.OUT_OF_SCOPE_REPLY_POOL
        return [str(x).strip() for x in src if str(x).strip()]
    return [
        str(x.get("text") or "").strip()
        for x in pools[kind]
        if isinstance(x, dict) and x.get("enabled") and str(x.get("text") or "").strip()
    ]


def _clean_pool(items: Any, kind: str) -> list[dict]:
    if not isinstance(items, list):
        raise ValueError(f"{kind} 话术格式不正确")
    out = []
    for i, item in enumerate(items, 1):
        if isinstance(item, str):
            text, enabled, pid = item, True, f"{kind}-{i}"
        elif isinstance(item, dict):
            text = str(item.get("text") or "")
            enabled = bool(item.get("enabled", True))
            pid = str(item.get("id") or f"{kind}-{i}")
        else:
            raise ValueError(f"{kind} 话术格式不正确")
        if "sk-" in text.lower() or "api_key" in text.lower():
            raise ValueError("话术不能包含密钥")
        out.append({"id": pid, "text": text.strip(), "enabled": enabled})
    return out


def _check_body(body: dict) -> None:
    for key, title in _FORBIDDEN.items():
        if key in body:
            raise ValueError(f"固定规则不能修改：{title}")
    budget = body.get("recall_budget")
    for field, limits in (('recall_budget', {'calls': 64, 'steps': 64, 'parallel': 8, 'tokens': 50000}),
                          ('test_budget', {'calls': 64, 'steps': 64, 'tokens': 100000, 'timeout_seconds': 300})):
        if field in body and body[field] is not None:
            if not isinstance(body[field], dict):
                raise ValueError(field + ' 格式不正确')
            for key, value in body[field].items():
                if key not in limits:
                    raise ValueError(field + ' 未登记参数：' + key)
                if field == 'recall_budget' and value in ('', None):
                    continue
                if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= limits[key]:
                    raise ValueError(f'{field}.{key} 必须为 1～{limits[key]} 的整数')
    if isinstance(budget, dict):
        calls, parallel = budget.get("calls"), budget.get("parallel")
        if calls not in (None, "") and parallel not in (None, ""):
            try:
                c_num, p_num = int(calls), int(parallel)
            except (TypeError, ValueError):
                raise ValueError("recall_budget.calls 与 recall_budget.parallel 必须是数字")
            if p_num > c_num:
                raise ValueError("recall_budget.parallel 不能大于 recall_budget.calls")
    if "temperature" in body and body.get("temperature") not in (None, ""):
        try:
            temp = float(body.get("temperature"))
        except (TypeError, ValueError):
            raise ValueError("temperature 不是数字")
        if not 0 <= temp <= 2:
            raise ValueError("temperature 超出已确认范围 0～2")
    if "prompts" in body:
        from .prompts import check_prompts
        err = check_prompts(body.get("prompts") or {})
        if err:
            raise ValueError(err)


def _check_publishable(extra: dict) -> None:
    tests = extra.get('test_budget') or {}
    if any(not isinstance(tests.get(k), int) or isinstance(tests[k], bool) or tests[k] <= 0
           for k in ('calls', 'steps', 'tokens', 'timeout_seconds')):
        raise ValueError('有限测试预算不完整，不能发布')
    recovery = extra.get("history_recovery", True)
    budget = extra.get("recall_budget")
    if recovery and isinstance(budget, dict) and any(budget.get(k) in (None, "", 0) for k in _BUDGET_KEYS):
        raise ValueError("循环预算空白，不能启用循环")
    pools = resolve_pools(extra)
    labels = {"ack": "确认话术池", "scope": "范围话术池"}
    for kind, label in labels.items():
        enabled = [x for x in pools[kind] if isinstance(x, dict) and x.get("enabled") and str(x.get("text") or "").strip()]
        if not enabled:
            raise ValueError(f"{label}没有启用话术，不能发布，也不能改用另一个池")


def _public_extra(extra: dict) -> dict:
    return {
        "history_recovery": extra.get("history_recovery", True),
        "recall_budget": extra.get("recall_budget"),
        "pools": resolve_pools(extra),
        "prompts": dict(extra.get("prompts") or {}),
        "test_budget": deepcopy(extra.get('test_budget')),
    }


class ConfigStore:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or settings.CONFIG_PATH
        self.data = _defaults()
        self.package_id = "pkg-base"
        self.packages: dict[str, dict] = {}
        self.history: list[dict] = []
        self.draft: dict | None = None
        self.draft_rev = 0
        self.extra = _blank_extra()
        self.draft_extra: dict | None = None
        self.publish_ops: dict[str, dict] = {}
        self.last_warnings: list[str] = []
        self.release_gate = None
        self.on_draft_saved = None
        self._lock = threading.RLock()
        self.load()

    def load(self) -> None:
        if not self.path.exists():
            self.packages[self.package_id] = self._package_body()
            return
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            self.packages[self.package_id] = self._package_body()
            return
        for key in _WRITABLE_KEYS:
            if key in raw and raw[key] is not None and raw[key] != "":
                self.data[key] = raw[key]
        self._normalize()
        # 已发布内容按文件保留。不再把旧 Prompt 覆盖成代码里的默认文案。
        self.package_id = str(raw.get("_package_id") or self.package_id)
        stored = raw.get("_packages") if isinstance(raw.get("_packages"), dict) else {}
        self.packages = {str(k): dict(v) for k, v in stored.items() if isinstance(v, dict)}
        self.packages[self.package_id] = self._published_writable()
        self.history = [dict(x) for x in (raw.get("_history") or []) if isinstance(x, dict) and x.get("id")]
        self.publish_ops = deepcopy(raw.get("_publish_ops") or {})
        draft = raw.get("_draft") if isinstance(raw.get("_draft"), dict) else None
        self.draft = dict(draft["data"]) if draft and isinstance(draft.get("data"), dict) else None
        self.draft_rev = int(raw.get('_draft_rev') or (draft or {}).get('rev') or 0)
        stored_extra = raw.get("_extra") if isinstance(raw.get("_extra"), dict) else None
        self.extra = _merge_extra(stored_extra)
        self.draft_extra = _merge_extra(draft.get("extra")) if draft and isinstance(draft.get("extra"), dict) else None
        self.packages[self.package_id] = self._package_body()

    def _published_writable(self) -> dict:
        return {k: self.data[k] for k in _WRITABLE_KEYS}

    def _package_body(self) -> dict:
        body = self._published_writable()
        body.update(_public_extra(self.extra))
        return body

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = self._published_writable()
        payload["_package_id"] = self.package_id
        payload["_packages"] = self.packages
        payload["_history"] = self.history
        payload["_extra"] = self.extra
        payload["_publish_ops"] = self.publish_ops
        payload['_draft_rev'] = self.draft_rev
        if self.draft or self.draft_extra:
            payload["_draft"] = {"rev": self.draft_rev, "data": self.draft, "extra": self.draft_extra}
        else:
            payload["_draft"] = None
        # 先完整落盘，再替换旧文件。中途写失败不破坏最后一个有效配置。
        fd, name = tempfile.mkstemp(prefix=self.path.name + '.', dir=str(self.path.parent))
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as stream:
                json.dump(payload, stream, ensure_ascii=False, indent=2)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(name, self.path)
        finally:
            if os.path.exists(name):
                os.unlink(name)

    def _state(self) -> dict:
        return deepcopy({key: getattr(self, key) for key in (
            'data', 'extra', 'package_id', 'packages', 'history', 'draft',
            'draft_extra', 'draft_rev', 'publish_ops', 'last_warnings',
        )})

    def _restore(self, state: dict) -> None:
        for key, value in state.items():
            setattr(self, key, value)

    def _commit(self, before: dict) -> None:
        try:
            self.save()
        except Exception:
            self._restore(before)
            raise

    def _normalize(self) -> None:
        self.data["recall_k"] = max(1, int(self.data.get("recall_k") or settings.DEFAULT_K))
        self.data["rerank_n"] = max(1, int(self.data.get("rerank_n") or settings.DEFAULT_N))
        self.data["history_turns"] = max(0, int(self.data.get("history_turns") or 0))
        self.data["temperature"] = float(self.data.get("temperature") or 0)
        self.data["system_prompt"] = str(self.data.get("system_prompt") or settings.SYSTEM_PROMPT)
        self.data["rewrite_prompt"] = str(self.data.get("rewrite_prompt") or settings.REWRITE_PROMPT)

    def _apply(self, base: dict, body: dict) -> dict:
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
        data = {k: base.get(k) for k in _WRITABLE_KEYS}
        for src, dest in mapping.items():
            if src in body and body[src] is not None:
                data[dest] = body[src]
        data["recall_k"] = max(1, int(data.get("recall_k") or settings.DEFAULT_K))
        data["rerank_n"] = max(1, int(data.get("rerank_n") or settings.DEFAULT_N))
        data["history_turns"] = max(0, int(data.get("history_turns") or 0))
        data["temperature"] = float(data.get("temperature") or 0)
        data["system_prompt"] = str(data.get("system_prompt") or settings.SYSTEM_PROMPT)
        data["rewrite_prompt"] = str(data.get("rewrite_prompt") or settings.REWRITE_PROMPT)
        return data

    def save_draft(self, body: dict, expected_rev: int | None = None) -> dict:
        """只改草稿。生效中的配置包不变。带了修订号且对不上时拒绝，不覆盖先保存的人。"""
        body = body or {}
        with self._lock:
            if expected_rev is not None:
                current = self.draft_rev
                if int(expected_rev) != int(current):
                    raise ConfigConflict("草稿已被他人保存", {
                        "current_rev": current,
                        "your_rev": int(expected_rev),
                        "draft": deepcopy(self.draft),
                    })
            _check_body(body)
            before = self._state()
            base = self.draft or self._published_writable()
            draft = self._apply(base, body)
            prev = deepcopy(self.draft_extra if self.draft_extra is not None else self.extra)
            if "history_recovery" in body:
                prev["history_recovery"] = bool(body.get("history_recovery"))
            if "recall_budget" in body:
                prev["recall_budget"] = dict(body["recall_budget"]) if isinstance(body.get("recall_budget"), dict) else None
            if 'test_budget' in body:
                prev['test_budget'] = deepcopy(body['test_budget'])
            if "ack_pool" in body or "scope_pool" in body:
                pools = resolve_pools(prev)
                if "ack_pool" in body:
                    pools["ack"] = _clean_pool(body.get("ack_pool"), "ack")
                if "scope_pool" in body:
                    pools["scope"] = _clean_pool(body.get("scope_pool"), "scope")
                prev["pools"] = pools
            if isinstance(body.get("prompts"), dict):
                prompts = dict(prev.get("prompts") or {})
                prompts.update(body["prompts"])
                prev["prompts"] = prompts
            self.draft = draft
            self.draft_extra = prev
            self.draft_rev += 1
            self._commit(before)
            if self.on_draft_saved:
                self.on_draft_saved(self.draft_rev)
            return self.snapshot()

    def update_writable(self, body: dict) -> dict:
        """旧入口改为写草稿，避免保存时直接改正在用的配置。"""
        rev = body.get("rev") if isinstance(body, dict) and "rev" in body else None
        return self.save_draft(body, rev)

    def accept_config(self) -> dict:
        """执行被接受时拷贝当时的生效包。之后发布不影响这一份。"""
        with self._lock:
            body = deepcopy(self.packages.get(self.package_id) or self._package_body())
            body["_package_id"] = self.package_id
            return body

    def test_config(self) -> dict:
        with self._lock:
            body = deepcopy(self.draft or self._published_writable())
            body.update(_public_extra(self.draft_extra if self.draft_extra is not None else self.extra))
            body.update(_package_id=self.package_id, draft_rev=self.draft_rev)
            return body

    @staticmethod
    def _incompatible(data: dict) -> bool:
        if data.get("max_conversations") == 40:
            return True
        if str(data.get("schema") or "") in {"v0", "0"}:
            return True
        return False

    def publish(self, expected_rev: int | None = None, op_id: str | None = None, reason: str = '',
                *, operation: str = 'publish', target: str | None = None) -> dict:
        """原子切换到草稿。同一操作号再点一次不重复切换。修订对不上则拒绝。"""
        with self._lock:
            if op_id and op_id in self.publish_ops:
                done = self.publish_ops[op_id]
                if (done.get('operation', 'publish') != operation or done.get('target') != target
                        or (expected_rev is not None and done.get('source_rev') != int(expected_rev))):
                    raise ConfigConflict('操作号已用于其他发布内容，请重新审阅并使用新操作号')
                return dict(done)
            if not self.draft:
                raise ConfigConflict("没有可发布的草稿")
            if expected_rev is not None and int(expected_rev) != int(self.draft_rev):
                raise ConfigConflict("草稿修订已变化")
            if self._incompatible(self.draft):
                raise ValueError("这份草稿不兼容，不能发布")
            extra = deepcopy(self.draft_extra if self.draft_extra is not None else self.extra)
            _check_publishable(extra)
            warnings: list[str] = []
            if self.release_gate:
                candidate = deepcopy(self.draft)
                candidate.update(_public_extra(extra))
                candidate.update(_package_id=self.package_id, draft_rev=self.draft_rev)
                block, warnings = self.release_gate(self.draft_rev, candidate, self._package_body())
                if block:
                    raise ValueError(block)
                if not reason.strip():
                    raise ValueError('请填写发布说明')
            before = self._state()
            prev_id = self.package_id
            prev_body = deepcopy(self.packages.get(prev_id) or self._package_body())
            new_id = uid("pkg")
            body = deepcopy(self.draft)
            for key in _WRITABLE_KEYS:
                self.data[key] = body.get(key)
            self.extra = extra
            self.packages[new_id] = self._package_body()
            self.package_id = new_id
            self.history.append({"id": prev_id, "data": prev_body, "reason": reason[:500], "next_id": new_id})
            self.draft = None
            self.draft_extra = None
            self.last_warnings = list(warnings or [])
            result = {"package_id": new_id, "previous_id": prev_id, "op_id": op_id, "warnings": self.last_warnings,
                      'source_rev': self.draft_rev, 'operation': operation, 'target': target}
            if op_id:
                self.publish_ops[op_id] = dict(result)
            self._commit(before)
            return result

    def rollback(self, package_id: str, op_id: str | None = None) -> dict:
        """回退是一次新发布。不兼容的历史包直接拒绝，不改当前包。"""
        with self._lock:
            if op_id and op_id in self.publish_ops:
                done = self.publish_ops[op_id]
                if done.get('operation') != 'rollback' or done.get('target') != package_id:
                    raise ConfigConflict('操作号已用于其他发布内容')
                return dict(done)
            found = next((x for x in self.history if x.get("id") == package_id), None)
            data = (found or {}).get("data") or self.packages.get(package_id)
            if not isinstance(data, dict):
                raise KeyError("未找到该版本")
            if self._incompatible(data):
                raise ValueError("该历史版本不兼容，不能回退")
            before = self._state()
            self.draft = self._apply(data, {})
            self.draft_extra = _merge_extra(deepcopy(data))
            self.draft_rev += 1
            rev = self.draft_rev
            try:
                return self.publish(rev, op_id, '回退到 ' + package_id, operation='rollback', target=package_id)
            except Exception:
                self._restore(before)
                raise

    def snapshot(self) -> dict:
        with self._lock:
            return self._snapshot()

    def _snapshot(self) -> dict:
        dash = "已配置" if settings.DASHSCOPE_API_KEY else "未配置"
        deep = "已配置" if settings.DEEPSEEK_API_KEY else "未配置"
        return {
            "writable": self._published_writable(),
            "package_id": self.package_id,
            "draft": deepcopy(self.draft) if self.draft else None,
            "draft_rev": self.draft_rev,
            "published": self._package_body(),
            "history": deepcopy(self.history),
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
            "fixed_rules": [dict(x) for x in FIXED_RULES],
            "pools": resolve_pools(self.draft_extra if self.draft_extra is not None else self.extra),
            "history_recovery": (self.draft_extra if self.draft_extra is not None else self.extra).get("history_recovery", True),
            "recall_budget": (self.draft_extra if self.draft_extra is not None else self.extra).get("recall_budget"),
            "test_budget": deepcopy((self.draft_extra if self.draft_extra is not None else self.extra).get('test_budget')),
            "unconnected": list(_UNCONNECTED),
            "key_note": "密钥只显示已配置或未配置，没有连通性检测，不能当成可用",
            "prompts": self._prompt_view(),
            'published_prompts': self._prompt_view(published=True),
        }

    def _prompt_view(self, published: bool = False) -> list[dict]:
        from .prompts import list_slots
        extra = self.extra if published else self.draft_extra if self.draft_extra is not None else self.extra
        return list_slots((extra or {}).get("prompts"))

    def discard(self, expected_rev: int) -> dict:
        with self._lock:
            if expected_rev != self.draft_rev:
                raise ConfigConflict('草稿修订已变化')
            before = self._state()
            self.draft = self.draft_extra = None
            self.draft_rev += 1
            self._commit(before)
            if self.on_draft_saved:
                self.on_draft_saved(self.draft_rev)
            return self.snapshot()

    def restore_draft(self, package_id: str, expected_rev: int) -> dict:
        data = self.packages.get(package_id)
        if not data:
            raise KeyError('未找到该版本')
        if self._incompatible(data):
            raise ValueError('该历史版本不兼容')
        body = deepcopy(data)
        body['ack_pool'] = body.get('pools', {}).get('ack', [])
        body['scope_pool'] = body.get('pools', {}).get('scope', [])
        body.pop('pools', None)
        return self.save_draft(body, expected_rev)
