"""Logging configuration helpers."""

from __future__ import annotations

import logging


def setup_logger(level: str = "INFO") -> logging.Logger:
    logger = logging.getLogger("job_automation")
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.setLevel(level.upper())
    return logger
