from datetime import datetime, timezone

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.schemas.jpilot_settings import JpilotSettingsResponse, JpilotSettingsUpdate, PortalConfigResponse

SETTINGS_ID = "default"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def default_document() -> dict:
    return {
        "_id": SETTINGS_ID,
        "displayHomePage": True,
        "updatedAt": utc_now(),
    }


async def ensure_jpilot_settings(db: AsyncIOMotorDatabase) -> None:
    existing = await db.jpilotSettings.find_one({"_id": SETTINGS_ID})
    if existing is None:
        await db.jpilotSettings.insert_one(default_document())


async def get_display_home_page(db: AsyncIOMotorDatabase) -> bool:
    await ensure_jpilot_settings(db)
    document = await db.jpilotSettings.find_one({"_id": SETTINGS_ID}) or {}
    return bool(document.get("displayHomePage", True))


async def get_portal_config(db: AsyncIOMotorDatabase) -> PortalConfigResponse:
    return PortalConfigResponse(displayHomePage=await get_display_home_page(db))


async def get_jpilot_settings(db: AsyncIOMotorDatabase) -> JpilotSettingsResponse:
    return JpilotSettingsResponse(displayHomePage=await get_display_home_page(db))


async def update_jpilot_settings(
    db: AsyncIOMotorDatabase,
    payload: JpilotSettingsUpdate,
) -> JpilotSettingsResponse:
    await ensure_jpilot_settings(db)
    await db.jpilotSettings.update_one(
        {"_id": SETTINGS_ID},
        {
            "$set": {
                "displayHomePage": bool(payload.displayHomePage),
                "updatedAt": utc_now(),
            }
        },
        upsert=True,
    )
    return await get_jpilot_settings(db)
