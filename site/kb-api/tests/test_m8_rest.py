# -*- coding: utf-8 -*-
"""M8 其余步骤：配置校验与话术、Prompt 槽位、隔离测试、发布必过、旧入口。"""
from __future__ import annotations

from pathlib import Path

import pytest

from app import main, settings
from app.config_store import ConfigStore, enabled_texts
from app.l1 import assemble_l1
from app.msg_store import MemoryMsgRepo, MsgStore
from app.purge import MemoryPurgeRepo, PurgeBook
from app.recall import budget_for
from tests.test_auth_m1 import _login, harness  # noqa: F401
from tests.test_m3_admin_base import _role_user

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(autouse=True)
def _reset_tests(monkeypatch, tmp_path):
    import json
    from app.test_runs import TestBook
    book = TestBook(tmp_path / 'test-book.json')
    book.bind_sources(main._test_source)
    book.bind_executor(main._execute_admin_test)
    monkeypatch.setattr(main, 'test_book', book)
    async def reply(messages, temperature):
        return json.dumps({'route': 'ack', 'requires_history': False, 'confidence': 1, 'reason': '确认'})
    monkeypatch.setattr(main.models, 'rewrite', reply)


def _run(client, **body):
    import time
    body.setdefault('input', '谢谢')
    body.setdefault('mode', 'slot')
    if body.get('conv_id') and 'message_ids' not in body:
        body['message_ids'] = [m['id'] for m in main.msgs.admin_messages(body['conv_id'])]
    response = client.post('/api/kb/admin/test-runs', json=body)
    assert response.status_code == 202, response.text
    rid = response.json()['id']
    for _ in range(100):
        result = client.get('/api/kb/admin/test-runs/' + rid).json()
        if result['status'] not in ('queued', 'running'):
            return result
        time.sleep(.01)
    raise AssertionError('测试未在限定时间内完成')


def _store(monkeypatch, tmp_path):
    store = ConfigStore(tmp_path / "kb-config.json")
    store.release_gate = main.test_book.gate
    store.on_draft_saved = main.test_book.mark_stale
    monkeypatch.setattr(main, "config_store", store)
    return store


def _msgs(monkeypatch):
    msgs = MsgStore(MemoryMsgRepo())
    monkeypatch.setattr(main, "msgs", msgs)
    return msgs


def test_a09_t21_fixed_rules_rejected(harness, monkeypatch, tmp_path):
    client, _s = harness
    store = _store(monkeypatch, tmp_path)
    live = store.package_id
    assert _login(client, "admin", "secret").status_code == 200
    denied = client.put("/api/kb/config", json={"l1_rounds": 40, "l1_tokens": 99999, "repair_max": 3, "cross_session": True})
    assert denied.status_code == 400
    assert "固定规则" in denied.json()["message"]
    assert "L1" in denied.json()["message"]
    assert store.package_id == live
    view = client.get("/api/kb/config").json()
    assert "l1_rounds" not in (view.get("writable") or {})
    assert any(x["id"] == "l1_rounds" for x in view["fixed_rules"])


def test_a09_t22_blank_budget_cannot_enable(harness, monkeypatch, tmp_path):
    client, _s = harness
    _store(monkeypatch, tmp_path)
    assert _login(client, "admin", "secret").status_code == 200
    saved = client.put("/api/kb/config", json={
        "history_recovery": True,
        "recall_budget": {"calls": "", "steps": "", "parallel": "", "tokens": ""},
    })
    assert saved.status_code == 200
    pub = client.post("/api/kb/config/publish", json={"rev": saved.json()["draft_rev"]})
    assert pub.status_code == 400
    assert "空白" in pub.json()["message"]
    assert "不能启用" in pub.json()["message"]


def test_a09_t23_combo_names_fields(harness, monkeypatch, tmp_path):
    client, _s = harness
    _store(monkeypatch, tmp_path)
    assert _login(client, "admin", "secret").status_code == 200
    denied = client.put("/api/kb/config", json={"recall_budget": {"calls": 2, "parallel": 5, "steps": 4, "tokens": 1000}})
    assert denied.status_code == 400
    text = denied.json()["message"]
    assert "recall_budget.parallel" in text
    assert "recall_budget.calls" in text


def test_a09_t25_draft_rev_conflict(harness, monkeypatch, tmp_path):
    client, _s = harness
    store = _store(monkeypatch, tmp_path)
    assert _login(client, "admin", "secret").status_code == 200
    first = client.put("/api/kb/config", json={"recall_k": 5, "rev": 0})
    assert first.status_code == 200
    second = client.put("/api/kb/config", json={"recall_k": 8, "rev": 0})
    assert second.status_code == 409
    assert second.json()["code"] == "draft_conflict"
    assert "draft" in second.json()["diff"]
    assert store.draft["recall_k"] == 5


def test_a09_t26_empty_pool_blocks_publish(harness, monkeypatch, tmp_path):
    client, _s = harness
    _store(monkeypatch, tmp_path)
    assert _login(client, "admin", "secret").status_code == 200
    saved = client.put("/api/kb/config", json={
        "ack_pool": [{"text": "好的。", "enabled": False}],
        "scope_pool": [{"text": "当前只处理已有规则。", "enabled": True}],
    })
    assert saved.status_code == 200
    pub = client.post("/api/kb/config/publish", json={"rev": saved.json()["draft_rev"]})
    assert pub.status_code == 400
    assert "确认话术池" in pub.json()["message"]
    assert "另一个池" in pub.json()["message"]
    pools = {"ack": [{"text": "好的。", "enabled": False}], "scope": [{"text": "当前只处理已有规则。", "enabled": True}]}
    assert enabled_texts({"pools": pools}, "ack") == []
    assert enabled_texts({"pools": pools}, "scope") == ["当前只处理已有规则。"]


def test_a09_t27_history_off_keeps_l1(harness, monkeypatch, tmp_path):
    client, _s = harness
    store = _store(monkeypatch, tmp_path)
    store.release_gate = None
    assert _login(client, "admin", "secret").status_code == 200
    saved = client.put("/api/kb/config", json={"history_recovery": False})
    pub = client.post("/api/kb/config/publish", json={"rev": saved.json()["draft_rev"]})
    assert pub.status_code == 200
    package = store.accept_config()
    assert package["history_recovery"] is False
    budget = budget_for(package, 1000)
    assert budget.enabled is False
    rows = [
        {"id": "u", "role": "user", "content": "保级规则", "round_id": "lr1", "round_seq": 1, "seq": 1, "completeness": "complete"},
        {"id": "a", "role": "assistant", "content": "按自然月。", "round_id": "lr1", "round_seq": 1, "seq": 2, "completeness": "complete", "is_current": 1},
    ]
    assert assemble_l1(rows)["turns"]
    assert "从未" not in (package.get("history_note") or "历史恢复已停用，本轮只使用当前有效上下文，不查找更早对话")


def test_a09_t28_key_is_configured_not_available(harness, monkeypatch, tmp_path):
    client, _s = harness
    _store(monkeypatch, tmp_path)
    assert _login(client, "admin", "secret").status_code == 200
    view = client.get("/api/kb/config").json()
    keys = view["readonly"]["Key 状态"]
    assert keys["DashScope"] in ("已配置", "未配置")
    assert keys["DeepSeek"] in ("已配置", "未配置")
    assert keys["DashScope"] != "可用"
    assert "不能当成可用" in view["key_note"]


def test_a09_admin_page_keeps_editor_and_preview():
    js = (ROOT / "kb-admin" / "admin.js").read_text(encoding="utf-8")
    assert "未保存" in js
    assert "预览将发出的原文" in js
    assert "不调用模型" in js
    assert "beforeunload" in js
    # Read-only rule controls are checked by admin-contract.test.cjs; server-side
    # rejection remains covered by test_a09_t21_fixed_rules_rejected.
    assert "未接入" in js


def test_a10_t29_router_rejects_tools(harness, monkeypatch, tmp_path):
    client, _s = harness
    _store(monkeypatch, tmp_path)
    assert _login(client, "admin", "secret").status_code == 200
    denied = client.put("/api/kb/config", json={"prompts": {"router": settings.ROUTER_PROMPT + "\ntool_call"}})
    assert denied.status_code == 400
    assert "tool_call" in denied.json()["message"]


def test_a10_t30_missing_required_text(harness, monkeypatch, tmp_path):
    client, _s = harness
    _store(monkeypatch, tmp_path)
    assert _login(client, "admin", "secret").status_code == 200
    denied = client.put("/api/kb/config", json={"prompts": {"router": "hello"}})
    assert denied.status_code == 400
    assert "缺少" in denied.json()["message"]
    offline = client.put("/api/kb/config", json={"prompts": {"generate": "随便写"}})
    assert offline.status_code == 400
    assert "未接入" in offline.json()["message"]


def test_a10_t40_save_does_not_call_model(harness, monkeypatch, tmp_path):
    client, _s = harness
    _store(monkeypatch, tmp_path)
    called = {"n": 0}

    def boom(*_a, **_k):
        called["n"] += 1
        raise AssertionError("不应调用模型")

    monkeypatch.setattr(main.models, "rewrite", boom)
    assert _login(client, "admin", "secret").status_code == 200
    saved = client.put("/api/kb/config", json={"prompts": {"router": settings.ROUTER_PROMPT}})
    assert saved.status_code == 200
    detail = client.get("/api/kb/config")
    assert detail.status_code == 200
    assert any(x["id"] == "router" and x["status"] == "已接入" for x in detail.json()["prompts"])
    assert any(x["id"] == "generate" and x["status"] == "未接入" for x in detail.json()["prompts"])
    assert called["n"] == 0


def test_a10_t36_edit_marks_old_test(harness, monkeypatch, tmp_path):
    client, _ = harness
    _store(monkeypatch, tmp_path)
    _login(client, 'admin', 'secret')
    rev = client.put('/api/kb/config', json={'prompts': {'router': settings.ROUTER_PROMPT + '\n测试版本'}}).json()['draft_rev']
    run = _run(client, rev=rev)
    client.put('/api/kb/config', json={'recall_k': 5, 'rev': rev})
    assert client.get('/api/kb/admin/test-runs/' + run['id']).json()['stale'] is True


def test_a11_t32_chain_uses_real_orchestrator_without_production_writes(harness, monkeypatch, tmp_path):
    client, auth = harness
    _store(monkeypatch, tmp_path)
    msgs = _msgs(monkeypatch)
    hits = []
    monkeypatch.setattr(main.logs, 'insert_running', lambda row: hits.append(row) or True)
    _login(client, 'admin', 'secret')
    run = _run(client, mode='chain')
    assert run['status'] == 'done'
    assert run['route'] == 'ack'
    assert run['usage']['calls'] == 1
    assert run['events'][-1]['event'] == 'done'
    assert run['production_write'] is False
    assert msgs.repo.rows == [] and hits == []


def test_a11_t33_only_selected_real_messages_are_copied(harness, monkeypatch, tmp_path):
    client, auth = harness
    _store(monkeypatch, tmp_path)
    _msgs(monkeypatch)
    owner = _role_user(auth, '原主人', ['知识问答'], 'owner33')
    owner_id = auth.repo.get_account_by_username(owner)['id']
    conv = main.convs.create(owner_id, {'title': '来源'})
    selected = main.msgs.append_user(conv['id'], '选定文本', 'req1', 'ex1')
    main.msgs.append_user(conv['id'], '未选定私密文本', 'req2', 'ex2')
    _login(client, 'admin', 'secret')
    run = _run(client, conv_id=conv['id'], message_ids=[selected['id']])
    assert [m['content'] for m in run['snapshot']['messages']] == ['选定文本']
    assert '未选定私密文本' not in str(run)
    assert run['snapshot']['owner'] == owner_id


def test_execution_import_requires_only_its_message_detail_permission(harness, monkeypatch, tmp_path):
    client, auth = harness
    _store(monkeypatch, tmp_path)
    _msgs(monkeypatch)
    admin = auth.repo.get_account_by_username('admin')
    conv = main.convs.create(admin['id'], {'title': '来源'})
    user = main.msgs.append_user(conv['id'], '谢谢', 'req', 'ex')
    answer = main.msgs.append_assistant(conv['id'], user, 'ex', '收到', 'complete')
    other = main.msgs.append_user(conv['id'], 'PRIVATE other round', 'req2', 'ex2')
    monkeypatch.setattr(main.logs, 'get_round', lambda _: {'conv_id': conv['id'], 'user_msg_id': user['id'], 'assistant_msg_id': answer['id']})
    uname = _role_user(auth, '执行调试', ['配置查看', 'Prompt查看', 'Prompt调试', '问答明细'], 'exec-debug')
    _login(client, uname, 'pw')
    run = _run(client, exec_id='ex', message_ids=[user['id'], answer['id']])
    assert run['source_exec'] == 'ex'
    assert {m['id'] for m in run['snapshot']['messages']} == {user['id'], answer['id']}
    assert 'PRIVATE' not in str(run)
    assert run['time_base'] == str(user['created_at'])
    denied = client.post('/api/kb/admin/test-runs', json={'exec_id': 'ex', 'input': '谢谢', 'message_ids': [other['id']]})
    assert denied.status_code == 403


def test_task_preparer_uses_the_accepted_prompt_and_real_schema(harness, monkeypatch, tmp_path):
    import json
    client, _ = harness
    _store(monkeypatch, tmp_path)
    from app.prompts import list_slots
    prompt = next(s['text'] for s in list_slots({}) if s['id'] == 'task_prep') + '\nTASK_PREP_REVIEW_MARKER'
    _login(client, 'admin', 'secret')
    rev = client.put('/api/kb/config', json={'prompts': {'task_prep': prompt}}).json()['draft_rev']
    async def reply(messages, temperature):
        assert 'TASK_PREP_REVIEW_MARKER' in messages[0]['content']
        return json.dumps({'tasks': [{'task_id': 'T1', 'goal': '查规则', 'mode': '查询', 'check': 'ready'}], 'excluded': [], 'information_gaps': [], 'response_constraint': ''})
    monkeypatch.setattr(main.models, 'rewrite', reply)
    run = _run(client, slot='task_prep', rev=rev)
    assert run['schema_ok'] is True
    assert run['covered_slots'] == ['task_prep']
    assert 'TASK_PREP_REVIEW_MARKER' in str(run['rendered'])


def test_a11_t34_hide_and_clear_revoke_old_test_copies(harness, monkeypatch, tmp_path):
    client, auth = harness
    _store(monkeypatch, tmp_path)
    _msgs(monkeypatch)
    acc = auth.repo.get_account_by_username('admin')
    _login(client, 'admin', 'secret')
    for action in ('hide', 'clear'):
        conv = main.convs.create(acc['id'], {'title': action})
        main.msgs.append_user(conv['id'], 'PRIVATE_SOURCE', action, action)
        run = _run(client, conv_id=conv['id'])
        if action == 'hide':
            main.convs.delete(acc['id'], conv['id'])
        else:
            boundary = main.msgs.clear(conv['id'], acc['id'])
            main.convs.note_clear(conv['id'], boundary)
        result = client.get('/api/kb/admin/test-runs/' + run['id']).json()
        assert result['snapshot']['messages'] == []
        assert 'PRIVATE_SOURCE' not in str(result)
        assert 'PRIVATE_SOURCE' not in main.test_book.path.read_text()


def test_chain_builds_memory_only_from_selected_copies_within_call_budget(harness, monkeypatch, tmp_path):
    client, auth = harness
    _store(monkeypatch, tmp_path)
    _msgs(monkeypatch)
    owner = auth.repo.get_account_by_username('admin')
    conv = main.convs.create(owner['id'], {'title': '隔离 Memory'})
    user = main.msgs.append_user(conv['id'], '选定的历史文本', 'r1', 'e1')
    main.msgs.append_user(conv['id'], 'PRIVATE_NOT_SELECTED', 'r2', 'e2')
    seen = []
    async def embed(texts):
        seen.extend(texts)
        return [[1., 0.] for _ in texts]
    monkeypatch.setattr(main.models, 'embed', embed)
    monkeypatch.setattr(main.mem_index.vec, 'upsert', lambda _: (_ for _ in ()).throw(AssertionError('不能写生产 Memory')))
    _login(client, 'admin', 'secret')
    rev = client.put('/api/kb/config', json={'recall_budget': {'calls': 4, 'steps': 4, 'parallel': 2, 'tokens': 3000}}).json()['draft_rev']
    run = _run(client, mode='chain', conv_id=conv['id'], message_ids=[user['id']], rev=rev)
    assert run['status'] == 'done'
    assert seen and '选定的历史文本' in seen[0]
    assert 'PRIVATE_NOT_SELECTED' not in str(seen) + str(run)
    assert run['usage']['calls'] == 2  # 隔离副本 embedding + 实际 Router


def test_a11_t35_purge_removes_all_test_body_copies(harness, monkeypatch, tmp_path):
    client, auth = harness
    _store(monkeypatch, tmp_path)
    _msgs(monkeypatch)
    acc = auth.repo.get_account_by_username('admin')
    conv = main.convs.create(acc['id'], {'title': '实际删除'})
    main.msgs.append_user(conv['id'], 'PRIVATE_SOURCE', 'purge', 'purge')
    _login(client, 'admin', 'secret')
    run = _run(client, conv_id=conv['id'])
    main.test_book.invalidate(conv['id'])
    result = client.get('/api/kb/admin/test-runs/' + run['id']).json()
    assert result['note'] == '来源已删除'
    assert 'PRIVATE_SOURCE' not in main.test_book.path.read_text()


def test_a11_t37_compare_keeps_source_and_output_differences(harness, monkeypatch, tmp_path):
    client, _ = harness
    _store(monkeypatch, tmp_path)
    _login(client, 'admin', 'secret')
    left = _run(client, input='谢谢')
    right = _run(client, input='好的')
    result = client.get('/api/kb/admin/test-runs/compare', params={'a': left['id'], 'b': right['id']}).json()
    assert result['same_input'] is False
    assert result['left']['output'] and result['right']['output']


def test_a11_t38_client_flags_cannot_forge_real_output(harness, monkeypatch, tmp_path):
    client, _ = harness
    _store(monkeypatch, tmp_path)
    async def invalid(*_args, **_kwargs):
        return 'invalid json'
    monkeypatch.setattr(main.models, 'rewrite', invalid)
    _login(client, 'admin', 'secret')
    run = _run(client, schema_ok=True, biz_resolved=True, refused=True)
    assert run['status'] == 'failed'
    assert run['schema_ok'] is False
    assert run['biz_resolved'] is None
    assert run['passed'] is False


def test_a11_t39_budget_and_source_permissions_checked_before_start(harness, monkeypatch, tmp_path):
    client, auth = harness
    _store(monkeypatch, tmp_path)
    _login(client, 'admin', 'secret')
    denied = client.post('/api/kb/admin/test-runs', json={'input': '谢谢', 'needs_recall': True})
    assert denied.status_code == 400 and '未开始' in denied.json()['message']
    uname = _role_user(auth, '调试但无原文', ['Prompt调试', 'Prompt查看', '配置查看', '问答明细'], 'partial-debug')
    _login(client, uname, 'pw')
    assert client.post('/api/kb/admin/test-runs', json={'input': '谢谢', 'conv_id': 'another', 'message_ids': ['m1']}).status_code == 403
    assert _run(client)['status'] == 'done'


def test_a11_t98_result_survives_process_restart(harness, monkeypatch, tmp_path):
    from app.test_runs import TestBook
    client, _ = harness
    _store(monkeypatch, tmp_path)
    _login(client, 'admin', 'secret')
    run = _run(client)
    reboot = TestBook(main.test_book.path)
    assert reboot.get(run['id'])['output'] == run['output']
    assert reboot.get(run['id'])['status'] == 'done'


def test_disabling_recall_with_blank_budget_can_be_verified_by_the_chain(harness, monkeypatch, tmp_path):
    client, _ = harness
    _store(monkeypatch, tmp_path)
    _login(client, 'admin', 'secret')
    case = client.post('/api/kb/admin/test-cases', json={'title': '停用追溯', 'critical': True, 'input': '谢谢', 'mode': 'chain', 'assertions': {'route': 'ack'}}).json()
    rev = client.put('/api/kb/config', json={'history_recovery': False, 'recall_budget': {'calls': '', 'steps': '', 'parallel': '', 'tokens': ''}}).json()['draft_rev']
    assert _run(client, case_id=case['id'], rev=rev)['passed'] is True
    result = client.post('/api/kb/config/publish', json={'rev': rev, 'reason': '停用历史追溯'})
    assert result.status_code == 200, result.text


def test_pool_publish_gate_requires_the_changed_branch(harness, monkeypatch, tmp_path):
    client, _ = harness
    store = _store(monkeypatch, tmp_path)
    _login(client, 'admin', 'secret')
    case = client.post('/api/kb/admin/test-cases', json={'title': '确认链路', 'critical': True, 'input': '谢谢', 'mode': 'chain', 'assertions': {'route': 'ack'}}).json()
    rev = client.put('/api/kb/config', json={'scope_pool': [{'text': '只回答支持范围内的问题', 'enabled': True}]}).json()['draft_rev']
    run = _run(client, case_id=case['id'], rev=rev)
    assert run['passed'] is True
    result = client.post('/api/kb/config/publish', json={'rev': rev, 'reason': '范围话术调整'})
    assert result.status_code == 400
    assert 'scope_pool' in result.json()['message']
    assert store.package_id == 'pkg-base'


def test_a12_t99_gate_requires_real_assertion_for_exact_revision(harness, monkeypatch, tmp_path):
    from app.test_runs import TestBook
    client, _ = harness
    cfg = _store(monkeypatch, tmp_path)
    _login(client, 'admin', 'secret')
    rev = client.put('/api/kb/config', json={'prompts': {'router': settings.ROUTER_PROMPT + '\n测试版本'}}).json()['draft_rev']
    blocked = client.post('/api/kb/config/publish', json={'rev': rev})
    assert blocked.status_code == 400 and blocked.json()['code'] == 'release_blocked'
    case = client.post('/api/kb/admin/test-cases', json={'title': '确认路由', 'critical': True, 'input': '谢谢', 'assertions': {'route': 'ack'}}).json()
    run = _run(client, rev=rev, case_id=case['id'], schema_ok=False, refused=True)
    assert run['passed'] is True and run['route'] == 'ack'
    reboot = TestBook(main.test_book.path)
    assert reboot.gate(rev)[0] is None
    repeated = client.post('/api/kb/admin/test-cases', json={'id': case['id'], 'critical': False, 'input': '谢谢', 'assertions': {'route': 'ack'}})
    assert repeated.status_code == 400
    wrong_package = dict(run['config'], recall_k=99)
    assert reboot.gate(rev, wrong_package)[0] is not None
    assert client.post('/api/kb/config/publish', json={'rev': rev, 'op_id': 'real-tested', 'reason': '验证 Router 修改'}).status_code == 200


def test_a19_t93_old_writes_do_not_retarget(harness, monkeypatch, tmp_path):
    client, store = harness
    cfg = _store(monkeypatch, tmp_path)
    msgs = _msgs(monkeypatch)
    acc = store.repo.get_account_by_username("admin")
    conv = main.convs.create(acc["id"], {"title": "旧入口"})
    user = msgs.append_user(conv["id"], "服务端原文", "cr-t93", "ex-t93")
    msgs.append_assistant(conv["id"], user, "ex-t93", "服务端回答", "complete")
    live = cfg.package_id
    assert _login(client, "admin", "secret").status_code == 200
    saved = client.put("/api/kb/config", json={"recall_k": cfg.data["recall_k"] + 1})
    assert saved.status_code == 200
    assert cfg.package_id == live
    put = client.put(f"/api/kb/conversations/{conv['id']}", json={"messages": [{"role": "user", "content": "客户端想覆盖"}]})
    assert put.status_code == 200
    contents = [m["content"] for m in msgs.admin_messages(conv["id"])]
    assert contents[0] == "服务端原文"
    assert "客户端想覆盖" not in contents

    def get_round(_rid):
        return {
            "round_id": _rid,
            "user_id": acc["id"],
            "assistant_msg_id": "m-real",
            "schema_ver": "v3",
            "msg_save": "saved",
            "status": "success",
        }

    monkeypatch.setattr(main.logs, "get_round", get_round)
    monkeypatch.setattr(main.logs, "set_feedback", lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("不应改写反馈")))
    denied = client.post("/api/kb/rounds/ex-t93/feedback", json={"feedback": "down", "assistant_msg_id": "m-other"})
    assert denied.status_code == 409
    assert denied.json()["code"] == "feedback_target"


def test_a19_t94_unconnected_blocks_stay_unconnected(harness, monkeypatch, tmp_path):
    client, _s = harness
    _store(monkeypatch, tmp_path)
    assert _login(client, "admin", "secret").status_code == 200
    view = client.get("/api/kb/config").json()
    assert "故障重试" in view["unconnected"]
    assert "分类兜底" in view["unconnected"]
    assert "在线更换模型" in view["unconnected"]
    roles = client.get("/api/kb/admin/roles").json()
    assert "Prompt调试" not in roles["pending"]
    js = (ROOT / "kb-admin" / "admin.js").read_text(encoding="utf-8")
    assert "未接入" in js
    assert "故障重试页" not in js


def test_a19_t95_login_is_not_admin_or_qa(harness):
    client, store = harness
    conf = (ROOT / "docker" / "nginx.conf").read_text(encoding="utf-8")
    assert "auth_request /_kb_site_gate" in conf
    assert "location = /_kb_admin_gate" in conf
    assert "auth_request /_kb_admin_gate" in conf
    login_at = conf.find("location = /login")
    assert "auth_request off" in conf[login_at:login_at + 180]
    feature_at = conf.find("location ^~ /feature-interaction/")
    feature = conf[feature_at:feature_at + 160]
    assert "auth_request off" not in feature
    uname = _role_user(store, "只登录", ["配置查看"], "onlylogin")
    assert _login(client, uname, "pw").status_code == 200
    ask = client.post("/api/kb/ask", json={"query": "保级规则"})
    assert ask.status_code == 403
    debug = client.get("/api/kb/admin/test-runs/none")
    assert debug.status_code == 403
