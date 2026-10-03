# -*- coding: utf-8 -*-
"""独立测试记录：服务端执行、精确配置绑定、可撤销来源和发布断言。"""
from __future__ import annotations

import asyncio
import hashlib
import json
import os
import tempfile
import time
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Callable

from . import settings
from .util import uid


def fingerprint(value) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, default=str).encode()).hexdigest()


class TestError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class TestBook:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or settings.DATA_DIR / 'tests' / 'book.json'
        self.runs: dict[str, dict] = {}
        self.cases: dict[str, dict] = {}
        self._sources: Callable | None = None
        self._executor = None
        self._tasks = set()
        self._load()

    def _load(self):
        if not self.path.exists():
            return
        # 损坏的门禁记录不能默默退化为空记录后允许发布。
        raw = json.loads(self.path.read_text(encoding='utf-8'))
        self.runs = raw.get('runs') or {}
        self.cases = raw.get('cases') or {}
        for row in self.runs.values():
            if row.get('status') in ('queued', 'running'):
                row.update(status='interrupted', passed=False, error='服务重启，测试未完成')

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, name = tempfile.mkstemp(prefix='book.', dir=str(self.path.parent))
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as stream:
                json.dump({'runs': self.runs, 'cases': self.cases}, stream, ensure_ascii=False, default=str)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(name, self.path)
        finally:
            if os.path.exists(name):
                os.unlink(name)

    def bind_sources(self, fn):
        self._sources = fn

    def bind_executor(self, fn):
        self._executor = fn

    def add_case(self, body: dict) -> dict:
        cid = str(body.get('id') or uid('case'))
        if cid in self.cases:
            raise TestError('用例编号已存在，请建立新版本，不能覆盖发布断言')
        assertion = body.get('assertions')
        if not isinstance(assertion, dict) or not assertion or any(k not in ('route', 'refused', 'schema_ok', 'contains', 'error') for k in assertion):
            raise TestError('需要预期 Route、拒绝、结构或必要文本断言')
        if any(not isinstance(assertion[k], bool) for k in ('refused', 'schema_ok') if k in assertion):
            raise TestError('拒绝与结构断言必须为布尔值')
        text = str(body.get('input') or '').strip()
        if not text:
            raise TestError('用例需要输入正文')
        row = {'id': cid, 'title': str(body.get('title') or cid)[:80], 'critical': bool(body.get('critical')),
               'input': text[:12000], 'slot': str(body.get('slot') or 'router'),
               'mode': str(body.get('mode') or 'slot'), 'assertions': deepcopy(assertion),
               'version': fingerprint([text, assertion, body.get('slot'), body.get('mode')])}
        self.cases[cid] = row
        try:
            self.save()
        except Exception:
            self.cases.pop(cid, None)
            raise
        return deepcopy(row)

    def start(self, body: dict, actor: str, cfg: dict) -> dict:
        if not self._executor:
            raise TestError('测试执行器未接入，测试未开始')
        rev = int(cfg.get('draft_rev') or 0)
        if 'rev' in body and int(body['rev']) != rev:
            raise TestError('草稿修订已变化，请重新查看后测试')
        case_id = str(body.get('case_id') or '')
        case = self.cases.get(case_id)
        if case_id and not case:
            raise TestError('未找到测试用例')
        mode = str((case or {}).get('mode') or body.get('mode') or 'slot')
        slot = str((case or {}).get('slot') or body.get('slot') or 'router')
        from .prompts import slot_map
        if mode not in ('slot', 'chain') or (mode == 'slot' and not (slot_map().get(slot) or {}).get('connected')):
            raise TestError('测试模式或职责槽位未接入')
        snap = {'messages': [], 'hash': fingerprint([]), 'source_type': 'synthetic'}
        source = str(body.get('conv_id') or '')
        if source:
            selected = body.get('message_ids')
            if not isinstance(selected, list) or not selected:
                raise TestError('必须明确选择目标消息及必要上下文，不能自动带入整段会话')
            snap = self._copy_source(source, selected)
        text = str((case or {}).get('input') or body.get('input') or '').strip()
        if not text:
            raise TestError('需要测试输入正文')
        budget = cfg.get('test_budget')
        if not isinstance(budget, dict) or any(not isinstance(budget.get(k), int) or isinstance(budget[k], bool) or budget[k] <= 0 for k in ('calls', 'steps', 'tokens', 'timeout_seconds')):
            raise TestError('有限测试预算未配置，测试未开始')
        if body.get('needs_recall') and not _budget_ready(cfg):
            raise TestError('追溯预算未配置，测试未开始')
        row = {'id': uid('trun'), 'status': 'queued', 'actor': actor, 'source_conv': source, 'source_exec': str(body.get('exec_id') or ''),
               'imported': bool(source), 'snapshot': snap, 'input': text[:12000],
               'mode': mode, 'slot': slot, 'config': deepcopy(cfg), 'config_hash': fingerprint(cfg),
               'against_rev': rev, 'case_id': case_id, 'case_version': (case or {}).get('version'),
               'assertions': deepcopy((case or {}).get('assertions') or {}), 'passed': False,
               'schema_ok': None, 'biz_resolved': None, 'refused': None, 'stale': False,
               'simulated': bool(body.get('simulate_tool')), 'tool': {'simulated': True, 'label': '操作者标记为模拟依赖测试'} if body.get('simulate_tool') else None,
               'materials': deepcopy(body.get('materials') or []), 'real_knowledge': bool(body.get('real_knowledge')),
               'created_at': datetime.utcnow().isoformat(), 'note': '', 'production_write': False}
        row['time_base'] = next((m.get('created_at') for m in reversed(snap['messages']) if m.get('role') == 'user'), row['created_at'])
        if not isinstance(row['materials'], list) or len(row['materials']) > 20:
            raise TestError('模拟知识材料最多 20 段')
        self.runs[row['id']] = row
        try:
            self.save()
        except Exception:
            self.runs.pop(row['id'], None)
            raise
        task = asyncio.create_task(self._run(row))
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)
        return self._public(row)

    async def _run(self, row):
        started = time.monotonic()
        row['status'] = 'running'
        try:
            result = await asyncio.wait_for(self._executor(deepcopy(row)), row['config']['test_budget']['timeout_seconds'])
            row.update(result)
            row['status'] = 'done' if not result.get('error') else 'failed'
            assertion = row['assertions']
            checks = {k: ((v in str(row.get('output') or '')) if k == 'contains' else row.get(k) == v) for k, v in assertion.items()}
            row['assertion_results'] = checks
            row['passed'] = bool(checks) and all(checks.values()) and (row['status'] == 'done' or 'error' in assertion) and not row.get('simulated')
        except asyncio.TimeoutError:
            row.update(status='failed', error='测试超出总截止', passed=False)
        except Exception as exc:
            row.update(status='failed', error=str(exc)[:500], passed=False)
        row['elapsed_ms'] = int((time.monotonic() - started) * 1000)
        row['finished_at'] = datetime.utcnow().isoformat()
        self._revoke(row)
        try:
            self.save()
        except Exception:
            # 不得将未持久保存的运行用作发布证据。
            row.update(status='failed', passed=False, error='测试结果写入失败')

    def get(self, run_id):
        row = self.runs.get(run_id)
        return self._public(row) if row else None

    def compare(self, left, right):
        a, b = self.get(left), self.get(right)
        if not a or not b:
            raise TestError('未找到测试')
        same = fingerprint([a.get('input'), a['snapshot'].get('hash')]) == fingerprint([b.get('input'), b['snapshot'].get('hash')])
        return {'same_source': same, 'difference': [] if same else ['来源内容已变化'],
                'same_input': a.get('input') == b.get('input'), 'same_time_base': a.get('time_base') == b.get('time_base'), 'left': a, 'right': b,
                'output_changed': a.get('output') != b.get('output')}

    def mark_stale(self, current_rev):
        for row in self.runs.values():
            if row['against_rev'] != current_rev:
                row.update(stale=True, note='针对旧修订')
        self.save()

    def invalidate(self, conv_id):
        for row in self.runs.values():
            if row.get('source_conv') == conv_id:
                self._redact(row, '来源已删除')
        self.save()

    def gate(self, rev, package=None, previous=None):
        critical = [c for c in self.cases.values() if c.get('critical')]
        if not critical:
            return '关键用例尚未配置，不能发布', []
        valid = [r for r in self.runs.values() if r.get('case_id') in {c['id'] for c in critical}
                 and r.get('passed') and not r.get('stale') and r.get('against_rev') == rev
                 and (package is None or r.get('config_hash') == fingerprint(package)) and not self._revoke(r)]
        if package is not None and previous is not None:
            from .prompts import list_slots
            old = {r['id']: r['text'] for r in list_slots(previous.get('prompts')) if r['connected']}
            new = {r['id']: r['text'] for r in list_slots(package.get('prompts')) if r['connected']}
            required = {k for k in new if new[k] != old[k]}
            for key, slot in (('system_prompt', 'generate'), ('recall_k', 'retrieve'), ('rerank_n', 'rerank'),
                              ('history_recovery', 'recall'), ('recall_budget', 'recall')):
                if package.get(key) != previous.get(key):
                    # 停用追溯也是可观察的链路行为，不能强迫停用后再调用追溯。
                    required.add('chain' if key in ('history_recovery', 'recall_budget') and package.get('history_recovery') is False else slot)
            for pool in ('ack', 'scope'):
                if (package.get('pools') or {}).get(pool) != (previous.get('pools') or {}).get(pool):
                    required.add(pool + '_pool')
            covered = {slot for row in valid for slot in row.get('covered_slots', [])}
            if not required.issubset(covered):
                return '关键用例未覆盖受影响职责：' + '、'.join(sorted(required - covered)), []
        warnings = []
        for case in self.cases.values():
            hit = any(r.get('case_id') == case['id'] and r.get('case_version') == case['version']
                      and not r.get('stale') and r.get('against_rev') == rev and r.get('passed')
                      and (r.get('status') == 'done' or 'error' in r.get('assertions', {}))
                      and (package is None or r.get('config_hash') == fingerprint(package))
                      and not self._revoke(r) for r in self.runs.values())
            if case['critical'] and not hit:
                return f"关键用例 {case['title']} 尚未在修订 {rev} 通过", []
            if not case['critical'] and not hit:
                warnings.append('非关键项未覆盖：' + case['title'])
        return None, warnings

    def _copy_source(self, conv_id, selected):
        live = self._sources(conv_id) if self._sources else None
        if not live:
            raise TestError('来源不可用')
        messages = [json.loads(json.dumps(m, default=str)) for m in live.get('messages') or [] if m['id'] in selected]
        if {m['id'] for m in messages} != set(selected):
            raise TestError('选定消息已不可用')
        return {'messages': messages, 'hash': fingerprint(messages), 'owner': live.get('owner'),
                'hidden_at': live.get('hidden_at'), 'clear_seq': live.get('clear_seq', 0), 'source_type': 'controlled_snapshot'}

    def _redact(self, row, note):
        row.update(snapshot={'messages': [], 'hash': '', 'void': note}, input='', materials=[],
                   output='', error=None, events=[], rendered=[], result={}, note=note, passed=False, assertions={})
        # 配置不含来源原文，可保留精确修订；所有测试输入/输出副本都被撤销。

    def _revoke(self, row):
        if not row.get('source_conv') or not self._sources:
            return False
        snap = row['snapshot']
        if snap.get('void'):
            return True
        live = self._sources(row['source_conv'])
        note = None
        if not live:
            note = '来源已不可用'
        elif live.get('hidden_at') != snap.get('hidden_at'):
            note = '来源已隐藏'
        elif live.get('clear_seq', 0) != snap.get('clear_seq', 0):
            note = '来源已清空'
        if note:
            self._redact(row, note)
            return True
        return False

    def _public(self, row):
        if self._revoke(row):
            self.save()
        return deepcopy(row)


def _budget_ready(cfg):
    budget = cfg.get('recall_budget') or {}
    return cfg.get('history_recovery') is not False and all(isinstance(budget.get(k), int) and budget[k] > 0 for k in ('calls', 'steps', 'parallel', 'tokens'))
