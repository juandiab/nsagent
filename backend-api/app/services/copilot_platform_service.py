import re
from datetime import datetime, timezone

from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel

from app.services.encryption_service import decrypt_value, encrypt_value

SETTINGS_ID = "default"

from app.services.vendor_doc_domains import (
    LOCKED_DOMAINS,
    all_locked_domain_groups,
    get_allowed_domains_for_vendor,
)

_DOMAIN_RE = re.compile(r"^[a-z0-9.-]+\.[a-z]{2,}$")


class CopilotPlatformSettingsUpdate(BaseModel):
    allowWebSearch: bool = False
    braveSearchApiKey: str | None = None
    extraDomains: list[str] | None = None


class CopilotPlatformSettingsResponse(BaseModel):
    allowWebSearch: bool = False
    hasBraveSearchApiKey: bool = False
    lockedDomains: list[str] = []
    vendorLockedDomains: dict[str, list[str]] = {}
    extraDomains: list[str] = []


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def default_document() -> dict:
    return {
        "_id": SETTINGS_ID,
        "allowWebSearch": False,
        "encryptedBraveSearchApiKey": encrypt_value(""),
        "extraDomains": [],
        "updatedAt": utc_now(),
    }


def _sanitize_domains(domains: list[str]) -> list[str]:
    """Normalize user-supplied domains; drop invalid, duplicate, and locked ones."""
    cleaned: list[str] = []
    for raw in domains or []:
        d = (raw or "").strip().lower()
        d = re.sub(r"^https?://", "", d)
        d = d.split("/")[0].strip().strip(".")
        if not d or not _DOMAIN_RE.match(d):
            continue
        if d in LOCKED_DOMAINS or d in cleaned:
            continue
        cleaned.append(d)
    return cleaned


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
        lockedDomains=list(LOCKED_DOMAINS),
        vendorLockedDomains=all_locked_domain_groups(),
        extraDomains=list(document.get("extraDomains", [])),
    )


async def get_brave_api_key(db: AsyncIOMotorDatabase) -> str:
    await ensure_default_settings(db)
    document = await db.copilotPlatformSettings.find_one({"_id": SETTINGS_ID}) or {}
    return decrypt_value(document.get("encryptedBraveSearchApiKey", "")).strip()


async def get_allowed_domains(db: AsyncIOMotorDatabase, vendor: str | None = "netscaler") -> list[str]:
    return await get_allowed_domains_for_vendor(db, vendor)


async def is_web_search_enabled(db: AsyncIOMotorDatabase) -> bool:
    settings = await get_platform_settings(db)
    return settings.allowWebSearch and settings.hasBraveSearchApiKey


async def get_web_search_runtime(db: AsyncIOMotorDatabase) -> dict:
    """Everything the chat needs to run a domain-restricted web search, or disabled."""
    settings = await get_platform_settings(db)
    if not (settings.allowWebSearch and settings.hasBraveSearchApiKey):
        return {"enabled": False}
    api_key = await get_brave_api_key(db)
    if not api_key:
        return {"enabled": False}
    return {
        "enabled": True,
        "apiKey": api_key,
        "allowedDomains": await get_allowed_domains(db),
    }


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

    if payload.extraDomains is not None:
        update_data["extraDomains"] = _sanitize_domains(payload.extraDomains)

    await db.copilotPlatformSettings.update_one({"_id": SETTINGS_ID}, {"$set": update_data}, upsert=True)
    return await get_platform_settings(db)
