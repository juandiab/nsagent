from __future__ import annotations

import logging
from email.message import EmailMessage

import aiosmtplib

from app.config import settings

logger = logging.getLogger(__name__)


async def send_email(*, to_address: str, subject: str, body: str) -> None:
    if not settings.smtp_host:
        if settings.password_reset_log_codes:
            logger.warning(
                "SMTP not configured; email not sent to %s. Subject: %s\n%s",
                to_address,
                subject,
                body,
            )
            return
        raise RuntimeError("SMTP is not configured")

    message = EmailMessage()
    message["From"] = settings.smtp_from_address or settings.smtp_username
    message["To"] = to_address
    message["Subject"] = subject
    message.set_content(body)

    await aiosmtplib.send(
        message,
        hostname=settings.smtp_host,
        port=settings.smtp_port,
        username=settings.smtp_username or None,
        password=settings.smtp_password or None,
        start_tls=settings.smtp_use_tls,
        use_tls=settings.smtp_use_ssl,
    )
