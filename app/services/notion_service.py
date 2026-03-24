"""Notion integration service."""

from __future__ import annotations

from logging import Logger
from typing import Any, TypedDict

from notion_client import Client
from notion_client.errors import APIResponseError, RequestTimeoutError

from app.config import Settings


class NotionScheduleItem(TypedDict):
    notion_page_id: str
    title: str
    company: str | None
    job_role: str | None
    company_size: str | None
    salary: str | None
    date: str | None
    status: str | None
    priority: str | None


class NotionExpiredJobTarget(TypedDict):
    notion_page_id: str
    title: str
    company: str | None
    deadline: str


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

    def update_expired_jobs_status(
        self,
        expired_jobs: list[NotionExpiredJobTarget],
        status_name: str = "마감",
    ) -> int:
        """만료 공고의 Notion 상태를 일괄 변경하기 위한 함수 골격.

        실제 API 업데이트는 아직 수행하지 않는다. 현재는 추후 구현을 위한
        인터페이스와 입력 구조만 고정한다.
        """

        if not expired_jobs:
            self.logger.info("No expired jobs to mark as closed.")
            return 0

        self.logger.info(
            "Prepared %s expired job(s) for Notion status update: target_status=%s",
            len(expired_jobs),
            status_name,
        )

        for job in expired_jobs:
            notion_page_id = job.get("notion_page_id", "")
            if not notion_page_id:
                self.logger.warning(
                    "Skipping expired job without notion_page_id: title=%s company=%s",
                    job.get("title", ""),
                    job.get("company", ""),
                )
                continue

            # TODO: Notion pages.update API를 호출해 진행상황 속성을 `status_name`으로 변경한다.
            # TODO: 삭제보다 상태 업데이트를 우선 적용하도록 이 함수에서 일괄 처리한다.
            # TODO: 실제 구현 시 진행상황 속성명이 변경될 수 있으므로 설정화 여부를 검토한다.

        return 0

    def build_expired_job_targets(
        self,
        expired_jobs: list[dict[str, Any]],
    ) -> list[NotionExpiredJobTarget]:
        """만료 공고 목록을 Notion 상태 업데이트용 최소 구조로 정규화한다."""

        targets: list[NotionExpiredJobTarget] = []
        for job in expired_jobs:
            notion_page_id = str(job.get("notion_page_id") or "").strip()
            if not notion_page_id:
                self.logger.warning(
                    "Expired job is missing notion_page_id: title=%s company=%s",
                    job.get("title", ""),
                    job.get("company", ""),
                )
                continue

            targets.append(
                NotionExpiredJobTarget(
                    notion_page_id=notion_page_id,
                    title=str(job.get("title") or "제목 없음"),
                    company=str(job.get("company") or "") or None,
                    deadline=str(job.get("deadline") or ""),
                )
            )
        return targets

    def _parse_schedule_item(self, page: dict[str, Any]) -> NotionScheduleItem:
        properties = page.get("properties", {})
        title_property = self._find_property(properties, ("지원 공고명",))
        company_property = self._find_property(properties, ("기업명",))
        job_role_property = self._find_property(properties, ("직무",))
        company_size_property = self._find_property(properties, ("기업 규모",))
        salary_property = self._find_property(properties, ("연봉/급여",))
        status_property = self._find_property(properties, ("진행상황",))
        priority_property = self._find_property(properties, ("우선순위",))
        date_property = self._find_property(properties, ("채용 마감일",))

        return NotionScheduleItem(
            notion_page_id=str(page.get("id") or ""),
            title=self._extract_title(title_property),
            company=self._extract_text_value(company_property),
            job_role=self._extract_text_value(job_role_property),
            company_size=self._extract_text_value(company_size_property),
            salary=self._extract_text_value(salary_property),
            date=self._extract_date(date_property),
            status=self._extract_status(status_property),
            priority=self._extract_status(priority_property),
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

    def _extract_text_value(self, prop: dict[str, Any] | None) -> str | None:
        if not prop:
            return None

        prop_type = prop.get("type")
        if prop_type == "title":
            value = self._extract_title(prop)
            return value or None
        if prop_type == "rich_text":
            rich_text_items = prop.get("rich_text", [])
            value = "".join(item.get("plain_text", "") for item in rich_text_items).strip()
            return value or None
        if prop_type == "select":
            select_value = prop.get("select")
            return select_value.get("name") if select_value else None
        if prop_type == "status":
            status_value = prop.get("status")
            return status_value.get("name") if status_value else None
        if prop_type == "number":
            number_value = prop.get("number")
            return str(number_value) if number_value is not None else None
        return None

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
