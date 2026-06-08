from __future__ import annotations

import re
from datetime import datetime, timezone

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.schemas.slack_settings import SlackSettingsResponse, SlackSettingsUpdate
from app.services.encryption_service import decrypt_value, encrypt_value

SETTINGS_ID = "default"
_SLACK_WEBHOOK_RE = re.compile(
    r"^https://hooks\.slack\.com/services/[A-Za-z0-9/_-]+$",
    re.IGNORECASE,
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def validate_slack_webhook_url(url: str) -> str:
    normalized = url.strip()
    if not normalized:
        raise ValueError("Slack webhook URL is required.")
    if not _SLACK_WEBHOOK_RE.match(normalized):
        raise ValueError("Enter a valid Slack incoming webhook URL (https://hooks.slack.com/services/…).")
    return normalized


def mask_webhook_url(url: str) -> str:
    if not url:
        return ""
    if len(url) <= 24:
        return "https://hooks.slack.com/···"
    return f"{url[:32]}···{url[-4:]}"


def default_document() -> dict:
    return {
        "_id": SETTINGS_ID,
        "enabled": False,
        "encryptedWebhookUrl": encrypt_value(""),
        "defaultChannel": "",
        "notifyLicenseAlerts": True,
        "notifyWorkflowUpdates": True,
        "notifyHealthChecks": False,
        "updatedAt": utc_now(),
    }


async def ensure_slack_settings(db: AsyncIOMotorDatabase) -> None:
    existing = await db.slackSettings.find_one({"_id": SETTINGS_ID})
    if existing is None:
        await db.slackSettings.insert_one(default_document())


async def get_slack_webhook_url(db: AsyncIOMotorDatabase) -> str:
    await ensure_slack_settings(db)
    document = await db.slackSettings.find_one({"_id": SETTINGS_ID}) or {}
    return decrypt_value(document.get("encryptedWebhookUrl", "")).strip()


async def get_slack_settings(db: AsyncIOMotorDatabase) -> SlackSettingsResponse:
    await ensure_slack_settings(db)
    document = await db.slackSettings.find_one({"_id": SETTINGS_ID}) or {}
    webhook_url = decrypt_value(document.get("encryptedWebhookUrl", "")).strip()
    return SlackSettingsResponse(
        enabled=bool(document.get("enabled")),
        hasWebhookUrl=bool(webhook_url),
        webhookUrlPreview=mask_webhook_url(webhook_url) if webhook_url else None,
        defaultChannel=document.get("defaultChannel", ""),
        notifyLicenseAlerts=bool(document.get("notifyLicenseAlerts", True)),
        notifyWorkflowUpdates=bool(document.get("notifyWorkflowUpdates", True)),
        notifyHealthChecks=bool(document.get("notifyHealthChecks", False)),
        updatedAt=document.get("updatedAt"),
    )


async def update_slack_settings(
    db: AsyncIOMotorDatabase,
    payload: SlackSettingsUpdate,
) -> SlackSettingsResponse:
    await ensure_slack_settings(db)
    update_data: dict = {
        "enabled": payload.enabled,
        "defaultChannel": payload.defaultChannel.strip(),
        "notifyLicenseAlerts": payload.notifyLicenseAlerts,
        "notifyWorkflowUpdates": payload.notifyWorkflowUpdates,
        "notifyHealthChecks": payload.notifyHealthChecks,
        "updatedAt": utc_now(),
    }

    if payload.webhookUrl is not None:
        normalized = payload.webhookUrl.strip()
        if normalized:
            update_data["encryptedWebhookUrl"] = encrypt_value(validate_slack_webhook_url(normalized))
        else:
            update_data["encryptedWebhookUrl"] = encrypt_value("")

    await db.slackSettings.update_one({"_id": SETTINGS_ID}, {"$set": update_data}, upsert=True)
    return await get_slack_settings(db)
