"""SQLite connection utilities."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from app.config import get_settings


def get_connection() -> sqlite3.Connection:
    settings = get_settings()
    db_path = Path(settings.sqlite_path)
    return sqlite3.connect(db_path)


def initialize_database() -> None:
    connection = get_connection()
    with connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS job_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_at TEXT NOT NULL,
                status TEXT NOT NULL
            )
            """
        )
    connection.close()
