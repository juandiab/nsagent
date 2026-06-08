from __future__ import annotations

from typing import Any

import httpx
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.services.slack_settings_service import (
    get_slack_settings,
    get_slack_webhook_url,
    validate_slack_webhook_url,
)


async def is_slack_delivery_enabled(db: AsyncIOMotorDatabase) -> bool:
    settings = await get_slack_settings(db)
    return settings.enabled and settings.hasWebhookUrl


async def send_slack_message(
    webhook_url: str,
    *,
    text: str,
    channel: str | None = None,
) -> tuple[bool, str]:
    url = validate_slack_webhook_url(webhook_url)
    payload: dict[str, Any] = {"text": text.strip()}
    if channel and channel.strip():
        payload["channel"] = channel.strip()

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        detail = exc.response.text.strip()[:200] if exc.response.text else str(exc)
        return False, f"Slack returned HTTP {exc.response.status_code}: {detail}"
    except httpx.RequestError as exc:
        return False, f"Could not reach Slack: {exc}"

    return True, "Notification delivered to Slack."


async def send_slack_notification(
    db: AsyncIOMotorDatabase,
    *,
    text: str,
    channel: str | None = None,
) -> tuple[bool, str]:
    if not await is_slack_delivery_enabled(db):
        return False, "Slack notifications are not enabled."

    webhook_url = await get_slack_webhook_url(db)
    if not webhook_url:
        return False, "Slack webhook URL is not configured."

    settings = await get_slack_settings(db)
    target_channel = channel or settings.defaultChannel or None
    return await send_slack_message(webhook_url, text=text, channel=target_channel)


async def test_slack_notification(
    db: AsyncIOMotorDatabase,
    *,
    webhook_url: str | None,
    message: str,
) -> tuple[bool, str]:
    url = (webhook_url or "").strip()
    if not url:
        url = await get_slack_webhook_url(db)
    if not url:
        return False, "Configure a Slack webhook URL before sending a test notification."

    settings = await get_slack_settings(db)
    return await send_slack_message(
        url,
        text=message.strip() or "JPilot Slack test notification.",
        channel=settings.defaultChannel or None,
    )
