"""Date utility helpers."""

from __future__ import annotations

from datetime import date, datetime


def now_local() -> datetime:
    return datetime.now()


def to_date_string(value: datetime) -> str:
    return value.strftime("%Y-%m-%d")


def today_local() -> date:
    return now_local().date()


def parse_date_string(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def calculate_days_until(target_date: date, base_date: date | None = None) -> int:
    reference_date = base_date or today_local()
    return (target_date - reference_date).days


def format_dday_label(days_until: int) -> str | None:
    reminder_map = {
        7: "D-7",
        3: "D-3",
        1: "D-1",
        0: "D-day",
    }
    return reminder_map.get(days_until)
