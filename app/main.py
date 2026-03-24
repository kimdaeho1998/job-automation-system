"""Application entrypoint."""

from app.config import get_settings
from app.db.sqlite import initialize_database
from app.scheduler import JobAutomationScheduler
from app.services.notion_service import NotionService
from app.utils.logger import setup_logger


def main() -> None:
    settings = get_settings()
    logger = setup_logger(settings.log_level)
    initialize_database()
    scheduler = JobAutomationScheduler(settings=settings, logger=logger)
    notion_service = NotionService(settings=settings, logger=logger)

    logger.info("Starting job automation system")
    try:
        schedules = notion_service.get_schedule_items()
        print("Notion schedules:")
        if not schedules:
            print("- 조회된 일정이 없습니다.")
        for item in schedules:
            print(
                f"- title={item['title'] or '-'}, date={item['date'] or '-'}, status={item['status'] or '-'}"
            )
    except ValueError as exc:
        logger.warning("Skipping Notion schedule fetch: %s", exc)
    except RuntimeError as exc:
        logger.error("Notion schedule fetch failed: %s", exc)

    scheduler.run_once()


if __name__ == "__main__":
    main()
