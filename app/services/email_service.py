"""Email notification service."""

from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage
from logging import getLogger
from typing import Any


logger = getLogger("job_automation")


def get_email_settings() -> dict[str, str | int]:
    """이메일 발송 설정을 환경변수에서 읽는다."""

    return {
        "host": os.getenv("EMAIL_HOST", "smtp.gmail.com"),
        "port": int(os.getenv("EMAIL_PORT", "587")),
        "user": os.getenv("EMAIL_USER", ""),
        "password": os.getenv("EMAIL_PASSWORD", ""),
        "to": os.getenv("EMAIL_TO", ""),
    }


def build_reminder_email_subject(reminder_targets: list[dict[str, Any]]) -> str:
    """알림 대상 공고 수를 기준으로 메일 제목을 만든다."""

    return f"[취업 알림] 오늘 확인할 공고 {len(reminder_targets)}건"


def build_reminder_email_body(reminder_targets: list[dict[str, Any]]) -> str:
    """알림 대상 공고 목록을 메일 본문 문자열로 만든다."""

    if not reminder_targets:
        return "오늘 확인할 공고가 없습니다."

    lines = [
        "오늘 확인이 필요한 채용 공고 목록입니다.",
        "",
    ]

    for index, job in enumerate(reminder_targets, start=1):
        title = str(job.get("title") or "제목 없음")
        company = str(job.get("company") or "기업명 없음")
        status = str(job.get("status") or "상태 없음")
        priority = str(job.get("priority") or "우선순위 없음")
        deadline = str(job.get("deadline") or job.get("date") or "마감일 없음")
        dday_label = str(job.get("dday_label") or "D-day 정보 없음")

        lines.extend(
            [
                f"{index}. {title}",
                f"   회사명: {company}",
                f"   진행상황: {status}",
                f"   우선순위: {priority}",
                f"   마감일: {deadline}",
                f"   D-day: {dday_label}",
                "",
            ]
        )

    return "\n".join(lines).rstrip()


def create_email_message(subject: str, body: str) -> EmailMessage:
    """채널별 확장을 고려해 이메일 메시지 생성 단계를 분리한다."""

    settings = get_email_settings()
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = str(settings["user"])
    message["To"] = str(settings["to"])
    message.set_content(body, subtype="plain", charset="utf-8")
    return message


def send_email(subject: str, body: str) -> bool:
    """SMTP를 이용해 이메일 알림을 발송한다."""

    settings = get_email_settings()
    host = str(settings["host"])
    port = int(settings["port"])
    user = str(settings["user"])
    password = str(settings["password"])
    recipient = str(settings["to"])

    if not user or not password or not recipient:
        logger.error("Email configuration is incomplete.")
        return False

    message = create_email_message(subject=subject, body=body)

    try:
        # Gmail SMTP 기본 흐름: STARTTLS 연결 후 로그인한다.
        with smtplib.SMTP(host, port) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()
            smtp.login(user, password)
            smtp.send_message(message)
    except Exception as exc:
        logger.error("Failed to send email notification: %s", exc)
        return False

    return True
