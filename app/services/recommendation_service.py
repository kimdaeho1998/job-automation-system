"""Recommendation generation service."""

from __future__ import annotations

from logging import Logger
from typing import Any

from app.config import Settings


class RecommendationService:
    """Builds action recommendations from collected jobs."""

    def __init__(self, settings: Settings, logger: Logger) -> None:
        self.settings = settings
        self.logger = logger

    def build_recommendations(
        self,
        jobs: list[dict[str, Any]],
    ) -> list[dict[str, str]]:
        recommendations = [
            {
                "type": "resume",
                "message": f"{job['company']} - {job['position']} 공고에 맞춰 이력서를 조정하세요.",
            }
            for job in jobs
        ]
        self.logger.info("Built %s recommendation(s)", len(recommendations))
        return recommendations
