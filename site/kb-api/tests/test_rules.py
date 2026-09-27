# -*- coding: utf-8 -*-
from pathlib import Path

from app.aliases import filter_named_ids, load_aliases
from app.chunking import parse_brief, scan_briefs
from app.pipeline import (
    Pipeline,
    apply_floor,
    build_rewrite_user,
    fill_block_content,
    numbers_ok,
    parse_rewrite,
    post_check_answer,
)
from app.util import NUMBER_LEAK_NOTE, excerpt, extract_numbers, truncate18


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def test_truncate18():
    assert truncate18("保级扣的是财富值还是金币") == "保级扣的是财富值还是金币"[:18]
    long = "这是一句超过十八个字的标题用于验收截断"
    assert truncate18(long) == long[:18]
    assert len(truncate18(long)) == 18


def test_chunk_default_only_and_vip_brief():
    root = repo_root()
    vip = root / "prd" / "design" / "vip" / "brief" / "current.md"
    chunks = parse_brief(vip, root, "vip")
    ids = {c.chunk_id for c in chunks}
    assert "vip.logic-wealth" in ids
    assert "vip.scope" in ids
    for c in chunks:
        assert c.collection == "hayyo-client"
        assert c.path == "prd/design/vip/brief/current.md"
        assert c.payload()["user_id"] == ""
        assert c.payload()["owner_id"] == ""
        assert c.payload()["tenant_id"] == ""
        assert c.payload()["role"] == ""


def test_skip_chunk_no_and_admin_collection():
    root = repo_root()
    chunks = parse_brief(root / "prd" / "design" / "admin" / "brief" / "current.md", root, "admin")
    assert chunks
    assert all(c.collection == "hayyo-admin" for c in chunks)
    src = (root / "prd" / "design" / "admin" / "brief" / "current.md").read_text(encoding="utf-8")
    assert "chunk:no" in src
    assert all("元信息" not in (c.heading or "") for c in chunks)


def test_scan_all_briefs():
    chunks = scan_briefs(repo_root())
    assert len(chunks) > 20
    assert any(c.chunk_id == "user-level.scope" for c in chunks)
    assert any(c.chunk_id == "referral.scope" for c in chunks)


def test_oversized_flag():
    from app.chunking import Chunk
    from app import settings
    c = Chunk(
        path="x.md", feature_id="vip", chunk_id="x", section="", heading="", anchor="",
        content="汉" * (settings.EMBED_TOKEN_LIMIT + 1), content_hash="a",
        collection="hayyo-client", token_estimate=settings.EMBED_TOKEN_LIMIT + 1, oversized=True,
    )
    assert c.oversized


def test_filter_named_ids_no_invent():
    got = filter_named_ids(["vip", "not-a-feature", "user-level", "vip"], repo_root())
    assert got == ["vip", "user-level"]


def test_parse_rewrite_filters_ids():
    raw = '{"rewrite_query":"那退款怎么扣财富值","same_topic":true,"named_feature_ids":["vip","invented"]}'
    parsed = parse_rewrite(raw)
    assert parsed["same_topic"] is True
    assert parsed["rewrite_query"]
    assert "invented" not in parsed["named_feature_ids"]
    assert "vip" in parsed["named_feature_ids"]


def test_apply_floor_multi_intent():
    pool = [
        {"path": "a", "chunk_id": "r1", "feature_id": "referral"},
        {"path": "a", "chunk_id": "r2", "feature_id": "referral"},
        {"path": "v", "chunk_id": "v1", "feature_id": "vip"},
        {"path": "u", "chunk_id": "u1", "feature_id": "user-level"},
    ]
    named = ["user-level", "vip", "referral"]
    picked = apply_floor(pool, named, n=2)
    assert len(picked) == 3
    feats = {b["feature_id"] for b in picked}
    assert feats == {"user-level", "vip", "referral"}


def test_numbers_subset():
    blocks = [{"content": "比例 200 金币 = 1 财富值。退款 3 财富值。"}]
    assert numbers_ok("按 200 金币计 1 财富值", blocks)
    assert not numbers_ok("保级线是 99999", blocks)
    assert numbers_ok("文档未写", [])
    assert extract_numbers("VIP11") == {"11"}
    assert excerpt("x" * 600) == "x" * 500
    # 千分位与问句复述、出处序号不得误杀。
    assert extract_numbers("每次最少转账10,000") == {"10000"}
    assert numbers_ok("出处 vip.logic-pretty [2] 块3", blocks)
    assert numbers_ok("这笔 20000 金币是否计榜", [{"content": "最低 10,000"}], original="转了 20000 金币")
    assert not numbers_ok("保级线是 99999", blocks, original="VIP 保级扣什么")


def test_post_check_keeps_success_when_main_answer_exists():
    """主问题已从生成集作答时，附带未写声明不整轮拒答。"""
    blocks = [{"content": "VIP1：标识、发图片、金色昵称。观众人数本版不做。"}]
    text = (
        "VIP 的权益按原文归属如下：VIP1 标识、发图片、金色昵称。"
        "观众人数本版不做。\n"
        "文档未写：各等级财富值档位数字（原文未给出各等级财富表，不编造）。"
    )
    checked = post_check_answer(text, blocks)
    assert checked["refused"] is False
    assert "VIP1" in checked["text"]
    assert "文档未写" in checked["text"]


def test_post_check_refuses_empty_rerank_wording():
    checked = post_check_answer("文档未写。重排后 0 块，系统拒答。", [])
    assert checked["refused"] is True
    assert checked["text"].startswith("文档未写")


def test_post_check_keeps_text_on_leaked_numbers():
    blocks = [{"content": "比例 200 金币 = 1 财富值。"}]
    checked = post_check_answer("保级线是 99999。按 200 计。", blocks)
    assert checked["refused"] is True
    assert "保级线是 99999" in checked["text"]
    assert NUMBER_LEAK_NOTE in checked["text"]
    assert not checked["text"].startswith("文档未写这些具体数字")


def test_legacy_system_prompt_migrates(tmp_path):
    import json
    from app import settings
    from app.config_store import ConfigStore

    path = tmp_path / "kb-config.json"
    path.write_text(
        json.dumps({"recall_k": 32, "system_prompt": settings.LEGACY_SYSTEM_PROMPT}, ensure_ascii=False),
        encoding="utf-8",
    )
    store = ConfigStore(path)
    assert store.data["system_prompt"] == settings.SYSTEM_PROMPT
    assert store.data["recall_k"] == 32
    saved = json.loads(path.read_text(encoding="utf-8"))
    assert saved["system_prompt"] == settings.SYSTEM_PROMPT
    assert "先回答用户本轮问到的点" in settings.SYSTEM_PROMPT
    assert settings.SYSTEM_PROMPT != settings.LEGACY_SYSTEM_PROMPT
    assert "宁多勿漏" in settings.REWRITE_PROMPT
    assert "chunk_id" in settings.SYSTEM_PROMPT


def test_legacy_v2_and_rewrite_prompts_migrate(tmp_path):
    import json
    from app import settings
    from app.config_store import ConfigStore

    path = tmp_path / "kb-config.json"
    path.write_text(
        json.dumps(
            {
                "recall_k": 32,
                "system_prompt": settings.LEGACY_SYSTEM_PROMPT_V2,
                "rewrite_prompt": settings.LEGACY_REWRITE_PROMPT,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    store = ConfigStore(path)
    assert store.data["system_prompt"] == settings.SYSTEM_PROMPT
    assert store.data["rewrite_prompt"] == settings.REWRITE_PROMPT
    assert store.data["recall_k"] == 32
    saved = json.loads(path.read_text(encoding="utf-8"))
    assert saved["system_prompt"] == settings.SYSTEM_PROMPT
    assert saved["rewrite_prompt"] == settings.REWRITE_PROMPT


def test_aliases_cover_link_pay_and_rewrite_user():
    root = repo_root()
    table = load_aliases(root)
    assert "链接支付" in table.get("yallapay", [])
    assert "体验券" in table.get("coupon", [])
    assert "Bounty Racing" in table.get("room-game", [])
    user = build_rewrite_user("币商用链接支付帮朋友充金币", [], root)
    assert "yallapay" in user
    assert "链接支付" in user
    assert "口语→功能 ID" in user


def test_generate_messages_uses_chunk_id_not_index():
    pipe = Pipeline(store=None, models=None, config_getter=lambda: {})
    msgs = pipe.generate_messages(
        "VIP 一共多少级？",
        {"rewrite_query": "VIP 一共多少级？", "named_feature_ids": ["vip"]},
        [{
            "path": "prd/design/vip/brief/current.md",
            "chunk_id": "vip.logic-pretty",
            "feature_id": "vip",
            "collection": "hayyo-client",
            "anchor": "logic-pretty",
            "content": "靓号共十级。",
        }],
        {},
    )
    body = msgs[1]["content"]
    assert "chunk_id=vip.logic-pretty" in body
    assert "[1]" not in body


class _MemStore:
    def __init__(self, items):
        self._items = {(b["path"], b["chunk_id"]): dict(b) for b in items}

    def lookup_payload(self, path, chunk_id):
        found = self._items.get((path, chunk_id))
        return dict(found) if found else None


class _CaptureRerank:
    def __init__(self):
        self.docs = None

    async def rerank(self, query, documents, top_n):
        self.docs = list(documents)
        return list(range(min(top_n, len(documents))))


def test_fill_block_content_from_store_then_excerpt():
    public = {
        "path": "prd/design/vip/brief/current.md",
        "chunk_id": "vip.logic-wealth",
        "feature_id": "vip",
        "excerpt": "比例 200 金币 = 1 财富值。",
    }
    store = _MemStore([{
        "path": "prd/design/vip/brief/current.md",
        "chunk_id": "vip.logic-wealth",
        "feature_id": "vip",
        "content": "VIP 是基于付费贡献的保级身份。比例 200 金币 = 1 财富值。",
    }])
    filled = fill_block_content(public, store)
    assert filled is not None
    assert "保级身份" in filled["content"]
    excerpt_only = fill_block_content(public, store=None)
    assert excerpt_only is not None
    assert excerpt_only["content"] == "比例 200 金币 = 1 财富值。"
    assert fill_block_content({"path": "gone.md", "chunk_id": "x"}) is None
    kept = fill_block_content({"path": "a", "chunk_id": "b", "content": " 已有正文 "})
    assert kept["content"] == "已有正文"


def test_rerank_hydrates_last_chunks_and_skips_empty():
    import asyncio

    models = _CaptureRerank()
    store = _MemStore([{
        "path": "prd/design/vip/brief/current.md",
        "chunk_id": "vip.logic-cycle",
        "feature_id": "vip",
        "content": "退款：按 200 退款金币 = 3 财富值扣除。",
    }])
    pipe = Pipeline(store=store, models=models, config_getter=lambda: {"rerank_n": 8})
    candidates = [{
        "path": "prd/design/vip/brief/current.md",
        "chunk_id": "vip.logic-wealth",
        "feature_id": "vip",
        "content": "比例 200 金币 = 1 财富值。",
    }]
    prev = [
        {
            "path": "prd/design/vip/brief/current.md",
            "chunk_id": "vip.logic-cycle",
            "feature_id": "vip",
            "excerpt": "退款按 200 退款金币 = 3 财富值扣除。",
        },
        {"path": "gone.md", "chunk_id": "missing"},
        {"path": "", "chunk_id": "", "content": ""},
    ]
    out = asyncio.run(pipe.rerank("VIP 一共多少级？", candidates, ["vip"], prev, True, {"rerank_n": 8}))
    assert models.docs is not None
    assert all(str(d).strip() for d in models.docs)
    assert any("3 财富值" in d for d in models.docs)
    ids = {b["chunk_id"] for b in out}
    assert "vip.logic-wealth" in ids
    assert "vip.logic-cycle" in ids
    assert "missing" not in ids


def test_rerank_skips_prev_when_not_same_topic():
    import asyncio

    models = _CaptureRerank()
    store = _MemStore([{
        "path": "prd/design/vip/brief/current.md",
        "chunk_id": "vip.logic-cycle",
        "content": "退款：按 200 退款金币 = 3 财富值扣除。",
    }])
    pipe = Pipeline(store=store, models=models, config_getter=lambda: {"rerank_n": 8})
    candidates = [{
        "path": "prd/design/referral/brief/current.md",
        "chunk_id": "referral.scope",
        "content": "拉新默认不开通。",
    }]
    prev = [{
        "path": "prd/design/vip/brief/current.md",
        "chunk_id": "vip.logic-cycle",
        "excerpt": "退款：按 200 退款金币 = 3 财富值扣除。",
    }]
    out = asyncio.run(pipe.rerank("拉新怎么开通", candidates, ["referral"], prev, False, {"rerank_n": 8}))
    assert models.docs == ["拉新默认不开通。"]
    assert [b["chunk_id"] for b in out] == ["referral.scope"]
