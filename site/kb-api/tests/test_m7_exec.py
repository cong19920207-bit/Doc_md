# -*- coding: utf-8 -*-
"""M7 A07：执行详情七组只读视图，历史正文另要对话审计。"""
from __future__ import annotations

from fastapi.testclient import TestClient

from app import main
from app.exec_view import LEGACY, build, referenced_msg_ids
from tests.test_auth_m1 import _login, harness  # noqa: F401
from tests.test_m3_admin_base import _role_user


def _text(view, title, label):
    group = next(g for g in view["groups"] if g["title"] == title)
    return next(it["text"] for it in group["items"] if it["label"] == label)


def test_a07_t12_not_loaded_is_not_no_history():
    """T12：L1 超预算显示未载入原因，不写成没有历史。"""
    view = build({
        "schema_ver": 1, "original_query": "退款呢",
        "snapshot": {"l1_not_loaded": ["超预算整轮未载入"], "l1_tokens": 0, "l1_round_ids": [], "l1_msg_ids": []},
    })
    loaded = _text(view, "输入与上下文", "L1")
    assert "超预算整轮未载入" in loaded and "没有历史" not in loaded


def test_a07_t13_no_memory_is_normal_path():
    """T13：requires_history 为真但本轮没调用记忆，不告警成缺步骤。"""
    view = build({"schema_ver": 1, "requires_history": 1, "route": "knowledge_query", "recall": None})
    note = _text(view, "历史恢复", "记忆")
    assert "正常路径" in note and "不要当成少了步骤" in note


def test_a07_t14_gap_status_kept_separately():
    """T14：同一批缺口一成一败，逐项保留。"""
    view = build({
        "schema_ver": 1,
        "recall": {"gap_status": {"G1": "resolved", "G2": "open"}, "items": [
            {"gap_id": "G1", "status": "ok"}, {"gap_id": "G2", "status": "timeout"},
        ], "stop_reason": "tool_error", "coverage": "partial"},
    })
    text = _text(view, "历史恢复", "逐缺口")
    assert "G1：resolved" in text and "G2 调用 timeout" in text


def test_a07_t15_route_stays_original():
    """T15：追溯之后原始 Route 仍是当时的分类。"""
    view = build({"schema_ver": 1, "route": "knowledge_query", "rewrite": {"status": "needs_context", "after_recall": True}})
    assert _text(view, "路由与任务", "原始 Route") == "knowledge_query"


def test_a07_t16_candidates_not_cgen():
    """T16：没有另记候选时，不把送入生成的材料说成候选。"""
    view = build({"schema_ver": 1, "c_gen": [{"path": "a"}], "lanes": []})
    assert "不把送入生成的材料当成候选" in _text(view, "改写与知识", "命中候选")
    assert _text(view, "改写与知识", "实际送入生成") == "1 条"


def test_a07_t17_drafts_listed_apart():
    """T17：初稿与修正稿分成两份检查记录。"""
    view = build({"schema_ver": 1, "evidence_check": {
        "rounds": [{"check_status": "fail", "issues": [{}]}, {"check_status": "pass", "issues": []}],
        "repair_count": 1,
    }})
    text = _text(view, "生成、检查与修正", "检查记录")
    assert "第 1 份草稿 fail" in text and "第 2 份草稿 pass" in text
    assert _text(view, "生成、检查与修正", "修正次数") == "1"


def test_a07_t18_statuses_stay_separate():
    """T18：检查通过、业务部分完成、消息没存上，三项分开。"""
    view = build({"schema_ver": 1, "check_status": "pass", "biz_result": "partial", "msg_save": "failed"})
    got = {s["key"]: s["text"] for s in view["statuses"]}
    assert got["check_status"] == "pass" and got["biz_result"] == "partial" and got["msg_save"] == "failed"


def test_a07_t19_current_source_is_separate():
    """T19：当次证据不写成当前来源。"""
    view = build({"schema_ver": 1, "answer": "正文"})
    assert "当前来源另列" in _text(view, "交付与保存", "当次证据")


def test_a07_t20_legacy_marked():
    """T20：没有 schema 的旧执行，新字段标旧版未记录。"""
    view = build({"original_query": "旧问题", "answer": "旧回答", "status": "success"})
    assert view["legacy"] is True
    assert _text(view, "路由与任务", "原始 Route") == LEGACY
    assert _text(view, "输入与上下文", "当前原句") == "旧问题"


def test_a07_t11_and_filters_and_t73(harness, monkeypatch):
    """T11：发送与刷新是两次执行。列表把发起方式和 Route 交给服务端。T73：只有问答明细读不到历史正文。"""
    client, store = harness
    secret = "机密历史正文"
    row = {
        "round_id": "e-send", "conv_id": "c1", "schema_ver": 1, "op_type": "send", "route": "knowledge_query",
        "logical_round_id": "lr-1", "original_query": "怎么退款", "answer": "按渠道退回", "status": "success",
        "user_id": "u", "snapshot": {"l1_msg_ids": [["m-old", "m-ans"]], "l1_tokens": 10, "l1_round_ids": ["lr-0"]},
        "requires_history": 0, "recall": None, "created_at": "2026-09-29 10:00:00.000",
    }
    refresh = dict(row, round_id="e-refresh", op_type="refresh")
    seen = {}

    def page_rounds(**k):
        seen.update(k)
        items = [row, refresh]
        if k.get("op_type"):
            items = [r for r in items if r["op_type"] == k["op_type"]]
        return items, False

    monkeypatch.setattr(main.logs, "page_rounds", page_rounds)
    monkeypatch.setattr(main.logs, "get_round", lambda rid: row if rid == "e-send" else None)
    monkeypatch.setattr(main.msgs, "get_by_ids", lambda conv, ids: [
        {"id": "m-old", "conv_id": conv, "role": "user", "content": secret, "seq": 1, "round_id": "lr-0",
         "round_seq": 1, "completeness": "complete"}
    ] if "m-old" in ids else [])

    assert _login(client, "admin", "secret").status_code == 200
    listed = client.get("/api/kb/rounds", params={"op_type": "refresh", "route": "knowledge_query"})
    assert listed.status_code == 200
    assert seen["op_type"] == "refresh" and seen["route"] == "knowledge_query"
    assert [x["round_id"] for x in listed.json()["items"]] == ["e-refresh"]
    assert build(row)["groups"] and build(refresh)["groups"]
    assert _text(build(row), "交付与保存", "执行状态")

    detail = client.get("/api/kb/rounds/e-send")
    assert detail.status_code == 200 and secret not in detail.text
    assert "view" in detail.json() and referenced_msg_ids(row) == {"m-old", "m-ans"}

    client.post("/api/kb/auth/logout")
    uname = _role_user(store, "只明细", ["进管理模块", "问答明细"], username="only-rounds")
    assert _login(client, uname, "pw").status_code == 200
    denied = client.get("/api/kb/rounds/e-send/context/m-old")
    assert denied.status_code == 403 and secret not in denied.text

    client.post("/api/kb/auth/logout")
    auditor = _role_user(store, "审计", ["进管理模块", "对话审计"], username="auditor")
    assert _login(client, auditor, "pw").status_code == 200
    opened = client.get("/api/kb/rounds/e-send/context/m-old")
    assert opened.status_code == 200 and opened.json()["message"]["content"] == secret
    missing = client.get("/api/kb/rounds/e-send/context/m-other")
    assert missing.status_code == 404 and secret not in missing.text
