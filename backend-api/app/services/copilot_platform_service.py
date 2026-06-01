from datetime import datetime, timezone

from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel

from app.services.encryption_service import decrypt_value, encrypt_value

SETTINGS_ID = "default"


class CopilotPlatformSettingsUpdate(BaseModel):
    allowWebSearch: bool = False
    braveSearchApiKey: str | None = None


class CopilotPlatformSettingsResponse(BaseModel):
    allowWebSearch: bool = False
    hasBraveSearchApiKey: bool = False


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def default_document() -> dict:
    return {
        "_id": SETTINGS_ID,
        "allowWebSearch": False,
        "encryptedBraveSearchApiKey": encrypt_value(""),
        "updatedAt": utc_now(),
    }


async def ensure_default_settings(db: AsyncIOMotorDatabase) -> None:
    existing = await db.copilotPlatformSettings.find_one({"_id": SETTINGS_ID})
    if existing is None:
        await db.copilotPlatformSettings.insert_one(default_document())


async def get_platform_settings(db: AsyncIOMotorDatabase) -> CopilotPlatformSettingsResponse:
    await ensure_default_settings(db)
    document = await db.copilotPlatformSettings.find_one({"_id": SETTINGS_ID}) or {}
    api_key = decrypt_value(document.get("encryptedBraveSearchApiKey", ""))
    return CopilotPlatformSettingsResponse(
        allowWebSearch=document.get("allowWebSearch", False),
        hasBraveSearchApiKey=bool(api_key.strip()),
    )


async def get_brave_api_key(db: AsyncIOMotorDatabase) -> str:
    await ensure_default_settings(db)
    document = await db.copilotPlatformSettings.find_one({"_id": SETTINGS_ID}) or {}
    return decrypt_value(document.get("encryptedBraveSearchApiKey", "")).strip()


async def is_web_search_enabled(db: AsyncIOMotorDatabase) -> bool:
    settings = await get_platform_settings(db)
    return settings.allowWebSearch and settings.hasBraveSearchApiKey


async def update_platform_settings(
    db: AsyncIOMotorDatabase,
    payload: CopilotPlatformSettingsUpdate,
) -> CopilotPlatformSettingsResponse:
    await ensure_default_settings(db)
    update_data: dict = {
        "allowWebSearch": payload.allowWebSearch,
        "updatedAt": utc_now(),
    }

    if payload.braveSearchApiKey is not None and payload.braveSearchApiKey.strip():
        update_data["encryptedBraveSearchApiKey"] = encrypt_value(payload.braveSearchApiKey.strip())

    await db.copilotPlatformSettings.update_one({"_id": SETTINGS_ID}, {"$set": update_data}, upsert=True)
    return await get_platform_settings(db)
