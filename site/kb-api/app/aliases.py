# -*- coding: utf-8 -*-
"""功能别名表：只允许仓库已有 feature_id，禁止发明。"""
from __future__ import annotations

import json
from pathlib import Path

from . import settings

# 常见口语别名。键必须是 prd/design 下已有目录名。
EXTRA_ALIASES: dict[str, list[str]] = {
    "vip": ["VIP", "vip", "用户VIP", "用户 VIP", "贵族"],
    "user-level": ["用户等级", "等级", "平台等级", "经验等级"],
    "referral": ["拉新", "邀请", "Share and Invite"],
    "admin": ["后台", "运营后台"],
    "auth-login": ["登录", "登录注册", "注册"],
    "merchant": ["币商", "代理转账", "币商代充"],
    "recharge": ["充值", "钱包充值", "首充"],
    "payout": ["提现", "积分提现"],
    "mall": ["商城", "靓号", "背包"],
    "room": ["房间"],
    "profile": ["个人中心", "资料", "绑手机"],
    "yallapay": ["YallaPay", "链接支付", "分销支付"],
    "coupon": ["体验券", "VIP体验券", "膨胀券", "福利券"],
    "room-game": ["Bounty Racing", "水果机", "动物机", "Game Center", "Lord of Olympus"],
    "casual-game": ["Ludo", "Carrom", "Block Crush", "休闲游戏"],
    "ranking": ["Billionaires", "充值榜", "排行榜"],
    "checkin-task": ["充值任务", "签到", "任务"],
}


_CACHE: dict[str, dict[str, list[str]]] = {}


def known_feature_ids(repo_root: Path | None = None) -> list[str]:
    root = repo_root or settings.REPO_ROOT
    design = root / "prd" / "design"
    if not design.is_dir():
        return sorted(EXTRA_ALIASES.keys())
    ids = [p.name for p in design.iterdir() if p.is_dir() and (p / "brief" / "current.md").exists()]
    return sorted(ids)


def load_aliases(repo_root: Path | None = None) -> dict[str, list[str]]:
    root = (repo_root or settings.REPO_ROOT).resolve()
    cache_key = str(root)
    cached = _CACHE.get(cache_key)
    if cached is not None:
        return cached
    ids = known_feature_ids(root)
    table: dict[str, list[str]] = {fid: [fid] for fid in ids}
    path = settings.ALIASES_PATH
    if path.exists():
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                for fid, names in raw.items():
                    if fid not in table:
                        continue
                    if isinstance(names, list):
                        table[fid].extend(str(x) for x in names if x)
        except (OSError, json.JSONDecodeError):
            pass
    for fid, names in EXTRA_ALIASES.items():
        if fid in table:
            table[fid].extend(names)
    for fid in list(table):
        seen: set[str] = set()
        cleaned: list[str] = []
        for name in table[fid]:
            key = str(name).strip()
            if not key or key.lower() in seen:
                continue
            seen.add(key.lower())
            cleaned.append(key)
        table[fid] = cleaned
    _CACHE[cache_key] = table
    return table


def format_alias_hint(repo_root: Path | None = None) -> str:
    """改写用户消息用的口语对照，不发明功能 ID。"""
    ids = known_feature_ids(repo_root)
    aliases = load_aliases(repo_root)
    lines: list[str] = []
    for fid in ids:
        names = [n for n in (aliases.get(fid) or [fid]) if n != fid]
        if names:
            lines.append(f"{fid}：{'、'.join(names)}")
        else:
            lines.append(fid)
    return "\n".join(lines)


def filter_named_ids(raw_ids: list[str] | None, repo_root: Path | None = None) -> list[str]:
    known = set(known_feature_ids(repo_root))
    out: list[str] = []
    seen: set[str] = set()
    for item in raw_ids or []:
        fid = str(item or "").strip()
        if fid in known and fid not in seen:
            seen.add(fid)
            out.append(fid)
    return out


def collection_for(feature_id: str) -> str:
    if feature_id == "admin":
        return settings.COLLECTION_ADMIN
    return settings.COLLECTION_CLIENT


def _has_han(text: str) -> bool:
    return any("\u4e00" <= ch <= "\u9fff" for ch in text)


def _json_alias_first(feature_id: str) -> str:
    """feature_aliases.json 中该 id 的第一项；读失败则空串。不改别名数据。"""
    path = settings.ALIASES_PATH
    if not path.exists():
        return ""
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ""
    if not isinstance(raw, dict):
        return ""
    names = raw.get(feature_id)
    if not isinstance(names, list):
        return ""
    for item in names:
        key = str(item or "").strip()
        if key:
            return key
    return ""


def c20_display_name(feature_id: str, repo_root: Path | None = None) -> str:
    """C20：合并去重列表第一条含汉字的别名；否则 JSON 第一项；否则 feature_id。"""
    fid = str(feature_id or "").strip()
    if not fid:
        return fid
    names = load_aliases(repo_root).get(fid) or []
    for name in names:
        if _has_han(str(name)):
            return str(name)
    json_first = _json_alias_first(fid)
    if json_first:
        return json_first
    return fid
