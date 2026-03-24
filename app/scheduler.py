"""Scheduling and orchestration logic."""

from __future__ import annotations

from logging import Logger

from app.config import Settings
from app.services.job_collect_service import JobCollectService
from app.services.notion_service import NotionService
from app.services.recommendation_service import RecommendationService
from app.services.reminder_service import ReminderService


class JobAutomationScheduler:
    """Coordinates service execution in a simple sequential flow."""

    def __init__(self, settings: Settings, logger: Logger) -> None:
        self.settings = settings
        self.logger = logger
        self.notion_service = NotionService(settings=settings, logger=logger)
        self.reminder_service = ReminderService(settings=settings, logger=logger)
        self.job_collect_service = JobCollectService(settings=settings, logger=logger)
        self.recommendation_service = RecommendationService(
            settings=settings,
            logger=logger,
        )

    def run_once(self) -> dict:
        self.logger.info("Scheduler cycle started")
        jobs = self.job_collect_service.collect_jobs()
        recommendations = self.recommendation_service.build_recommendations(jobs)
        reminders = self.reminder_service.build_daily_reminders()
        summary = self.notion_service.sync_dashboard(
            jobs=jobs,
            recommendations=recommendations,
            reminders=reminders,
        )
        self.logger.info("Scheduler cycle finished")
        return summary
