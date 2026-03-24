"""Lightweight Notion integration placeholder."""

from __future__ import annotations

from logging import Logger
from typing import Any

from app.config import Settings


class NotionService:
    """Handles dashboard sync operations for Notion."""

    def __init__(self, settings: Settings, logger: Logger) -> None:
        self.settings = settings
        self.logger = logger

    def sync_dashboard(
        self,
        jobs: list[dict[str, Any]],
        recommendations: list[dict[str, Any]],
        reminders: list[dict[str, Any]],
    ) -> dict[str, Any]:
        self.logger.info(
            "Syncing dashboard to Notion placeholder: jobs=%s recommendations=%s reminders=%s",
            len(jobs),
            len(recommendations),
            len(reminders),
        )
        return {
            "database_id": self.settings.notion_database_id or "not-configured",
            "jobs_synced": len(jobs),
            "recommendations_synced": len(recommendations),
            "reminders_synced": len(reminders),
        }
