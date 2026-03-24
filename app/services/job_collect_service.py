"""Job collection service."""

from __future__ import annotations

from logging import Logger

from app.config import Settings
from app.utils.date_utils import now_local, to_date_string


class JobCollectService:
    """Collects job postings from configured sources."""

    def __init__(self, settings: Settings, logger: Logger) -> None:
        self.settings = settings
        self.logger = logger

    def collect_jobs(self) -> list[dict[str, str]]:
        jobs = [
            {
                "company": "Example Tech",
                "position": "Python Automation Engineer",
                "source": "sample-feed",
                "collected_at": to_date_string(now_local()),
            }
        ]
        self.logger.info("Collected %s job posting(s)", len(jobs))
        return jobs
