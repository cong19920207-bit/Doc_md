# -*- coding: utf-8 -*-
"""M3 后台底座：A01 权限拆分与迁移、A02 审计、A04 列表骨架、A03 账号角色页。"""
from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app import main
from app.auth_store import NEW_PERMS, PERM_CHECKBOX, ROLE_SUPER_ID
from tests.test_auth_m1 import _login, harness  # noqa: F401


def _role_user(store, name: str, perms: list[str], username: str | None = None) -> str:
    role = store.create_custom_role(name, perms)
    uname = username or ("u_" + role["id"])
    store.create_user(uname, "pw", role["id"])
    return uname


def _legacy_role(store, role_id: str, perms: list[str]) -> None:
    """模拟旧库角色：直接写库，绕过勾选项过滤。"""
    store.repo.upsert_role({
        "id": role_id, "name": "旧配置", "is_super": 0, "is_preset": 0, "created_at": store.now(),
    })
    store.repo.set_role_perms(role_id, perms)


# ---------- A01 ----------

def test_a01_new_perms_registered_super_full(harness):
    client, store = harness
    for code in NEW_PERMS:
        assert code in PERM_CHECKBOX
    assert "配置" not in PERM_CHECKBOX
    assert "对话删除" not in PERM_CHECKBOX
    assert store.role_perm_set(ROLE_SUPER_ID) == set(PERM_CHECKBOX)
    # 旧库超管只有旧清单：启动补全
    store.repo.set_role_perms(ROLE_SUPER_ID, ["知识问答", "配置"])
    store.sync_super_perms()
    assert store.role_perm_set(ROLE_SUPER_ID) == set(PERM_CHECKBOX)
    assert _login(client, "admin", "secret").status_code == 200
    roles = client.get("/api/kb/admin/roles").json()
    assert set(NEW_PERMS) <= set(roles["checkboxes"])
    assert "Prompt调试" not in roles["pending"]
    # 预置普通用户不自动扩权
    user_role = [r for r in roles["items"] if r["id"] == "role-user"][0]
    assert user_role["permissions"] == ["知识问答"]


def test_a01_t96_config_view_filters_prompt(harness):
    client, store = harness
    cfg_only = _role_user(store, "仅配置查看", ["配置查看"])
    prompt_only = _role_user(store, "仅Prompt查看", ["Prompt查看"])
    assert _login(client, cfg_only, "pw").status_code == 200
    data = client.get("/api/kb/config").json()
    assert "system_prompt" not in data["writable"] and "rewrite_prompt" not in data["writable"]
    assert "recall_k" in data["writable"]
    assert data["readonly"]
    assert "系统 Prompt" not in data["writable_fields"]
    assert data["editable"] == {"config": False, "prompt": False}
    assert client.put("/api/kb/config", json={"recall_k": 9}).status_code == 403
    client.post("/api/kb/auth/logout")
    assert _login(client, prompt_only, "pw").status_code == 200
    data = client.get("/api/kb/config").json()
    assert set(data["writable"].keys()) == {"system_prompt", "rewrite_prompt"}
    assert data["readonly"] == {}


def test_a01_t78_legacy_config_role_retired_and_reported(harness):
    client, store = harness
    _legacy_role(store, "role-legacy", ["配置", "问答明细"])
    store.create_account("old", "pw", "role-legacy")
    assert _login(client, "old", "pw").status_code == 200
    me = client.get("/api/kb/auth/me").json()
    assert "配置" not in me["permissions"]
    assert not (set(NEW_PERMS) & set(me["permissions"]))
    assert client.get("/api/kb/config").status_code == 403
    assert client.put("/api/kb/config", json={"recall_k": 3}).status_code == 403
    assert client.get("/api/kb/rounds").status_code == 200
    assert client.get("/api/kb/admin/perm-migration").status_code == 403
    client.post("/api/kb/auth/logout")
    assert _login(client, "admin", "secret").status_code == 200
    rep = client.get("/api/kb/admin/perm-migration").json()
    row = [x for x in rep["items"] if x["role_id"] == "role-legacy"][0]
    assert row["retired"] == ["配置"]
    assert row["account_count"] == 1
    assert row["current_permissions"] == ["问答明细"]
    roles = client.get("/api/kb/admin/roles").json()["items"]
    legacy = [r for r in roles if r["id"] == "role-legacy"][0]
    assert legacy["retired_permissions"] == ["配置"]
    assert "配置" not in legacy["permissions"]
    # 超管重新分配后，旧码被清掉，报告为空
    put = client.put("/api/kb/admin/roles/role-legacy/permissions", json={"permissions": ["配置查看", "问答明细"]})
    assert put.status_code == 200
    rep = client.get("/api/kb/admin/perm-migration").json()
    assert not [x for x in rep["items"] if x["role_id"] == "role-legacy"]


def test_a01_put_config_needs_edit_and_prompt_edit(harness):
    client, store = harness
    before = main.config_store.snapshot()["writable"]
    editor = _role_user(store, "配置编辑", ["配置查看", "配置编辑", "Prompt查看"])
    edit_no_view = _role_user(store, "只编辑", ["配置编辑"])
    assert _login(client, editor, "pw").status_code == 200
    denied = client.put("/api/kb/config", json={"recall_k": 7, "system_prompt": "改掉"})
    assert denied.status_code == 403
    assert denied.json()["code"] == "forbidden"
    assert main.config_store.snapshot()["writable"]["system_prompt"] == before["system_prompt"]
    ok = client.put("/api/kb/config", json={"recall_k": before["recall_k"]})
    assert ok.status_code == 200
    assert "system_prompt" in ok.json()["writable"]
    client.post("/api/kb/auth/logout")
    assert _login(client, edit_no_view, "pw").status_code == 200
    assert client.put("/api/kb/config", json={"recall_k": 5}).status_code == 403


def _audits(store, action=None):
    rows = store.repo.list_audits()
    return [r for r in rows if action is None or r.get("action") == action]


def _break_insert(store, monkeypatch):
    def boom(row):
        raise RuntimeError("audit db down")
    monkeypatch.setattr(store.repo, "insert_audit", boom)


# ---------- A02 ----------

def test_a02_t81_change_role_audited_with_before_after(harness):
    client, store = harness
    uname = _role_user(store, "明细", ["问答明细"], username="bob")
    bob = store.repo.get_account_by_username(uname)
    assert _login(client, "admin", "secret").status_code == 200
    res = client.patch(f"/api/kb/admin/accounts/{bob['id']}", json={"role_id": "role-user"})
    assert res.status_code == 200
    row = _audits(store, "change_role")[0]
    assert row["result"] == "success"
    assert row["op_id"] == row["id"]
    assert row["object"] == bob["id"] and row["object_type"] == "account"
    assert row["actor_username"] == "admin" and row["actor_role"]
    assert row["detail"]["before"]["role_id"] == bob["role_id"]
    assert row["detail"]["after"]["role_id"] == "role-user"
    assert row["changed_fields"] == ["role_id"]
    assert "pw" not in str(row) and "password" not in str(row).lower()
    listed = client.get("/api/kb/admin/audits").json()
    pub = [x for x in listed["items"] if x["action"] == "change_role"][0]
    assert pub["legacy"] is False and pub["pending_check"] is False
    assert "integrity" in listed


def test_a02_t83_high_risk_blocked_when_audit_down(harness, monkeypatch):
    client, store = harness
    uname = _role_user(store, "明细", ["问答明细"], username="bob")
    bob = store.repo.get_account_by_username(uname)
    assert _login(client, "admin", "secret").status_code == 200
    before_cfg = main.config_store.snapshot()["writable"]["recall_k"]
    _break_insert(store, monkeypatch)
    res = client.patch(f"/api/kb/admin/accounts/{bob['id']}", json={"role_id": "role-user"})
    assert res.status_code == 503 and res.json()["code"] == "audit_unavailable"
    assert store.repo.get_account(bob["id"])["role_id"] == bob["role_id"]
    cfg = client.put("/api/kb/config", json={"recall_k": before_cfg + 1})
    assert cfg.status_code == 503
    assert main.config_store.snapshot()["writable"]["recall_k"] == before_cfg
    assert client.post("/api/kb/admin/unlock", json={"username": "bob"}).status_code == 503
    assert client.post("/api/kb/admin/tls/disable").status_code == 503
    assert client.post("/api/kb/admin/accounts", json={
        "username": "x1", "password": "pw", "role_id": "role-user",
    }).status_code == 503
    assert store.repo.get_account_by_username("x1") is None
    assert store.audit_health()["blocked_high_risk"] >= 5
    # 登录只尽力记录，审计不可用不挡登录
    other = TestClient(main.app)
    assert _login(other, "bob", "pw").status_code == 200


def test_a02_t84_result_audit_fail_not_redone(harness, monkeypatch):
    client, store = harness
    role = store.create_custom_role("待改", ["问答明细"])
    assert _login(client, "admin", "secret").status_code == 200
    calls = {"n": 0}
    orig = store.set_custom_role_perms

    def counted(role_id, perms):
        calls["n"] += 1
        return orig(role_id, perms)

    monkeypatch.setattr(store, "set_custom_role_perms", counted)
    monkeypatch.setattr(store.repo, "update_audit", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("down")))
    res = client.put(f"/api/kb/admin/roles/{role['id']}/permissions", json={"permissions": ["反馈汇总"]})
    assert res.status_code == 200
    assert calls["n"] == 1
    assert store.role_perm_set(role["id"]) == {"反馈汇总"}
    row = _audits(store, "change_role_perms")[0]
    assert row["result"] == "accepted"
    pub = [x for x in client.get("/api/kb/admin/audits").json()["items"] if x["action"] == "change_role_perms"][0]
    assert pub["pending_check"] is True
    assert store.audit_health()["result_audit_failures"] == 1


def test_a02_t82_t85_t86_legacy_and_no_body(harness):
    client, store = harness
    store.repo.insert_audit({
        "id": "aud-old", "actor_id": "a", "actor_username": "admin", "action": "config_update",
        "object": "a", "ip": "", "created_at": store.now(), "detail": {"fields": ["system_prompt"]},
    })
    store.write_audit("conv_delete", actor_id="a", object_="c1", detail={
        "content": "被删原文", "system_prompt": "PROMPT-SECRET", "answer": "A", "fields": ["x"],
        "nested": {"query": "问句", "ok": 1},
    }, object_type="conversation", result="success")
    assert _login(client, "admin", "secret").status_code == 200
    ok = client.put("/api/kb/config", json={"system_prompt": main.config_store.snapshot()["writable"]["system_prompt"]})
    assert ok.status_code == 200
    items = client.get("/api/kb/admin/audits").json()["items"]
    old = [x for x in items if x["id"] == "aud-old"][0]
    assert old["legacy"] is True and old["before_ver"] is None and old["result"] is None
    assert old["detail"] == {"fields": ["system_prompt"]}
    dumped = str(items)
    assert "被删原文" not in dumped and "PROMPT-SECRET" not in dumped and "问句" not in dumped
    deleted = [x for x in items if x["action"] == "conv_delete"][0]
    assert deleted["detail"] == {"fields": ["x"], "nested": {"ok": 1}}
    prompt_text = main.config_store.snapshot()["writable"]["system_prompt"]
    assert prompt_text[:20] not in dumped


def test_a02_t101_read_audit_fail_still_returns(harness, monkeypatch):
    client, store = harness
    monkeypatch.setattr(main.logs, "get_round", lambda rid: {"round_id": rid, "user_id": "x", "answer": "正文"})
    assert _login(client, "admin", "secret").status_code == 200
    ok = client.get("/api/kb/rounds/r1")
    assert ok.status_code == 200
    assert _audits(store, "sensitive_read")[0]["object"] == "r1"
    assert "正文" not in str(_audits(store, "sensitive_read"))
    _break_insert(store, monkeypatch)
    res = client.get("/api/kb/rounds/r1")
    assert res.status_code == 200 and res.json()["answer"] == "正文"
    assert store.audit_health()["read_audit_failures"] == 1


# ---------- A04 ----------

ROOT = Path(__file__).resolve().parents[3]
ADMIN_JS = (ROOT / "site" / "kb-admin" / "admin.js").read_text(encoding="utf-8")


def test_a04_t91_list_error_not_empty(harness, monkeypatch):
    client, store = harness
    assert _login(client, "admin", "secret").status_code == 200

    def boom(**k):
        raise RuntimeError("db down")

    monkeypatch.setattr(main.logs, "page_rounds", boom)
    res = client.get("/api/kb/rounds")
    assert res.status_code == 503 and res.json()["code"] == "list_unavailable"
    monkeypatch.setattr(store.repo, "page_audits", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("x")))
    res = client.get("/api/kb/admin/audits")
    assert res.status_code == 503 and res.json()["code"] == "list_unavailable"
    bad = client.get("/api/kb/admin/accounts?cursor=@@@")
    assert bad.status_code == 400 and bad.json()["code"] == "bad_cursor"
    assert client.get("/api/kb/rounds", params={"cursor": "%%%"}).json()["code"] == "bad_cursor"
    # 前端：报错走 listError，不写「暂无记录」；总览不再先取 200 行
    assert "/rounds?limit=200" not in ADMIN_JS
    assert "加载失败：" in ADMIN_JS
    assert "listError(e)" in ADMIN_JS


def test_a04_audit_cursor_pages_stable(harness):
    client, store = harness
    same = store.now()
    for i in range(120):
        store.repo.insert_audit({
            "id": f"aud-{i:03d}", "actor_id": "a", "actor_username": "admin", "action": "unlock",
            "object": "u", "ip": "", "created_at": same, "detail": {},
        })
    assert _login(client, "admin", "secret").status_code == 200
    seen, cursor, pages = [], "", 0
    while True:
        data = client.get("/api/kb/admin/audits", params={"action": "unlock", "page_size": 50, "cursor": cursor}).json()
        pages += 1
        seen += [x["id"] for x in data["items"]]
        for key in ("next_cursor", "has_more", "total", "coverage", "data_cutoff", "time_field", "tz"):
            assert key in data
        assert data["tz"] == "Asia/Shanghai" and data["stored_tz"] == "UTC"
        if not data["has_more"]:
            break
        cursor = data["next_cursor"]
    assert pages == 3
    assert len(seen) == 120 == len(set(seen))
    assert seen == sorted(seen, reverse=True)
    big = client.get("/api/kb/admin/audits", params={"page_size": 999}).json()
    assert len(big["items"]) == 200 or not big["has_more"]
    legacy = client.get("/api/kb/admin/audits", params={"result": "legacy", "page_size": 5}).json()
    assert all(x["legacy"] for x in legacy["items"])


def test_a04_rounds_server_filter_and_accounts_page(harness, monkeypatch):
    client, store = harness
    got = {}

    def page_rounds(**k):
        got.update(k)
        return ([{"round_id": "r2", "created_at": "2026-09-29 10:00:00.000", "user_id": "x"}], True)

    monkeypatch.setattr(main.logs, "page_rounds", page_rounds)
    assert _login(client, "admin", "secret").status_code == 200
    data = client.get("/api/kb/rounds", params={"pending": 1, "page_size": 8, "q": "退款"}).json()
    assert got["pending"] is True and got["size"] == 8 and got["q"] == "退款"
    assert data["has_more"] is True and data["next_cursor"]
    client.get("/api/kb/rounds", params={"cursor": data["next_cursor"]})
    assert got["before"] == ("2026-09-29 10:00:00.000000", "r2")
    client.get("/api/kb/rounds", params={"limit": 300})
    assert got["size"] == 300
    for i in range(5):
        store.create_user(f"p{i}", "pw", "role-user")
    acc = client.get("/api/kb/admin/accounts", params={"page_size": 2}).json()
    assert len(acc["items"]) == 2 and acc["has_more"] and acc["total"] == 6
    acc2 = client.get("/api/kb/admin/accounts", params={"page_size": 2, "cursor": acc["next_cursor"]}).json()
    assert not ({x["id"] for x in acc["items"]} & {x["id"] for x in acc2["items"]})
    only = client.get("/api/kb/admin/accounts", params={"q": "p3"}).json()
    assert [x["username"] for x in only["items"]] == ["p3"]


def test_a04_csrf_origin_check(harness, monkeypatch):
    client, store = harness
    assert _login(client, "admin", "secret").status_code == 200
    evil = client.post("/api/kb/admin/unlock", json={"username": "x"}, headers={"Origin": "https://evil.example"})
    assert evil.status_code == 403 and evil.json()["code"] == "csrf_rejected"
    ref = client.post("/api/kb/admin/unlock", json={"username": "x"}, headers={"Referer": "https://evil.example/a"})
    assert ref.status_code == 403
    same = client.post("/api/kb/admin/unlock", json={"username": "x"}, headers={"Origin": "http://testserver:18768"})
    assert same.status_code == 200
    assert client.post("/api/kb/admin/unlock", json={"username": "x"}).status_code == 200
    assert client.post("/api/kb/admin/unlock", json={"username": "x"}, headers={"Origin": "null"}).status_code == 403
    # 读请求不校验
    assert client.get("/api/kb/auth/me", headers={"Origin": "https://evil.example"}).status_code == 200
    monkeypatch.setattr(main.settings, "TRUSTED_ORIGINS", ("https://portal.example",))
    ok = client.post("/api/kb/admin/unlock", json={"username": "x"}, headers={"Origin": "https://portal.example"})
    assert ok.status_code == 200
    anon = TestClient(main.app)
    res = anon.get("/api/kb/admin/accounts")
    assert res.status_code == 401 and res.json()["code"] == "unauthorized"


def test_a04_t92_safe_render_static():
    block = ADMIN_JS.split("function block(title, text)")[1].split("}")[0]
    assert "escapeHtml(text)" in block
    for needle in ("innerHTML = row.", "innerHTML = r.", "innerHTML = data."):
        assert needle not in ADMIN_JS
    assert "escapeHtml(JSON.stringify(r.detail" in ADMIN_JS


# ---------- A03 ----------

def test_a03_t75_role_perm_edit_page_and_audit(harness):
    client, store = harness
    role = store.create_custom_role("编辑中", ["问答明细"])
    assert _login(client, "admin", "secret").status_code == 200
    res = client.put(f"/api/kb/admin/roles/{role['id']}/permissions", json={"permissions": ["反馈汇总", "问答明细"]})
    assert res.status_code == 200
    row = _audits(store, "change_role_perms")[0]
    assert row["detail"]["added"] == ["反馈汇总"] and row["detail"]["removed"] == []
    assert row["detail"]["before"]["permissions"] == ["问答明细"]
    roles = client.get("/api/kb/admin/roles").json()["items"]
    assert all("account_count" in r for r in roles)
    # Drawer role changes and the read-only super role are exercised as behavior
    # in kb-admin/tests/admin-contract.test.cjs; do not freeze obsolete markup/copy.
    for needle in ("openRoleEditor", "预览变更", "window.confirm", "/admin/login-lock"):
        assert needle in ADMIN_JS


def test_a03_t76_last_super_guard_concurrent(harness, monkeypatch):
    import threading

    client, store = harness
    store.create_user("admin2", "pw", ROLE_SUPER_ID)
    ids = [store.repo.get_account_by_username(n)["id"] for n in ("admin", "admin2")]
    results = []

    def disable(aid):
        try:
            store.set_account_enabled(aid, False)
            results.append("ok")
        except PermissionError:
            results.append("denied")

    threads = [threading.Thread(target=disable, args=(aid,)) for aid in ids]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert sorted(results) == ["denied", "ok"]
    assert store.count_enabled_super() == 1
    # 前置检查被绕过（模拟另一进程同时改）时，写后复核回滚
    left = [a for a in ids if store.repo.get_account(a)["enabled"]][0]
    real = store.count_enabled_super
    seq = iter([2])
    monkeypatch.setattr(store, "count_enabled_super", lambda: next(seq, None) or real())
    try:
        store.set_account_role(left, "role-user")
        raised = False
    except PermissionError:
        raised = True
    assert raised
    assert store.repo.get_account(left)["role_id"] == ROLE_SUPER_ID
    assert real() == 1
    monkeypatch.setattr(store, "count_enabled_super", real)
    assert _login(client, "admin" if left == ids[0] else "admin2", "secret" if left == ids[0] else "pw").status_code == 200
    res = client.patch(f"/api/kb/admin/accounts/{left}", json={"role_id": "role-user"})
    assert res.status_code == 403
    assert _audits(store, "change_role")[0]["result"] == "failed"


def test_a03_t77_revoked_perm_blocks_old_page(harness):
    client, store = harness
    role = store.create_custom_role("明细", ["进管理模块", "问答明细"])
    store.create_user("carol", "pw", role["id"])
    carol = TestClient(main.app)
    assert _login(carol, "carol", "pw").status_code == 200
    assert carol.get("/api/kb/rounds").status_code == 200
    store.set_custom_role_perms(role["id"], ["进管理模块"])
    assert carol.get("/api/kb/rounds").status_code == 403
    store.set_account_enabled(store.repo.get_account_by_username("carol")["id"], False)
    assert carol.get("/api/kb/auth/me").status_code == 401


def test_a03_t79_unlock_only_login_lock(harness):
    client, store = harness
    store.create_user("dave", "pw", "role-user")
    dave = store.repo.get_account_by_username("dave")
    conv = main.convs.create(dave["id"], {"title": "t"})
    main.convs.set_save_block(conv["id"], "exec-blocked")
    for _ in range(5):
        client.post("/api/kb/auth/login", json={"username": "dave", "password": "bad"})
    assert _login(client, "admin", "secret").status_code == 200
    st = client.get("/api/kb/admin/login-lock", params={"username": "dave"}).json()
    assert st["locked"] is True and st["fail_count"] >= 5 and st["exists"] is True
    assert client.post("/api/kb/admin/unlock", json={"username": "dave"}).status_code == 200
    st = client.get("/api/kb/admin/login-lock", params={"username": "dave"}).json()
    assert st["locked"] is False and st["fail_count"] == 0
    assert main.convs.save_block_of(conv["id"]) == "exec-blocked"
    assert client.get("/api/kb/admin/login-lock").status_code == 400


def test_a03_t80_non_super_denied_even_with_all_boxes(harness):
    client, store = harness
    uname = _role_user(store, "全勾", list(PERM_CHECKBOX))
    target = store.create_custom_role("目标", [])
    assert _login(client, uname, "pw").status_code == 200
    calls = [
        ("POST", "/api/kb/admin/accounts", {"username": "z", "password": "pw", "role_id": "role-user"}),
        ("POST", "/api/kb/admin/roles", {"name": "r", "permissions": []}),
        ("PUT", f"/api/kb/admin/roles/{target['id']}/permissions", {"permissions": ["知识问答"]}),
        ("POST", "/api/kb/admin/unlock", {"username": "admin"}),
        ("POST", "/api/kb/admin/tls", {"cert_pem": "", "key_pem": ""}),
        ("POST", "/api/kb/admin/tls/enable", None),
        ("GET", "/api/kb/admin/login-lock?username=admin", None),
        ("GET", "/api/kb/admin/perm-migration", None),
    ]
    for method, path, body in calls:
        res = client.request(method, path, json=body)
        assert res.status_code == 403, (method, path, res.status_code)
    assert store.repo.get_account_by_username("z") is None


def test_a01_t74_page_perm_without_admin_gate(harness):
    client, store = harness
    uname = _role_user(store, "只明细", ["问答明细"])
    assert _login(client, uname, "pw").status_code == 200
    assert client.get("/api/kb/auth/admin-gate").status_code == 403
    assert client.get("/api/kb/rounds").status_code == 200
    assert client.get("/api/kb/config").status_code == 403
