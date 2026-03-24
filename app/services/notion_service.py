"""Notion integration service."""

from __future__ import annotations

from logging import Logger
from typing import Any, TypedDict

from notion_client import Client
from notion_client.errors import APIResponseError, RequestTimeoutError

from app.config import Settings


class NotionScheduleItem(TypedDict):
    title: str
    date: str | None
    status: str | None


class NotionService:
    """Handles Notion database access for dashboard and schedule items."""

    def __init__(self, settings: Settings, logger: Logger) -> None:
        self.settings = settings
        self.logger = logger
        self.client: Client | None = None

        if self.settings.notion_api_key:
            self.client = Client(auth=self.settings.notion_api_key)

    def get_schedule_items(self) -> list[NotionScheduleItem]:
        """Fetch schedule items from the configured Notion database."""

        if not self.settings.notion_api_key:
            raise ValueError("NOTION_API_KEY is not configured.")
        if not self.settings.notion_db_id:
            raise ValueError("NOTION_DB_ID is not configured.")
        if self.client is None:
            raise RuntimeError("Notion client is not initialized.")

        try:
            response = self.client.databases.query(
                **{"database_id": self.settings.notion_db_id}
            )
        except (APIResponseError, RequestTimeoutError) as exc:
            self.logger.exception("Failed to query Notion database")
            raise RuntimeError("Failed to fetch schedule items from Notion.") from exc
        except Exception as exc:
            self.logger.exception("Unexpected error while querying Notion database")
            raise RuntimeError("Unexpected error while fetching Notion schedules.") from exc

        results = response.get("results", [])
        return [self._parse_schedule_item(page) for page in results]

    def _parse_schedule_item(self, page: dict[str, Any]) -> NotionScheduleItem:
        properties = page.get("properties", {})
        title_property = self._find_property(properties, ("title", "Title", "name", "Name"))
        date_property = self._find_property(properties, ("date", "Date", "scheduled", "Scheduled"))
        status_property = self._find_property(properties, ("status", "Status"))

        return NotionScheduleItem(
            title=self._extract_title(title_property),
            date=self._extract_date(date_property),
            status=self._extract_status(status_property),
        )

    def _find_property(
        self,
        properties: dict[str, Any],
        candidates: tuple[str, ...],
    ) -> dict[str, Any] | None:
        for key in candidates:
            if key in properties:
                return properties[key]
        return None

    def _extract_title(self, prop: dict[str, Any] | None) -> str:
        if not prop or prop.get("type") != "title":
            return ""
        title_items = prop.get("title", [])
        return "".join(item.get("plain_text", "") for item in title_items).strip()

    def _extract_date(self, prop: dict[str, Any] | None) -> str | None:
        if not prop or prop.get("type") != "date":
            return None
        date_value = prop.get("date")
        if not date_value:
            return None
        return date_value.get("start")

    def _extract_status(self, prop: dict[str, Any] | None) -> str | None:
        if not prop:
            return None
        prop_type = prop.get("type")
        if prop_type == "status":
            status_value = prop.get("status")
            return status_value.get("name") if status_value else None
        if prop_type == "select":
            select_value = prop.get("select")
            return select_value.get("name") if select_value else None
        return None

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
            "database_id": self.settings.notion_db_id or "not-configured",
            "jobs_synced": len(jobs),
            "recommendations_synced": len(recommendations),
            "reminders_synced": len(reminders),
        }
