"""Discord notification service."""

from __future__ import annotations

from logging import getLogger
from typing import Any

import requests


logger = getLogger("job_automation")


def build_discord_message(reminder_targets: list[dict[str, Any]]) -> str:
    """알림 대상 공고 목록을 Discord 메시지 문자열로 변환한다."""

    if not reminder_targets:
        return "[채용 공고 알림]\n\n오늘 확인할 공고가 없습니다."

    lines = ["[채용 공고 알림]", ""]
    for job in reminder_targets:
        dday_label = str(job.get("dday_label") or "D-day 정보 없음")
        company = str(job.get("company") or "기업명 없음")
        title = str(job.get("title") or "제목 없음")
        status = str(job.get("status") or "상태 없음")
        priority = str(job.get("priority") or "없음")
        deadline = str(job.get("deadline") or job.get("date") or "마감일 없음")

        lines.append(f"- [{dday_label}] {company} | {title}")
        lines.append(
            f"  상태: {status} | 우선순위: {priority} | 마감일: {deadline}"
        )
        lines.append("")

    return "\n".join(lines).rstrip()


def send_discord_notification(
    webhook_url: str,
    reminder_targets: list[dict[str, Any]],
) -> bool:
    """Discord Webhook으로 알림을 전송한다."""

    if not webhook_url.strip():
        logger.error("Discord webhook configuration is incomplete")
        return False

    message = build_discord_message(reminder_targets)

    try:
        response = requests.post(
            webhook_url,
            json={"content": message},
            timeout=10,
        )
        response.raise_for_status()
    except Exception:
        logger.exception("Discord notification failed")
        return False

    return True
