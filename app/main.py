"""Application entrypoint."""

from app.config import get_settings
from app.db.sqlite import initialize_database
from app.scheduler import JobAutomationScheduler
from app.utils.logger import setup_logger


def main() -> None:
    settings = get_settings()
    logger = setup_logger(settings.log_level)
    initialize_database()
    scheduler = JobAutomationScheduler(settings=settings, logger=logger)

    logger.info("Starting job automation system")
    scheduler.run_once()


if __name__ == "__main__":
    main()
