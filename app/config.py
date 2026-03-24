"""Application configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    app_name: str = "job-automation-system"
    env: str = "development"
    log_level: str = "INFO"
    notion_api_key: str = ""
    notion_db_id: str = ""
    sqlite_path: str = "job_automation.db"
    reminder_hour: int = 9


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings(
        app_name=os.getenv("APP_NAME", "job-automation-system"),
        env=os.getenv("APP_ENV", "development"),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        notion_api_key=os.getenv("NOTION_API_KEY", ""),
        notion_db_id=os.getenv("NOTION_DB_ID", ""),
        sqlite_path=os.getenv("SQLITE_PATH", "job_automation.db"),
        reminder_hour=int(os.getenv("REMINDER_HOUR", "9")),
    )
