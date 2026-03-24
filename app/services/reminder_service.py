"""Reminder generation service."""

from __future__ import annotations

from datetime import date
from logging import Logger
from typing import Any, TypedDict

from app.config import Settings
from app.utils.date_utils import now_local, parse_date_string, to_date_string


REMINDER_DAY_OFFSETS = {7, 3, 1, 0}


class ReminderJobItem(TypedDict):
    title: str
    company: str
    status: str
    priority: str
    deadline: str
    dday_label: str


class ExpiredJobItem(TypedDict):
    title: str
    company: str
    deadline: str
    notion_page_id: str


class ReminderClassificationResult(TypedDict):
    reminder_targets: list[ReminderJobItem]
    expired_jobs: list[ExpiredJobItem]


def calculate_dday(deadline: date, today: date | None = None) -> int:
    """마감일까지 남은 일수를 계산한다."""

    base_date = today or now_local().date()
    return (deadline - base_date).days


def format_dday_label(days_until_deadline: int) -> str | None:
    """알림 정책에 해당하는 D-day 라벨을 반환한다."""

    if days_until_deadline == 0:
        return "D-day"
    if days_until_deadline in REMINDER_DAY_OFFSETS:
        return f"D-{days_until_deadline}"
    return None


def build_reminder_job_item(
    job: dict[str, Any],
    deadline_text: str,
    dday_label: str,
) -> ReminderJobItem:
    """출력과 테스트에 쓰기 쉬운 공통 아이템 구조를 만든다."""

    return ReminderJobItem(
        title=str(job.get("title") or "제목 없음"),
        company=str(job.get("company") or "기업명 없음"),
        status=str(job.get("status") or "상태 없음"),
        priority=str(job.get("priority") or "우선순위 없음"),
        deadline=deadline_text,
        dday_label=dday_label,
    )


def build_expired_job_item(
    job: dict[str, Any],
    deadline_text: str,
) -> ExpiredJobItem:
    """후속 정리 작업에 사용할 최소 공고 정보를 만든다."""

    return ExpiredJobItem(
        title=str(job.get("title") or "제목 없음"),
        company=str(job.get("company") or "기업명 없음"),
        deadline=deadline_text,
        notion_page_id=str(job.get("notion_page_id") or ""),
    )


def get_deadline_text(job: dict[str, Any]) -> str:
    """마감일 문자열을 가져온다. 기존 date 필드도 호환한다."""

    return str(job.get("deadline") or job.get("date") or "").strip()


def classify_jobs_for_reminders(
    jobs: list[dict[str, Any]],
    logger: Logger,
    today: date | None = None,
) -> ReminderClassificationResult:
    """공고 목록을 알림 대상과 지난 공고로 분류한다."""

    reference_date = today or now_local().date()
    reminder_targets: list[ReminderJobItem] = []
    expired_jobs: list[ExpiredJobItem] = []

    for job in jobs:
        status = str(job.get("status") or "").strip()
        if status == "지원완료":
            continue

        deadline_text = get_deadline_text(job)
        if not deadline_text:
            continue

        try:
            deadline_date = parse_date_string(deadline_text)
        except ValueError:
            logger.warning(
                "Skipping job with invalid deadline format: title=%s deadline=%s",
                job.get("title", ""),
                deadline_text,
            )
            continue

        days_until_deadline = calculate_dday(deadline_date, today=reference_date)
        dday_label = format_dday_label(days_until_deadline)

        if days_until_deadline < 0:
            expired_jobs.append(
                build_expired_job_item(
                    job=job,
                    deadline_text=deadline_text,
                )
            )
            continue

        if dday_label is None:
            continue

        reminder_targets.append(
            build_reminder_job_item(
                job=job,
                deadline_text=deadline_text,
                dday_label=dday_label,
            )
        )

    reminder_targets.sort(key=lambda item: item["deadline"])
    expired_jobs.sort(key=lambda item: item["deadline"])
    return {
        "reminder_targets": reminder_targets,
        "expired_jobs": expired_jobs,
    }


class ReminderService:
    """Builds reminder payloads for daily job-prep tasks."""

    def __init__(self, settings: Settings, logger: Logger) -> None:
        self.settings = settings
        self.logger = logger

    def classify_schedules(
        self,
        jobs: list[dict[str, Any]],
    ) -> ReminderClassificationResult:
        """노션 공고 목록을 알림 대상과 지난 공고로 분리한다."""

        return classify_jobs_for_reminders(jobs=jobs, logger=self.logger)

    def filter_reminder_targets(
        self,
        jobs: list[dict[str, Any]],
    ) -> list[ReminderJobItem]:
        """알림 대상 공고 목록만 반환한다."""

        return self.classify_schedules(jobs)["reminder_targets"]

    def get_expired_jobs(
        self,
        jobs: list[dict[str, Any]],
    ) -> list[ExpiredJobItem]:
        """지난 공고 목록만 반환한다."""

        return self.classify_schedules(jobs)["expired_jobs"]

    def format_reminders_for_console(
        self,
        reminders: list[ReminderJobItem],
    ) -> str:
        """알림 대상 공고를 콘솔에서 보기 좋게 출력한다."""

        if not reminders:
            return "알림 대상 일정이 없습니다."

        lines = ["알림 대상 일정", "-" * 76]
        for reminder in reminders:
            lines.append(
                f"[{reminder['dday_label']:<5}] {reminder['deadline']} | "
                f"{reminder['status']:<10} | {reminder['priority']:<10} | "
                f"{reminder['company']} | {reminder['title']}"
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
