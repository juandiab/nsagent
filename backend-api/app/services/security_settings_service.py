from datetime import datetime, timezone

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.schemas.security_settings import PasskeyPolicy, SecuritySettingsResponse, SecuritySettingsUpdate

SETTINGS_ID = "default"
VALID_PASSKEY_POLICIES: frozenset[str] = frozenset({"disabled", "enabled", "enforced"})
DEFAULT_PASSKEY_POLICY: PasskeyPolicy = "enabled"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def default_document() -> dict:
    return {
        "_id": SETTINGS_ID,
        "passkeyPolicy": DEFAULT_PASSKEY_POLICY,
        "updatedAt": utc_now(),
    }


def normalize_passkey_policy(value: str | None) -> PasskeyPolicy:
    cleaned = (value or "").strip().lower()
    if cleaned in VALID_PASSKEY_POLICIES:
        return cleaned  # type: ignore[return-value]
    return DEFAULT_PASSKEY_POLICY


async def ensure_security_settings(db: AsyncIOMotorDatabase) -> None:
    existing = await db.securitySettings.find_one({"_id": SETTINGS_ID})
    if existing is None:
        await db.securitySettings.insert_one(default_document())


async def get_passkey_policy(db: AsyncIOMotorDatabase) -> PasskeyPolicy:
    await ensure_security_settings(db)
    document = await db.securitySettings.find_one({"_id": SETTINGS_ID}) or {}
    return normalize_passkey_policy(document.get("passkeyPolicy"))


async def get_security_settings(db: AsyncIOMotorDatabase) -> SecuritySettingsResponse:
    return SecuritySettingsResponse(passkeyPolicy=await get_passkey_policy(db))


async def update_security_settings(
    db: AsyncIOMotorDatabase,
    payload: SecuritySettingsUpdate,
) -> SecuritySettingsResponse:
    await ensure_security_settings(db)
    policy = normalize_passkey_policy(payload.passkeyPolicy)
    await db.securitySettings.update_one(
        {"_id": SETTINGS_ID},
        {"$set": {"passkeyPolicy": policy, "updatedAt": utc_now()}},
        upsert=True,
    )
    return SecuritySettingsResponse(passkeyPolicy=policy)
