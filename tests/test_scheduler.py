"""Basic scheduler tests."""

from app.config import get_settings
from app.scheduler import JobAutomationScheduler
from app.utils.logger import setup_logger


def test_scheduler_run_once_returns_summary() -> None:
    scheduler = JobAutomationScheduler(
        settings=get_settings(),
        logger=setup_logger("INFO"),
    )

    result = scheduler.run_once()

    assert result["jobs_synced"] >= 1
    assert result["recommendations_synced"] >= 1
    assert result["reminders_synced"] >= 1
