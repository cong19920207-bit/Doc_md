# -*- coding: utf-8 -*-
"""STEP-A15（G-ADM-E04）：运行概览。只用已记录的事实计算，每个指标带口径声明；未知单列，分母为 0 显示不适用。"""
from __future__ import annotations

import math
from typing import Any

HEAT_SCAN_LIMIT = 20000
SOURCE = "qa_rounds（执行记录）"
TIME_FIELD = "created_at（执行开始时间，UTC 存储）"
ACCEPTED = "已接受执行：有 schema_ver 且有逻辑回合；被拒请求（忙碌、重复、未找到、提问未保存）不计"
LEGACY = "旧记录（无 schema_ver）无法映射，单列 legacy_rows，不计入各指标"
NOT_CONNECTED = "未接入"


def _ratio(num: int, den: int) -> dict:
    return {
        "numerator": num,
        "denominator": den,
        "value": round(num / den, 4) if den else None,
        "display": f"{num / den * 100:.1f}%" if den else "不适用",
    }


def _percentile(sorted_vals: list[float], p: float) -> float | None:
    if not sorted_vals:
        return None
    k = (len(sorted_vals) - 1) * p
    lo, hi = math.floor(k), math.ceil(k)
    if lo == hi:
        return round(sorted_vals[int(k)], 1)
    return round(sorted_vals[lo] + (sorted_vals[hi] - sorted_vals[lo]) * (k - lo), 1)


def _metric(key: str, label: str, value: Any, unit: str, rule: str, **extra: Any) -> dict:
    out = {"key": key, "label": label, "value": value, "unit": unit, "rule": rule,
           "source": SOURCE, "time_field": TIME_FIELD}
    out.update(extra)
    return out


def compose(counts: dict, heat: dict) -> dict:
    """counts 来自 LogStore.overview_counts（SQL 聚合）；heat 来自 compute_heat。"""
    c = counts
    terminal = {k: v for k, v in (c.get("exec_state") or {}).items() if k in ("completed", "failed", "interrupted")}
    running = int((c.get("exec_state") or {}).get("running", 0))
    state_unknown = int((c.get("exec_state") or {}).get(None, 0))
    abnormal = int(terminal.get("failed", 0)) + int(terminal.get("interrupted", 0))
    durations = sorted(float(x) for x in (c.get("durations_ms") or []))
    biz = dict(c.get("biz") or {})
    biz_unknown = int(biz.pop(None, 0))
    route = dict(c.get("route") or {})
    route_unrecorded = int(route.pop(None, 0))
    fb_up, fb_down, queue = int(c.get("fb_up", 0)), int(c.get("fb_down", 0)), int(c.get("fb_queue", 0))

    usage = [
        _metric("active_accounts", "活跃提问账号", c.get("active_accounts", 0), "个账号",
                "范围内至少有一个新逻辑回合的去重账号；仅刷新或被拒请求不算"),
        _metric("new_rounds", "新逻辑回合", c.get("new_rounds", 0), "个回合",
                "操作类型为发送的已接受执行去重逻辑回合；刷新不增加，网络重传不重复计"),
        _metric("executions", "执行次数", c.get("execs", 0), "次",
                ACCEPTED + "；含主动刷新", rejected=c.get("rejected", 0)),
        _metric("refreshes", "主动刷新", c.get("refresh", 0), "次",
                "已接受执行中操作类型为刷新的数量", unknown=c.get("op_unknown", 0)),
        _metric("knowledge_calls", "实际调用 Knowledge 的执行", c.get("kn_yes", 0), "次",
                "有真实知识检索调用标记的执行；只看 Route 不算",
                not_called=c.get("kn_no", 0), unknown=c.get("kn_unknown", 0)),
        _metric("route", "Route 分布", route, "次", "已保存的原始 Router 分类", unrecorded=route_unrecorded),
        _metric("memory_calls", "实际 Memory 调用", (c.get('calls') or {}).get('memory'), "次",
                '已记录 call_usage.memory 的合计；缺字段为未知',
                status='recorded' if 'calls' in c else 'not_connected'),
    ]
    results = [
        _metric("biz_result", "业务结果分布", biz, "次", "已结束执行的业务结果", unknown=biz_unknown),
        _metric("exec_error_rate", "执行异常率", _ratio(abnormal, sum(int(v) for v in terminal.values())), "比例",
                "异常结束（failed、interrupted）÷ 已知终态的已结束执行；运行中与终态未知不进分母",
                breakdown=terminal, running=running, unknown=state_unknown),
        _metric("msg_save_fail_rate", "消息保存失败率",
                _ratio(int(c.get("ms_failed_final", 0)), int(c.get("ms_saved", 0)) + int(c.get("ms_failed_final", 0))),
                "比例", "最终保存失败 ÷（已保存 + 最终保存失败）；待补写、未发生保存、未知单列",
                pending_retry=c.get("ms_failed_pending", 0), pending=c.get("ms_pending", 0),
                not_applicable=c.get("ms_na", 0), unknown=c.get("ms_unknown", 0)),
        _metric("runtime_incomplete", "Runtime 不完整记录", c.get("rt_partial", 0), "条",
                "终态更新未写入、停在 partial 的执行；是可观察下限，Runtime 整行写失败另见健康与异常"),
        _metric("evidence_check", "证据检查", c.get('checks'), "次", '已记录 check_status 分布；空值单列未知',
                status='recorded' if 'checks' in c else 'not_connected'),
        _metric("duration", "执行耗时", {
            "samples": len(durations),
            "mean_ms": round(sum(durations) / len(durations), 1) if durations else None,
            "p50_ms": _percentile(durations, 0.5),
            "p95_ms": _percentile(durations, 0.95),
        }, "毫秒", "finished_at − created_at；只算已结束且有终态时间的执行", unknown=c.get("dur_unknown", 0)),
        _metric("model_usage", "模型/工具用量", c.get('calls'), "次调用", '已记录 call_usage 合计；缺字段为未知。供应商 token 用量未记录',
                status='recorded' if 'calls' in c else 'not_connected'),
    ]
    feedback = [
        _metric("feedback_coverage", "评价覆盖率", _ratio(fb_up + fb_down, queue), "比例",
                "有赞或踩的版本 ÷ 可评价版本（范围内生成、已保存、正常完成的回复；按执行开始时间）"),
        _metric("feedback_up_ratio", "已评价赞占比", _ratio(fb_up, fb_up + fb_down), "比例",
                "赞 ÷（赞 + 踩）；分母为 0 显示不适用", up=fb_up, down=fb_down, unrated=max(0, queue - fb_up - fb_down)),
    ]
    return {
        "sections": [
            {"key": "usage", "label": "使用与执行量", "metrics": usage},
            {"key": "results", "label": "结果、异常与耗时", "metrics": results},
            {"key": "feedback", "label": "反馈概览", "metrics": feedback,
             "note": "按回复生成（执行开始）时间的版本队列；与反馈列表按反馈时间筛选是两种口径，不混算"},
        ],
        "heat": heat,
        "legacy_rows": c.get("legacy_rows", 0),
        "legacy_note": LEGACY,
        "total_rows": c.get("total", 0),
    }


def compute_heat(rows: list[dict], limit: int = HEAT_SCAN_LIMIT) -> dict:
    """新热度：只统计实际调用 Knowledge 的执行，同一执行同功能只 +1；资格或生成集未知单列；旧口径分开。"""
    window = rows[:limit]
    complete = len(rows) <= limit
    counts: dict[str, int] = {}
    legacy: dict[str, int] = {}
    unclassified = unknown_qualify = unknown_cgen = legacy_rows = legacy_unclassified = 0
    for r in window:
        feats: list[str] = []
        seen: set[str] = set()
        for block in r.get("c_gen") or []:
            fid = (block or {}).get("feature_id")
            if fid and fid not in seen:
                seen.add(fid)
                feats.append(fid)
        if not r.get("schema_ver"):
            legacy_rows += 1
            if not feats:
                legacy_unclassified += 1
            for f in feats:
                legacy[f] = legacy.get(f, 0) + 1
            continue
        used = r.get("used_knowledge_rag")
        if used is None:
            unknown_qualify += 1
            continue
        if not used:
            continue
        if r.get("c_gen") is None:
            unknown_cgen += 1
            continue
        if not feats:
            unclassified += 1
            continue
        for f in feats:
            counts[f] = counts.get(f, 0) + 1
    rank = lambda d: sorted(({"feature_id": k, "count": v} for k, v in d.items()),  # noqa: E731
                            key=lambda x: (-x["count"], x["feature_id"]))
    times = [r.get("created_at") for r in window if r.get("created_at") is not None]
    return {
        "items": rank(counts),
        "unclassified": unclassified,
        "unknown_qualification": unknown_qualify,
        "unknown_c_gen": unknown_cgen,
        "legacy": {"items": rank(legacy), "rows": legacy_rows, "unclassified": legacy_unclassified,
                   "note": "旧口径：无实际调用标记，全部计入；与新口径不合算"},
        "coverage": {
            "complete": complete,
            "scanned": len(window),
            "limit": limit,
            "window_start": str(min(times)) if times else None,
            "window_end": str(max(times)) if times else None,
            "note": "" if complete else f"范围内超过 {limit} 条执行，只统计最近 {limit} 条，见实际窗口",
        },
        "rule": "只统计实际调用 Knowledge RAG 的执行；同一执行 c_gen 中功能去重各 +1；生成集记录完整且无功能才计未归类",
        "version": "heat-v2",
    }
