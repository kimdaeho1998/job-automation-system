"""Reminder generation service."""

from __future__ import annotations

from logging import Logger
from typing import TypedDict

from app.config import Settings
from app.services.notion_service import NotionScheduleItem
from app.utils.date_utils import (
    calculate_days_until,
    format_dday_label,
    now_local,
    parse_date_string,
    to_date_string,
)


class ReminderItem(TypedDict):
    title: str
    date: str
    status: str
    d_day: str


class ReminderService:
    """Builds reminder payloads for daily job-prep tasks."""

    def __init__(self, settings: Settings, logger: Logger) -> None:
        self.settings = settings
        self.logger = logger

    def filter_reminder_targets(
        self,
        schedules: list[NotionScheduleItem],
    ) -> list[ReminderItem]:
        reminders: list[ReminderItem] = []

        for schedule in schedules:
            schedule_date = schedule.get("date")
            if not schedule_date:
                continue

            try:
                days_until = calculate_days_until(parse_date_string(schedule_date))
            except ValueError:
                self.logger.warning(
                    "Skipping schedule with invalid date format: title=%s date=%s",
                    schedule.get("title", ""),
                    schedule_date,
                )
                continue

            d_day = format_dday_label(days_until)
            if d_day is None:
                continue

            reminders.append(
                ReminderItem(
                    title=schedule.get("title") or "제목 없음",
                    date=schedule_date,
                    status=schedule.get("status") or "상태 없음",
                    d_day=d_day,
                )
            )

        self.logger.info("Filtered %s reminder target(s)", len(reminders))
        return sorted(reminders, key=lambda item: item["date"])

    def format_reminders_for_console(
        self,
        reminders: list[ReminderItem],
    ) -> str:
        if not reminders:
            return "알림 대상 일정이 없습니다."

        lines = ["알림 대상 일정", "-" * 52]
        for reminder in reminders:
            lines.append(
                f"[{reminder['d_day']:<5}] {reminder['date']} | {reminder['status']:<10} | {reminder['title']}"
            )
        return "\n".join(lines)

    def build_daily_reminders(self) -> list[dict[str, str]]:
        reminder = {
            "title": "오늘 지원 현황 점검",
            "scheduled_for": f"{to_date_string(now_local())} {self.settings.reminder_hour:02d}:00",
            "channel": "notion",
        }
        self.logger.info("Built %s reminder", 1)
        return [reminder]
