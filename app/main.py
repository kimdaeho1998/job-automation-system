"""Application entrypoint."""

from __future__ import annotations

from logging import Logger

from app.config import get_settings
from app.db.sqlite import initialize_database
from app.scheduler import JobAutomationScheduler
from app.services.email_service import (
    build_reminder_email_body,
    build_reminder_email_subject,
    send_email,
)
from app.services.notion_service import NotionService
from app.services.reminder_service import (
    ReminderClassificationResult,
    ReminderJobItem,
    ReminderService,
)
from app.utils.logger import setup_logger


def _format_schedule_list(schedules: list[dict[str, str | None]]) -> str:
    if not schedules:
        return "Notion schedules:\n- 조회된 일정이 없습니다."

    headers = [
        "지원 공고명",
        "기업명",
        "직무",
        "기업 규모",
        "연봉/급여",
        "진행상황",
        "우선순위",
        "채용 마감일",
    ]
    lines = ["Notion schedules:", " | ".join(headers), "-" * 120]
    for item in schedules:
        lines.append(
            " | ".join(
                [
                    item["title"] or "-",
                    item.get("company") or "-",
                    item.get("job_role") or "-",
                    item.get("company_size") or "-",
                    item.get("salary") or "-",
                    item["status"] or "-",
                    item.get("priority") or "-",
                    item["date"] or "-",
                ]
            )
        )
    return "\n".join(lines)


def _print_console_summary(
    schedules: list[dict[str, str | None]],
    reminder_targets: list[ReminderJobItem],
    reminder_service: ReminderService,
) -> None:
    """콘솔 출력은 유지하되 출력 책임을 별도 함수로 분리한다."""

    print(_format_schedule_list(schedules))
    print()
    print(reminder_service.format_reminders_for_console(reminder_targets))


def _send_reminder_email_if_needed(
    reminder_targets: list[ReminderJobItem],
    logger: Logger,
) -> None:
    """알림 대상이 있을 때만 이메일을 발송한다."""

    if not reminder_targets:
        logger.info("No reminder targets found. Skipping email notification.")
        return

    subject = build_reminder_email_subject(reminder_targets)
    body = build_reminder_email_body(reminder_targets)
    logger.info("Sending email notification for %s reminder target(s)", len(reminder_targets))

    if send_email(subject=subject, body=body):
        logger.info("Email notification sent successfully.")
        return

    logger.error("Email notification failed.")


def _process_job_notifications(
    notion_service: NotionService,
    reminder_service: ReminderService,
    logger: Logger,
) -> None:
    """조회, 분류, 출력, 메일 전송 흐름을 한 번에 처리한다."""

    schedules = notion_service.get_schedule_items()
    reminder_result: ReminderClassificationResult = reminder_service.classify_schedules(
        schedules
    )
    reminder_targets = reminder_result["reminder_targets"]
    expired_jobs = reminder_result["expired_jobs"]

    _print_console_summary(schedules, reminder_targets, reminder_service)
    logger.info("Expired jobs queued for cleanup: %s", len(expired_jobs))
    _send_reminder_email_if_needed(reminder_targets, logger)


def main() -> None:
    settings = get_settings()
    logger = setup_logger(settings.log_level)
    initialize_database()
    scheduler = JobAutomationScheduler(settings=settings, logger=logger)
    notion_service = NotionService(settings=settings, logger=logger)
    reminder_service = ReminderService(settings=settings, logger=logger)

    logger.info("Starting job automation system")
    try:
        _process_job_notifications(
            notion_service=notion_service,
            reminder_service=reminder_service,
            logger=logger,
        )
    except ValueError as exc:
        logger.warning("Skipping Notion schedule fetch: %s", exc)
    except RuntimeError as exc:
        logger.error("Notion schedule fetch failed: %s", exc)

    scheduler.run_once()


if __name__ == "__main__":
    main()
