"""The user's local calendar day. Timestamps stay UTC; file names and "today" use local time."""
from __future__ import annotations

import os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

TZ = ZoneInfo(os.environ.get("AI_SECRETARY_TZ", "Asia/Taipei"))


def local_day(now: datetime | None = None) -> str:
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    return now.astimezone(TZ).strftime("%Y-%m-%d")
