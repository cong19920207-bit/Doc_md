# -*- coding: utf-8 -*-
from pathlib import Path

from fastapi.testclient import TestClient

from app.aliases import c20_display_name
from app import main


ROOT = Path(__file__).resolve().parents[3]
QA_JS = (ROOT / "site" / "feature-interaction" / "qa.js").read_text(encoding="utf-8")
QA_CSS = (ROOT / "site" / "feature-interaction" / "qa.css").read_text(encoding="utf-8")
QA_HTML = (ROOT / "site" / "feature-interaction" / "index.html").read_text(encoding="utf-8")
INIT_SQL = (ROOT / "site" / "kb-api" / "sql" / "init.sql").read_text(encoding="utf-8")
V3 = ROOT / "site" / "docs" / "design" / "kb-qa" / "PRD-知识问答-v3.md"

CHIP_FIXED = [
    (
        "币商用链接支付帮朋友充金币：付款人能拿 VIP 积分和拉新返利吗？收货人呢？这笔算不算收货人的首充？会不会进充值任务进度？",
        "币商用链接支付帮朋友充金币：付款人能拿 VIP 积分和拉新返利吗？收货人呢？这笔算不算收货人的首充？会不会进充值任务进度？",
    ),
    (
        "币商给用户转了 20000 金币。这笔会进 Billionaires 充值榜吗？算不算用户首充？会不会给用户加 VIP 财富值？",
        "币商给用户转了 20000 金币。这笔会进 Billionaires 充值榜吗？算不算用户首充？会不会给用户加 VIP 财富值？",
    ),
    (
        "非 VIP 在语聊房 Game Center 点 Bounty Racing 会怎样？如果这个房间同时开着 Ludo，我关掉数值游戏弹窗后，休闲游戏还在吗？Lord of Olympus 有 VIP 限制吗？",
        "非 VIP 在语聊房 Game Center 点 Bounty Racing 会怎样？如果这个房间同时开着 Ludo，我关掉数值游戏弹窗后，休闲游戏还在吗？Lord of Olympus 有 VIP 限制吗？",
    ),
    (
        "VIP 保级扣的是财富值还是金币？200 金币等于多少财富值？退款怎么扣？",
        "VIP 保级扣的是财富值还是金币？200 金币等于多少财富值？退款怎么扣？",
    ),
]


def test_init_sql_has_feedback_columns():
    assert "feedback VARCHAR(16) NULL" in INIT_SQL
    assert "feedback_at DATETIME(3) NULL" in INIT_SQL


def test_c20_vip_and_yallapay():
    assert c20_display_name("vip", ROOT) == "用户VIP"
    assert c20_display_name("yallapay", ROOT) == "链接支付"


def test_bind_fields_and_action_keys_in_js():
    for key in ("round_id", "logWritten", "query", "historySnapshot", "lastChunksSnapshot"):
        assert key in QA_JS
    assert "复制回答" in QA_JS
    assert 'label: "赞"' in QA_JS
    assert 'label: "踩"' in QA_JS
    assert 'label: "刷新"' in QA_JS
    assert "data-toggle-cite" in QA_JS
    assert "qa-cite-pane" in QA_HTML
    assert "qa-icon-btn" in QA_CSS
    assert 'toast("已复制回答")' in QA_JS
    assert 'toast("生成中…")' in QA_JS
    assert "本轮日志未写入，反馈不会进明细" in QA_JS
    assert 'freezeSnap: true' in QA_JS


def test_chip_fixed_and_send_path():
    for title, query in CHIP_FIXED:
        assert title == query
        assert title in QA_JS
        assert query in QA_JS
    assert "那退款呢" not in QA_JS.split("CHIP_FIXED")[1].split("];")[0]
    assert "data-qa-chip" in QA_JS
    assert "async function send(presetQuery)" in QA_JS


def test_content_col_and_composer():
    assert "max-width: 768px" in QA_CSS
    assert "padding: 0 24px" in QA_CSS
    assert "class=\"qa-col\"" in QA_HTML
    assert 'id="qaStage"' in QA_HTML
    assert QA_HTML.index("qa-col") < QA_HTML.index('id="qaStage"')
    assert QA_HTML.index('id="qaStage"') < QA_HTML.index('id="qaInput"')
    assert "qa-composer-bar" in QA_HTML
    assert 'id="qaInput"' in QA_HTML
    assert 'id="qaSend"' in QA_HTML
    assert 'id="qaCitePane"' in QA_HTML
    assert QA_HTML.index("qa-main") < QA_HTML.index("qaCitePane")


def test_rounds_overlay_has_feedback():
    assert "<p><b>反馈</b>" in QA_JS
    assert "<th>反馈</th>" in QA_JS
    assert "feedbackUiFromRow" in QA_JS


def test_v3_prd_untouched():
    text = V3.read_text(encoding="utf-8")
    assert "知识问答" in text


def test_feedback_api_write_clear_and_404(monkeypatch):
    store = {
        "r1": {
            "round_id": "r1",
            "feedback": None,
            "answer": "ok",
            "status": "success",
        }
    }

    async def _noop_index():
        return None

    def get_round(rid):
        row = store.get(rid)
        return dict(row) if row else None

    def set_feedback(rid, fb):
        if rid not in store:
            return "not_found"
        store[rid]["feedback"] = fb
        store[rid]["feedback_at"] = "t"
        return "ok"

    monkeypatch.setattr(main, "_startup_index", _noop_index)
    monkeypatch.setattr(main.logs, "ensure_feedback_columns", lambda: True)
    monkeypatch.setattr(main.logs, "get_round", get_round)
    monkeypatch.setattr(main.logs, "set_feedback", set_feedback)

    with TestClient(main.app) as client:
        login = client.post(
            "/api/kb/auth/login",
            json={"username": "admin", "password": "admin-test-pass"},
        )
        assert login.status_code == 200
        me_id = client.get("/api/kb/auth/me").json()["id"]
        store["r1"]["user_id"] = me_id
        up = client.post("/api/kb/rounds/r1/feedback", json={"feedback": "up"})
        assert up.status_code == 200
        assert up.json()["feedback"] == "up"
        cleared = client.post("/api/kb/rounds/r1/feedback", json={"feedback": None})
        assert cleared.status_code == 200
        assert cleared.json()["feedback"] is None
        missing = client.post("/api/kb/rounds/nope/feedback", json={"feedback": "up"})
        assert missing.status_code == 404
        bad = client.post("/api/kb/rounds/r1/feedback", json={"feedback": "sideways"})
        assert bad.status_code == 400
        # STEP-Q21：新记录（schema_ver≥2）只允许已保存且正常完成的回复；旧记录 r1 沿用原规则
        store["r2"] = {
            "round_id": "r2", "user_id": me_id, "status": "gen_fail",
            "schema_ver": 2, "msg_save": "saved", "assistant_msg_id": "m_x",
        }
        denied = client.post("/api/kb/rounds/r2/feedback", json={"feedback": "up"})
        assert denied.status_code == 409
        assert denied.json()["code"] == "feedback_not_allowed"
        store["r2"]["status"] = "success"
        assert client.post("/api/kb/rounds/r2/feedback", json={"feedback": "up"}).status_code == 200
