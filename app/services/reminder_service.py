"""Reminder generation service."""

from __future__ import annotations

from logging import Logger

from app.config import Settings
from app.utils.date_utils import now_local, to_date_string


class ReminderService:
    """Builds reminder payloads for daily job-prep tasks."""

    def __init__(self, settings: Settings, logger: Logger) -> None:
        self.settings = settings
        self.logger = logger

    def build_daily_reminders(self) -> list[dict[str, str]]:
        reminder = {
            "title": "오늘 지원 현황 점검",
            "scheduled_for": f"{to_date_string(now_local())} {self.settings.reminder_hour:02d}:00",
            "channel": "notion",
        }
        self.logger.info("Built %s reminder", 1)
        return [reminder]
