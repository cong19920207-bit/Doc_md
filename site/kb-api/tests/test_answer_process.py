"""User-visible process: real events, versioned history, failures and access boundaries."""
import json

from test_m5_orchestration import (
    env, _ask, _last, _new_conv, _refresh, _router_json,
)
from app import main
from app.models_ext import ModelError
from app.answer_process import AnswerProcess


def test_excluded_task_names_follow_the_task_preparation_contract():
    process = AnswerProcess('example')
    process.observe('stage', {'stage': 'task_prep'})
    process.observe('process', {'kind': 'tasks', 'tasks': [], 'excluded': [
        {'text': '帮我写代码', 'reason': '超出知识库范围'},
    ]})
    assert process.snapshot()['steps'][0]['details'] == ['未执行：帮我写代码；超出知识库范围']


def test_process_is_detailed_persisted_and_does_not_add_model_calls(env):
    c = env['client']
    conv = _new_conv(c)
    events = _ask(c, conv, 'VIP 保级和退款规则')
    done = _last(events, 'done')
    process = done.get('process')
    assert process, 'The reply must carry its actual execution process'
    assert process['state'] == 'completed'
    stages = [s['stage'] for s in process['steps']]
    assert stages == ['route', 'task_prep', 'rewrite', 'retrieve', 'rerank', 'generate', 'check']
    assert all(s['state'] == 'done' for s in process['steps'])
    assert '按原句查询规则' in json.dumps(process, ensure_ascii=False)
    sources = next(s['sources'] for s in process['steps'] if s['stage'] == 'rerank')
    assert sources[0]['path'] == 'a.md'
    assert 'content' not in sources[0]
    assert len(env['models'].seen) == len(env['prep'].seen) == len(env['check'].seen) == 1
    assert [name for name, _ in env['pipe'].calls] == ['rewrite', 'retrieve', 'rerank', 'generate']
    saved = c.get('/api/kb/rounds/' + done['exec_id'] + '/status').json()
    assert saved['process'] == process


def test_reopened_history_keeps_the_process_for_each_answer_version(env):
    c = env['client']
    conv = _new_conv(c)
    first = _last(_ask(c, conv, 'VIP 规则'), 'done')
    env['pipe'].answer = '新版说明。'
    second = _last(_refresh(c, conv, first['logical_round_id']), 'done')
    history = c.get('/api/kb/conversations/' + conv + '/answer-history').json()
    assert history.get('messages'), 'Reopening must read saved answers, not a stale browser payload'
    answer = history['messages'][-1]
    assert answer['text'] == '新版说明。'
    assert answer['viewIndex'] == 1
    assert [v['process']['exec_id'] for v in answer['versions']] == [first['exec_id'], second['exec_id']]
    c.post('/api/kb/conversations/' + conv + '/clear')
    assert c.get('/api/kb/conversations/' + conv + '/answer-history').json()['messages'] == []
    assert c.get('/api/kb/rounds/' + first['exec_id'] + '/status').status_code == 404


def test_process_failure_does_not_claim_generation_or_check_completed(env):
    env['pipe'].stream_error = ModelError('gen_fail', '模型暂不可用')
    conv = _new_conv(env['client'])
    error = _last(_ask(env['client'], conv, 'VIP 规则'), 'error')
    process = error.get('process')
    assert process and process['state'] == 'failed'
    assert process['steps'][-1]['stage'] == 'generate'
    assert process['steps'][-1]['state'] == 'error'
    assert not any(s['stage'] == 'check' for s in process['steps'])


def test_smalltalk_has_no_invented_retrieval_or_verification(env):
    env['models'].replies = [_router_json('ack', False)]
    conv = _new_conv(env['client'])
    done = _last(_ask(env['client'], conv, '好的谢谢'), 'done')
    assert done.get('process')
    assert [s['stage'] for s in done['process']['steps']] == ['route']
    assert env['pipe'].calls == []


def test_process_history_is_owned_and_hidden_conversations_are_inaccessible(env):
    c = env['client']
    conv = _new_conv(c)
    done = _last(_ask(c, conv, 'VIP 规则'), 'done')
    c.post('/api/kb/auth/logout')
    c.post('/api/kb/auth/login', json={'username': 'admin', 'password': 'secret'})
    assert c.get('/api/kb/conversations/' + conv + '/answer-history').status_code == 404
    assert c.get('/api/kb/rounds/' + done['exec_id'] + '/status').status_code == 404
    c.post('/api/kb/auth/logout')
    c.post('/api/kb/auth/login', json={'username': 'alice', 'password': 'pw'})
    c.delete('/api/kb/conversations/' + conv)
    assert c.get('/api/kb/conversations/' + conv + '/answer-history').status_code == 404


def test_repair_keeps_failed_check_and_second_check_visible(env):
    env['check'].replies = [
        json.dumps({'check_status': 'fail', 'issues': [{'kind': 'unsupported', 'claim': '错误结论', 'reason': '缺少依据', 'evidence_ids': []}], 'conflict': False}),
        '修正后的说明。',
        json.dumps({'check_status': 'pass', 'issues': [], 'conflict': False}),
    ]
    conv = _new_conv(env['client'])
    done = _last(_ask(env['client'], conv, 'VIP 规则'), 'done')
    assert done and done.get('process')
    stages = done['process']['steps']
    assert [s['stage'] for s in stages][-3:] == ['check', 'repair', 'check']
    assert stages[-3]['state'] == 'warning'
    assert stages[-1]['state'] == 'done'
