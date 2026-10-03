# -*- coding: utf-8 -*-
"""G-ADM-E01：管理列表公共约定——游标分页、响应结构、错误格式。"""
from __future__ import annotations

import base64
import json
from datetime import date, datetime, time, timedelta, timezone
from typing import Any, Callable

from fastapi.responses import JSONResponse

from . import settings

ERROR_CODES = {
    400: "invalid_request",
    401: "unauthorized",
    403: "forbidden",
    404: "not_found",
    409: "conflict",
    503: "unavailable",
}


class BadCursor(ValueError):
    """游标无法解析。"""


def time_key(value: Any) -> str:
    """统一时间排序键：datetime 与字符串都转成同一格式，保证字典序即时间序。"""
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S.%f")
    text = str(value or "")
    if len(text) == 19:
        return text + ".000000"
    if "." in text:
        head, frac = text.split(".", 1)
        return head + "." + (frac + "000000")[:6]
    return text


def encode_cursor(ts: Any, oid: Any) -> str:
    raw = json.dumps([time_key(ts), str(oid or "")], ensure_ascii=False).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def decode_cursor(cursor: str | None) -> tuple[str, str] | None:
    if not cursor:
        return None
    try:
        pad = "=" * (-len(cursor) % 4)
        data = json.loads(base64.urlsafe_b64decode(cursor + pad).decode("utf-8"))
        ts, oid = data
        return str(ts), str(oid)
    except Exception as exc:  # noqa: BLE001
        raise BadCursor("游标无效") from exc


def page_size(raw: Any, default: int | None = None) -> int:
    base = int(default or settings.ADMIN_PAGE_SIZE)
    try:
        n = int(raw) if raw not in (None, "") else base
    except (TypeError, ValueError):
        n = base
    return max(1, min(n, int(settings.ADMIN_PAGE_MAX)))


def envelope(
    items: list[dict],
    *,
    next_cursor: str | None,
    has_more: bool,
    time_field: str,
    total: int | None = None,
    complete: bool = True,
    note: str = "",
    **extra: Any,
) -> dict:
    out = {
        "items": items,
        "next_cursor": next_cursor,
        "has_more": bool(has_more),
        "total": total,
        "coverage": {"complete": bool(complete), "note": note},
        "data_cutoff": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "time_field": time_field,
        "stored_tz": "UTC",
        "tz": settings.DISPLAY_TZ,
    }
    out.update(extra)
    return out


def paginate(
    rows: list[dict],
    *,
    ts_of: Callable[[dict], Any],
    id_of: Callable[[dict], Any],
    cursor: str | None,
    size: int,
) -> tuple[list[dict], str | None, bool]:
    """内存分页：按时间倒序、id 倒序，取游标之后的一页。"""
    after = decode_cursor(cursor)
    keyed = sorted(rows, key=lambda r: (time_key(ts_of(r)), str(id_of(r) or "")), reverse=True)
    if after:
        keyed = [r for r in keyed if (time_key(ts_of(r)), str(id_of(r) or "")) < after]
    page = keyed[:size]
    has_more = len(keyed) > size
    nxt = encode_cursor(ts_of(page[-1]), id_of(page[-1])) if has_more and page else None
    return page, nxt, has_more


class BadRange(ValueError):
    """时间范围不合法或超出上限。"""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def display_tz():
    """显示时区；容器缺时区库时上海按固定 +8，其余按 UTC。"""
    try:
        from zoneinfo import ZoneInfo

        return ZoneInfo(settings.DISPLAY_TZ)
    except Exception:  # noqa: BLE001
        if settings.DISPLAY_TZ == "Asia/Shanghai":
            return timezone(timedelta(hours=8))
        return timezone.utc


def _fmt_utc(value: datetime) -> str:
    return value.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]


def day_range(
    since: str | None,
    until: str | None,
    *,
    default_days: int | None = None,
    max_days: int | None = None,
) -> dict | None:
    """按显示时区的自然日解析 [since, until]（含首尾），换成 UTC 半开区间。
    两者都空且无默认天数时返回 None（不按时间筛选）。"""
    since = str(since or "").strip()
    until = str(until or "").strip()
    if not since and not until and not default_days:
        return None
    tz = display_tz()
    try:
        end_day = date.fromisoformat(until) if until else datetime.now(tz).date()
        if since:
            start_day = date.fromisoformat(since)
        else:
            start_day = end_day - timedelta(days=max(1, int(default_days or 1)) - 1)
    except ValueError as exc:
        raise BadRange("invalid_range", "日期格式应为 YYYY-MM-DD") from exc
    if start_day > end_day:
        raise BadRange("invalid_range", "开始日期晚于结束日期")
    days = (end_day - start_day).days + 1
    if max_days and days > max_days:
        raise BadRange("range_too_large", f"时间范围最长 {max_days} 天")
    start = datetime.combine(start_day, time.min, tz).astimezone(timezone.utc).replace(tzinfo=None)
    end = datetime.combine(end_day + timedelta(days=1), time.min, tz).astimezone(timezone.utc).replace(tzinfo=None)
    return {
        "since": start_day.isoformat(),
        "until": end_day.isoformat(),
        "days": days,
        "tz": settings.DISPLAY_TZ,
        "start": start,
        "end": end,
        "start_utc": _fmt_utc(start),
        "end_utc": _fmt_utc(end),
    }


def public_range(rng: dict | None) -> dict | None:
    if not rng:
        return None
    return {k: rng[k] for k in ("since", "until", "days", "tz", "start_utc", "end_utc")}


def like_arg(q: str) -> str:
    """LIKE 包含匹配：转义 % _ \\，按字面查找。"""
    text = str(q or "").replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{text}%"


def error(status: int, message: str, code: str | None = None, **extra: Any) -> JSONResponse:
    body = {"ok": False, "code": code or ERROR_CODES.get(status, "error"), "message": message}
    body.update(extra)
    return JSONResponse(body, status_code=status)
