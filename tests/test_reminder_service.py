"""Tests for reminder service policy rules."""

from __future__ import annotations

from datetime import date
import logging

import pytest

from app.services.reminder_service import classify_jobs_for_reminders


@pytest.fixture
def fixed_today() -> date:
    return date(2026, 3, 24)


@pytest.fixture
def test_logger() -> logging.Logger:
    return logging.getLogger("test_reminder_service")


def make_job(
    *,
    title: str,
    company: str = "테스트기업",
    status: str = "관심",
    priority: str = "중",
    deadline: str | None = "2026-03-31",
    notion_page_id: str = "page-1",
) -> dict[str, str]:
    job = {
        "title": title,
        "company": company,
        "status": status,
        "priority": priority,
        "notion_page_id": notion_page_id,
    }
    if deadline is not None:
        job["deadline"] = deadline
    return job


def test_completed_status_is_excluded(
    fixed_today: date,
    test_logger: logging.Logger,
) -> None:
    jobs = [
        make_job(title="완료 공고", status="지원완료", deadline="2026-03-31"),
    ]

    result = classify_jobs_for_reminders(jobs, logger=test_logger, today=fixed_today)

    assert result["reminder_targets"] == []
    assert result["expired_jobs"] == []


def test_missing_deadline_is_excluded(
    fixed_today: date,
    test_logger: logging.Logger,
) -> None:
    jobs = [
        make_job(title="마감일 없음", deadline=None),
    ]

    result = classify_jobs_for_reminders(jobs, logger=test_logger, today=fixed_today)

    assert result["reminder_targets"] == []
    assert result["expired_jobs"] == []


def test_past_deadline_jobs_are_separated_to_expired_jobs(
    fixed_today: date,
    test_logger: logging.Logger,
) -> None:
    jobs = [
        make_job(
            title="지난 공고",
            company="지난회사",
            deadline="2026-03-20",
            notion_page_id="expired-page-1",
        ),
    ]

    result = classify_jobs_for_reminders(jobs, logger=test_logger, today=fixed_today)

    assert result["reminder_targets"] == []
    assert result["expired_jobs"] == [
        {
            "title": "지난 공고",
            "company": "지난회사",
            "deadline": "2026-03-20",
            "notion_page_id": "expired-page-1",
        }
    ]


def test_only_d7_d3_d1_and_dday_are_included_in_reminder_targets(
    fixed_today: date,
    test_logger: logging.Logger,
) -> None:
    jobs = [
        make_job(title="D-7 공고", deadline="2026-03-31", priority="상"),
        make_job(title="D-3 공고", deadline="2026-03-27", priority="중"),
        make_job(title="D-1 공고", deadline="2026-03-25", priority="하"),
        make_job(title="D-day 공고", deadline="2026-03-24", priority="상"),
    ]

    result = classify_jobs_for_reminders(jobs, logger=test_logger, today=fixed_today)

    assert [item["title"] for item in result["reminder_targets"]] == [
        "D-day 공고",
        "D-1 공고",
        "D-3 공고",
        "D-7 공고",
    ]
    assert [item["dday_label"] for item in result["reminder_targets"]] == [
        "D-day",
        "D-1",
        "D-3",
        "D-7",
    ]


def test_d2_and_d5_jobs_are_not_included(
    fixed_today: date,
    test_logger: logging.Logger,
) -> None:
    jobs = [
        make_job(title="D-2 공고", deadline="2026-03-26"),
        make_job(title="D-5 공고", deadline="2026-03-29"),
    ]

    result = classify_jobs_for_reminders(jobs, logger=test_logger, today=fixed_today)

    assert result["reminder_targets"] == []
    assert result["expired_jobs"] == []


def test_all_priorities_are_allowed(
    fixed_today: date,
    test_logger: logging.Logger,
) -> None:
    jobs = [
        make_job(title="상 우선순위", priority="상", deadline="2026-03-31"),
        make_job(title="중 우선순위", priority="중", deadline="2026-03-27"),
        make_job(title="하 우선순위", priority="하", deadline="2026-03-25"),
    ]

    result = classify_jobs_for_reminders(jobs, logger=test_logger, today=fixed_today)

    assert [item["priority"] for item in result["reminder_targets"]] == [
        "하",
        "중",
        "상",
    ]


def test_invalid_deadline_format_is_excluded_and_logs_warning(
    fixed_today: date,
    test_logger: logging.Logger,
    caplog: pytest.LogCaptureFixture,
) -> None:
    jobs = [
        make_job(title="잘못된 날짜 공고", deadline="2026년 3월 31일"),
    ]

    with caplog.at_level(logging.WARNING):
        result = classify_jobs_for_reminders(jobs, logger=test_logger, today=fixed_today)

    assert result["reminder_targets"] == []
    assert result["expired_jobs"] == []
    assert "Skipping job with invalid deadline format" in caplog.text
