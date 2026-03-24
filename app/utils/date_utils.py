"""Date utility helpers."""

from __future__ import annotations

from datetime import datetime


def now_local() -> datetime:
    return datetime.now()


def to_date_string(value: datetime) -> str:
    return value.strftime("%Y-%m-%d")
