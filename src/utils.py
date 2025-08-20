"""
Shared utilities: time conversions, logging, backoff.
"""
from __future__ import annotations

import time
import math
import sys
import logging
from typing import Optional
from datetime import datetime, timezone

def setup_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        stream=sys.stdout,
    )

def to_millis(dt_or_str) -> int:
    """Convert datetime or ISO string to milliseconds since epoch (UTC)."""
    if isinstance(dt_or_str, (int, float)):
        # assume already ms
        return int(dt_or_str)
    if isinstance(dt_or_str, datetime):
        if dt_or_str.tzinfo is None:
            dt_or_str = dt_or_str.replace(tzinfo=timezone.utc)
        return int(dt_or_str.timestamp() * 1000)
    # parse string
    d = datetime.fromisoformat(str(dt_or_str))
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    return int(d.timestamp() * 1000)

def from_millis(ms: int) -> datetime:
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc)

def sleep_backoff(attempt: int, base: float = 1.0, cap: float = 30.0) -> None:
    """Exponential backoff with jitter."""
    sleep = min(cap, base * (2 ** attempt))
    # jitter: +/- 20%
    jitter = sleep * 0.2
    time.sleep(max(0.0, sleep - jitter))

def floor_to_day(ms: int) -> int:
    """Floor a millisecond timestamp to 00:00 UTC of that day."""
    dt = from_millis(ms).replace(hour=0, minute=0, second=0, microsecond=0)
    return to_millis(dt)

def ceil_to_day(ms: int) -> int:
    dt = from_millis(ms).replace(hour=0, minute=0, second=0, microsecond=0)
    return to_millis(dt) + 24 * 60 * 60 * 1000
