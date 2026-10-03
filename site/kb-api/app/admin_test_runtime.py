# -*- coding: utf-8 -*-
"""独立测试运行时。复用生产职责与编排，消息/日志/Memory 均为本次隔离副本。"""
from __future__ import annotations

import json
import math
import time
from copy import deepcopy
from types import SimpleNamespace

from . import settings
from .branches import smalltalk_reply, clarify
from .conv_store import ConvStore, MemoryConvRepo
from .conv_task import restate
from .evidence import EvidenceChecker
from .l1 import assemble_l1, as_history
from .memory_index import MemoryIndex, MemoryRecordRepo
from .memory_tool import MemoryTool, MemoryScope
from .models_ext import ModelError
from .msg_store import MsgStore, MemoryMsgRepo
from .pipeline import Pipeline
from .recall import RecallWorkflow, budget_for
from .router import ConversationRouter
from .tasks import TaskPreparer
from .util import uid


class BoundedModels:
    def __init__(self, actual, budget):
        self.actual, self.budget = actual, budget
        self.calls, self.tokens = 0, 0
        self.rendered = []

    def charge(self, value, call=False):
        if call:
            self.calls += 1
        # 估算值明确标识；不假称供应商实际计费 token。
        self.tokens += max(1, math.ceil(len(json.dumps(value, ensure_ascii=False)) / 2))
        if self.calls > self.budget['calls'] or self.tokens > self.budget['tokens']:
            raise ModelError('test_budget_exceeded', '测试超出有限预算', 400)

    async def rewrite(self, messages, temperature):
        self.charge(messages, True)
        self.rendered.append(deepcopy(messages))
        raw = await self.actual.rewrite(messages, temperature)
        self.charge(raw)
        return raw

    async def embed(self, texts):
        self.charge(texts, True)
        return await self.actual.embed(texts)

    async def rerank(self, query, documents, top_n):
        self.charge([query, documents], True)
        return await self.actual.rerank(query, documents, top_n)

    async def stream_chat(self, messages, temperature):
        self.charge(messages, True)
        self.rendered.append(deepcopy(messages))
        async for part in self.actual.stream_chat(messages, temperature):
            self.charge(part)
            yield part


class TestLogs:
    def __init__(self):
        self.rows = {}

    def insert_running(self, row):
        self.rows[row['round_id']] = deepcopy(row)
        return True

    def update_round(self, rid, fields):
        self.rows[rid].update(deepcopy(fields))
        return True

    def get_round(self, rid):
        return self.rows.get(rid)

    def find_by_request(self, *_):
        return None


class TestDiagnostics:
    def record(self, *_args, **_kwargs):
        return None


class FixtureKnowledge:
    """明确合成材料；检索依赖用固定材料替身，仍调用真实编排/生成/证据检查。"""
    def __init__(self, materials):
        self.blocks = []
        for i, item in enumerate(materials):
            content = str(item.get('content') or '') if isinstance(item, dict) else str(item)
            self.blocks.append({'path': 'test-materials', 'chunk_id': f'fixture-{i + 1}',
                                'feature_id': str(item.get('feature_id') or '') if isinstance(item, dict) else '',
                                'heading': '合成测试材料', 'content': content[:20000], 'collection': 'test',
                                'content_scope': 'full', 'content_hash': '', 'anchor': ''})

    def hybrid_search(self, query, vector, k, collections=None, feature_id=None):
        return [deepcopy(b) for b in self.blocks if not feature_id or b['feature_id'] == feature_id][:k]

    def lookup_payload(self, path, chunk_id):
        return next((deepcopy(b) for b in self.blocks if b['path'] == path and b['chunk_id'] == chunk_id), None)


class IsolatedVectors:
    """仅本次运行的向量副本，不持有生产 collection 或原用户身份。"""
    def __init__(self):
        self.points = {}

    def ensure(self):
        return None

    def upsert(self, points):
        for pid, vector, payload in points:
            self.points[pid] = (list(vector), deepcopy(payload))

    def search(self, vector, conv_id, limit):
        ranked = []
        norm = math.sqrt(sum(x*x for x in vector)) or 1
        for value, payload in self.points.values():
            if payload.get('conv_id') != conv_id:
                continue
            denom = math.sqrt(sum(x*x for x in value)) or 1
            score = sum(a*b for a,b in zip(vector,value))/(norm*denom)
            ranked.append(dict(payload, score=score))
        return sorted(ranked, key=lambda p:p['score'], reverse=True)[:limit]

    def delete_msg(self, msg_id):
        self.points = {k:v for k,v in self.points.items() if v[1].get('msg_id') != msg_id}

    def delete_conv(self, conv_id):
        self.points = {k:v for k,v in self.points.items() if v[1].get('conv_id') != conv_id}


async def execute(row, actual_models, production_store, ask_flow):
    cfg = deepcopy(row['config'])
    models = BoundedModels(actual_models, cfg['test_budget'])
    msgs = MsgStore(MemoryMsgRepo())
    convs = ConvStore(MemoryConvRepo())
    cid = convs.create(row['actor'], {'title': '隔离测试'})['id']
    copied = deepcopy(row['snapshot'].get('messages') or [])
    for message in copied:
        message['conv_id'] = cid
        # 原版本选择保留，未选定的其他版本和历史不会进入测试。
    msgs.repo.insert_many(copied)
    msgs.repo.last_seq[cid] = max([int(m.get('seq') or 0) for m in copied] or [0])
    memory = MemoryIndex(MemoryRecordRepo(), IsolatedVectors(), models.embed, lambda _: row['actor'])
    memory_note = '隔离 Memory 仅使用选定副本'
    if copied and (row['mode'] == 'chain' or row['slot'] == 'recall') and budget_for(cfg, time.monotonic() + cfg['test_budget']['timeout_seconds']).enabled:
        # 有限预算覆盖索引准备的实际 embedding 调用；关键词与向量都只用本次选定消息。
        indexed = await memory.index_rows(copied)
        memory.connected = not indexed.get('failed')
        if indexed.get('failed'):
            memory_note += '；向量副本准备失败，仅关键词通道可用'
    tool = MemoryTool(msgs, convs, memory, models.embed, models.rerank)
    kb = production_store if row.get('real_knowledge') else FixtureKnowledge(row.get('materials') or [])
    pipe = Pipeline(kb, models, lambda: cfg)
    l1 = assemble_l1(copied)
    turns = l1['turns']
    original = row['input']
    checker = EvidenceChecker(models)
    route, result, output, events, error = None, None, '', [], None
    try:
        if row['mode'] == 'chain':
            logs = TestLogs()
            runtime = {'config': cfg, 'convs': convs, 'msgs': msgs, 'logs': logs, 'models': models,
                       'router': ConversationRouter(models), 'task_preparer': TaskPreparer(models),
                       'evidence_checker': checker, 'recall_workflow': RecallWorkflow(models),
                       'pipeline': pipe, 'diag': TestDiagnostics(), 'pending_replies': {}, 'memory_tool': lambda: tool,
                       'time_base': row.get('time_base')}
            if not row.get('real_knowledge'):
                runtime.update(health=lambda: {'qdrant_ready': True, 'index_ready': True}, fail_type=lambda _: None)
            request = SimpleNamespace(state=SimpleNamespace(account={'id': row['actor']}))
            rid = uid('texec')
            run = {}
            async for raw in ask_flow(request, {'query': original, 'conversation_id': cid, 'round_id': rid}, run, runtime):
                lines = raw.decode('utf-8').splitlines()
                event = {'event': lines[0][7:], 'data': json.loads(lines[1][6:])}
                events.append(event)
                if len([e for e in events if e['event'] == 'stage']) > cfg['test_budget']['steps']:
                    raise ModelError('test_budget_exceeded', '测试超出步骤预算', 400)
                if event['event'] == 'done':
                    output = event['data'].get('text') or output
                elif event['event'] == 'token':
                    output += event['data'].get('text') or ''
                elif event['event'] == 'error':
                    error = event['data'].get('type') or 'execution_failed'
            result = logs.get_round(rid) or {}
            route = result.get('route')
            schema_ok = not error
            refused = result.get('biz_result') in ('refused', 'insufficient')
            biz = result.get('biz_result') == 'answered' if result.get('biz_result') else None
        else:
            slot = row['slot']
            if slot == 'router':
                result = await ConversationRouter(models).route(original, turns, cfg)
                route = result['route']
            elif slot == 'task_prep':
                result = await TaskPreparer(models).prepare(original, turns, 'knowledge_query', bool(turns), cfg)
            elif slot == 'rewriter':
                result = await pipe.rewrite(original, as_history(l1), cfg)
            elif slot == 'check':
                from .evidence import evidence_items
                result = await checker.check(original, None, original, '', original, evidence_items(kb.blocks if hasattr(kb, 'blocks') else []), cfg)
            elif slot == 'repair':
                result = await checker.repair(original, None, original, '', original, [], [], cfg)
            elif slot == 'smalltalk':
                result = await smalltalk_reply(models, original, turns, cfg)
            elif slot == 'clarify':
                result = await clarify(models, original, turns, cfg, 'test', row.get('time_base'))
            elif slot == 'restate':
                result = await restate(models, original, [{'content': t['assistant']} for t in turns], cfg)
            elif slot == 'recall':
                budget = budget_for(cfg, time.monotonic() + cfg['test_budget']['timeout_seconds'])
                if not budget.enabled:
                    raise ModelError('recall_budget_missing', '追溯预算未配置', 400)
                scope = MemoryScope(row['actor'], cid, msgs.repo.last_seq[cid] + 1, 'test-target', row.get('time_base'))
                result = await RecallWorkflow(models).run(original, turns, [{'gap_id': 'G1', 'goal': original, 'clue': original, 'depends_on': []}], tool, scope, budget, cfg=cfg)
            output = result if isinstance(result, str) else json.dumps(result, ensure_ascii=False)
            schema_ok, biz, refused = True, None, route == 'out_of_scope'
    except Exception as exc:
        error = getattr(exc, 'code', type(exc).__name__)
        output = getattr(exc, 'raw', '') or ''
        schema_ok, biz, refused = False, None, None
        result = {'error': error, 'detail': str(exc)[:500]}
    return {'output': output, 'result': result, 'events': events, 'rendered': models.rendered,
            'covered_slots': ([row['slot']] if row['mode'] == 'slot' else
                              ['chain', 'router'] + ([{'ack': 'ack_pool', 'out_of_scope': 'scope_pool'}[route]] if not error and route in ('ack', 'out_of_scope') else []) +
                              [({'route': 'router', 'task_prep': 'task_prep', 'rewrite': 'rewriter'}.get(e['data']['stage'], e['data']['stage'])) for e in events if e['event'] == 'stage']),
            'route': route, 'schema_ok': schema_ok, 'biz_resolved': biz, 'refused': refused, 'error': error,
            'usage': {'calls': models.calls, 'estimated_tokens': models.tokens, 'actual_tokens': None},
            'limitations': [memory_note] + ([] if row.get('real_knowledge') else ['Knowledge 检索使用明确标识的合成材料']),
            'knowledge_mode': 'real' if row.get('real_knowledge') else 'synthetic_fixture'}
