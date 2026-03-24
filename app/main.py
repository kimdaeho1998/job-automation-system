"""Application entrypoint."""

from app.config import get_settings
from app.db.sqlite import initialize_database
from app.scheduler import JobAutomationScheduler
from app.services.notion_service import NotionService
from app.services.reminder_service import ReminderService
from app.utils.logger import setup_logger


def _format_schedule_list(schedules: list[dict[str, str | None]]) -> str:
    if not schedules:
        return "Notion schedules:\n- 조회된 일정이 없습니다."

    lines = ["Notion schedules:", "-" * 52]
    for item in schedules:
        lines.append(
            f"{item['date'] or '-':<10} | {item['status'] or '-':<10} | {item['title'] or '-'}"
        )
    return "\n".join(lines)


def main() -> None:
    settings = get_settings()
    logger = setup_logger(settings.log_level)
    initialize_database()
    scheduler = JobAutomationScheduler(settings=settings, logger=logger)
    notion_service = NotionService(settings=settings, logger=logger)
    reminder_service = ReminderService(settings=settings, logger=logger)

    logger.info("Starting job automation system")
    try:
        schedules = notion_service.get_schedule_items()
        print(_format_schedule_list(schedules))
        print()
        reminder_targets = reminder_service.filter_reminder_targets(schedules)
        print(reminder_service.format_reminders_for_console(reminder_targets))
    except ValueError as exc:
        logger.warning("Skipping Notion schedule fetch: %s", exc)
    except RuntimeError as exc:
        logger.error("Notion schedule fetch failed: %s", exc)

    scheduler.run_once()


if __name__ == "__main__":
    main()
