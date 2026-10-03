"""管理后台复查：发布一致性、权限和删除后的原文边界。"""
import pytest

from app import main, settings
from app.config_store import ConfigStore, ConfigConflict
from app.issues import IssueBook, MemoryIssueRepo
from app.index_tasks import IndexTaskBook, MemoryTaskRepo
from app.prompts import check_prompts, list_slots
from tests.test_auth_m1 import _login, harness  # noqa: F401
from tests.test_m3_admin_base import _role_user


def test_default_slots_can_be_saved_together(tmp_path):
    payload = {r['id']: r['text'] for r in list_slots({}) if r['connected']}
    assert check_prompts(payload) is None
    store = ConfigStore(tmp_path / 'config.json')
    store.save_draft({'recall_k': 6, 'prompts': payload})
    assert store.draft['recall_k'] == 6


def test_publish_io_failure_keeps_live_draft_and_operation(tmp_path, monkeypatch):
    store = ConfigStore(tmp_path / 'config.json')
    store.save_draft({'recall_k': 7})
    old = store.accept_config()
    disk = store.path.read_bytes()
    monkeypatch.setattr(store, 'save', lambda: (_ for _ in ()).throw(OSError('disk full')))
    with pytest.raises(OSError):
        store.publish(store.draft_rev, 'failed-op')
    assert store.accept_config() == old
    assert store.draft['recall_k'] == 7
    assert 'failed-op' not in store.publish_ops
    assert store.path.read_bytes() == disk


def test_rollback_restores_entire_package_and_repeat_survives_restart(tmp_path):
    path = tmp_path / 'config.json'
    store = ConfigStore(path)
    original = store.accept_config()
    store.save_draft({'history_recovery': False, 'prompts': {'router': settings.ROUTER_PROMPT + '\n新包'}})
    store.publish(store.draft_rev, 'first')
    result = store.rollback(original['_package_id'], 'back')
    restored = store.accept_config()
    assert restored['history_recovery'] is True
    assert restored['prompts'] == original['prompts']
    reboot = ConfigStore(path)
    assert reboot.rollback(original['_package_id'], 'back') == result


def test_publish_operation_cannot_be_reused_for_another_revision_or_action(tmp_path):
    store = ConfigStore(tmp_path / 'config.json')
    store.save_draft({'recall_k': 7})
    rev = store.draft_rev
    published = store.publish(rev, 'once')
    store.save_draft({'recall_k': 9})
    assert store.publish(rev, 'once') == published
    with pytest.raises(ConfigConflict):
        store.publish(store.draft_rev, 'once')
    with pytest.raises(ConfigConflict):
        store.rollback(published['previous_id'], 'once')
    assert store.draft['recall_k'] == 9


def test_publish_rejects_incomplete_test_budget(tmp_path):
    store = ConfigStore(tmp_path / 'config.json')
    store.save_draft({'test_budget': {'calls': 2}})
    with pytest.raises(ValueError, match='测试预算'):
        store.publish(store.draft_rev)


def test_new_draft_can_use_the_revision_visible_after_publish_and_discard(tmp_path):
    store = ConfigStore(tmp_path / 'config.json')
    store.save_draft({'recall_k': 7}, 0)
    store.publish(store.draft_rev)
    published_view = store.snapshot()
    store.save_draft({'recall_k': 9}, published_view['draft_rev'])
    store.discard(store.draft_rev)
    discarded_view = store.snapshot()
    store.save_draft({'recall_k': 11}, discarded_view['draft_rev'])
    with pytest.raises(ConfigConflict):
        store.save_draft({'recall_k': 12}, published_view['draft_rev'])


def test_rewriter_keeps_complete_preassembled_l1_instead_of_legacy_slice():
    import asyncio
    import json
    from app.pipeline import Pipeline
    rendered = []
    class Models:
        async def rewrite(self, messages, temperature):
            rendered.extend(messages)
            return json.dumps({'status': 'ready', 'standalone_query': '查规则', 'response_constraint': '',
                               'missing_context': [], 'confidence': 1, 'named_feature_ids': [], 'same_topic': False})
    history = [{'role': role, 'text': f'第 {i} 轮 {role}'} for i in range(1, 4) for role in ('user', 'assistant')]
    asyncio.run(Pipeline(None, Models(), lambda: {}).rewrite('查规则', history, {'history_turns': 1}))
    assert all(m['text'] in rendered[1]['content'] for m in history)


def test_config_conflict_does_not_reveal_prompt(harness, tmp_path, monkeypatch):
    client, auth = harness
    cfg = ConfigStore(tmp_path / 'config.json')
    cfg.save_draft({'system_prompt': 'PRIVATE_PROMPT_MARKER'})
    monkeypatch.setattr(main, 'config_store', cfg)
    uname = _role_user(auth, '参数编辑', ['配置查看', '配置编辑'], 'param-editor')
    _login(client, uname, 'pw')
    conflict = client.put('/api/kb/config', json={'recall_k': 5, 'rev': 0})
    assert conflict.status_code == 409
    assert 'PRIVATE_PROMPT_MARKER' not in conflict.text


def test_prompt_editor_does_not_require_parameter_edit(harness, tmp_path, monkeypatch):
    client, auth = harness
    monkeypatch.setattr(main, 'config_store', ConfigStore(tmp_path / 'config.json'))
    uname = _role_user(auth, 'Prompt编辑', ['Prompt查看', 'Prompt编辑'], 'prompt-editor')
    _login(client, uname, 'pw')
    response = client.put('/api/kb/config', json={'prompts': {'router': settings.ROUTER_PROMPT}})
    assert response.status_code == 200
    assert response.json()['readonly'] == {}
    assert client.put('/api/kb/config', json={'recall_k': 8}).status_code == 403


def test_publisher_must_read_changed_content(harness, tmp_path, monkeypatch):
    client, auth = harness
    cfg = ConfigStore(tmp_path / 'config.json')
    cfg.save_draft({'system_prompt': 'PRIVATE_PROMPT_MARKER'})
    monkeypatch.setattr(main, 'config_store', cfg)
    uname = _role_user(auth, '仅发布', ['配置发布'], 'publisher')
    _login(client, uname, 'pw')
    response = client.post('/api/kb/config/publish', json={'rev': cfg.draft_rev})
    assert response.status_code == 403
    assert cfg.package_id == 'pkg-base'


def test_purge_removes_sensitive_issue_copies():
    book = IssueBook(MemoryIssueRepo())
    row = book.create('actor', {'title': 'PRIVATE title', 'symptom': 'PRIVATE symptom', 'source_type': 'conv', 'source_id': 'conv-x'})
    book.add_note(row['id'], 'actor', 'PRIVATE note')
    book.apply(row['id'], 'actor', {'status': 'closed', 'close_reason': 'external', 'close_basis': 'PRIVATE basis'}, lambda _: True)
    book.invalidate_conv('conv-x')
    public = book.public(book.repo.get(row['id']))
    assert 'PRIVATE' not in str(public)
    assert 'PRIVATE' not in str(book.repo.rows)
    assert 'PRIVATE' not in str(book.repo.notes)
    assert public['source_deleted'] is True


def test_running_task_outside_display_window_still_blocks_overlap():
    class WindowRepo(MemoryTaskRepo):
        def list_all(self):
            return super().list_all()[:100]
    repo = WindowRepo()
    book = IndexTaskBook(repo)
    old, _ = book.accept('memory', 'backfill', 'all', 'actor')
    for i in range(110):
        repo.insert({'id': str(i), 'grp': 'memory', 'scope': str(i), 'status': 'done', 'created_at': '9999'})
    new, hit = book.accept('memory', 'backfill', 'conv-x', 'actor')
    assert new is None
    assert hit['id'] == old['id']
