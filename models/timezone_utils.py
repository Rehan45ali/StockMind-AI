from __future__ import annotations

from datetime import timedelta, timezone, tzinfo
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def get_ist_timezone() -> tzinfo:
    try:
        return ZoneInfo("Asia/Kolkata")
    except ZoneInfoNotFoundError:
        # Kolkata does not observe DST, so a fixed UTC+05:30 offset is a safe fallback.
        return timezone(timedelta(hours=5, minutes=30), name="Asia/Kolkata")


IST = get_ist_timezone()
