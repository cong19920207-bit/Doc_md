# -*- coding: utf-8 -*-
from app.bm25 import Bm25Index, rrf_merge
from app.logs import LogStore


def test_bm25_chinese_and_rrf():
    idx = Bm25Index()
    idx.add("a", "保级扣的是财富值还是金币", {"feature_id": "vip", "collection": "hayyo-client"})
    idx.add("b", "拉新后台奖励组字段", {"feature_id": "admin", "collection": "hayyo-admin"})
    hits = idx.search("财富值保级", 5)
    assert hits and hits[0][0] == "a"
    merged = rrf_merge([["a", "b"], ["b", "a"]], 2)
    assert set(merged) == {"a", "b"}


def test_heatmap_c34():
    rows = [
        {"c_gen": [{"feature_id": "vip"}, {"feature_id": "vip"}, {"feature_id": "referral"}]},
        {"c_gen": [{"feature_id": "vip"}]},
        {"c_gen": []},
        {"c_gen": [{"feature_id": "user-level"}]},
    ]
    counts = {}
    unclassified = 0
    for row in rows:
        feats = LogStore._hit_features(row)
        if not feats:
            unclassified += 1
            continue
        for fid in feats:
            counts[fid] = counts.get(fid, 0) + 1
    ranked = sorted(counts.items(), key=lambda x: (-x[1], x[0]))
    assert unclassified == 1
    assert ranked[0] == ("vip", 2)
    assert ("referral", 1) in ranked
    assert ("user-level", 1) in ranked
    # STEP-Q21：旧记录（无 schema_ver）按旧口径计入，结果与原算法一致并单列旧口径数量
    agg = LogStore.aggregate_heat(rows)
    assert [(i["feature_id"], i["count"]) for i in agg["items"]] == ranked
    assert agg["unclassified"] == 1 and agg["legacy_rows"] == 4
    assert all(i["count"] == i["legacy_count"] for i in agg["items"])
    # 新记录未实际调用 Knowledge RAG：不进热度、不加未归类
    skipped = LogStore.aggregate_heat([{"schema_ver": 2, "used_knowledge_rag": 0, "c_gen": []}])
    assert skipped["items"] == [] and skipped["unclassified"] == 0
    # 空路不计：点名 referral 但 c_gen 无该功能
    empty_lane_round = {"c_gen": [{"feature_id": "vip"}], "lanes": [{"feature_id": "referral", "count": 0, "empty": True}]}
    assert "referral" not in LogStore._hit_features(empty_lane_round)
