from __future__ import annotations

from datetime import datetime, timedelta

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.utils.time import ensure_utc_aware, utc_now

LOGIN_MAX_FAILURES = 5
LOGIN_LOCKOUT_MINUTES = 15


def _normalize_username(username: str) -> str:
    return username.strip().lower()


def _lockout_message(locked_until: datetime) -> str:
    remaining = ensure_utc_aware(locked_until) - utc_now()
    minutes = max(1, int(remaining.total_seconds() + 59) // 60)
    return (
        f"Too many failed sign-in attempts. Try again in about {minutes} minute"
        f"{'' if minutes == 1 else 's'}."
    )


async def ensure_auth_lockout_indexes(db: AsyncIOMotorDatabase) -> None:
    await db.authLoginLockouts.create_index("username", unique=True)


async def get_login_lockout_message(db: AsyncIOMotorDatabase, *, username: str) -> str | None:
    cleaned = _normalize_username(username)
    if not cleaned:
        return None

    doc = await db.authLoginLockouts.find_one({"username": cleaned})
    if doc is None:
        return None

    locked_until = doc.get("lockedUntil")
    if locked_until is None:
        return None

    locked_until_aware = ensure_utc_aware(locked_until)
    if locked_until_aware <= utc_now():
        await db.authLoginLockouts.update_one(
            {"username": cleaned},
            {"$set": {"failedAttempts": 0, "lockedUntil": None, "updatedAt": utc_now()}},
        )
        return None

    return _lockout_message(locked_until_aware)


async def record_login_failure(db: AsyncIOMotorDatabase, *, username: str) -> str | None:
    cleaned = _normalize_username(username)
    if not cleaned:
        return None

    now = utc_now()
    doc = await db.authLoginLockouts.find_one({"username": cleaned})
    failed_attempts = (doc.get("failedAttempts", 0) if doc else 0) + 1
    locked_until: datetime | None = None
    if failed_attempts >= LOGIN_MAX_FAILURES:
        locked_until = now + timedelta(minutes=LOGIN_LOCKOUT_MINUTES)
        failed_attempts = LOGIN_MAX_FAILURES

    await db.authLoginLockouts.update_one(
        {"username": cleaned},
        {
            "$set": {
                "failedAttempts": failed_attempts,
                "lockedUntil": locked_until,
                "updatedAt": now,
            }
        },
        upsert=True,
    )

    if locked_until is not None:
        return _lockout_message(locked_until)
    return None


async def clear_login_lockout(db: AsyncIOMotorDatabase, *, username: str) -> None:
    cleaned = _normalize_username(username)
    if not cleaned:
        return
    await db.authLoginLockouts.delete_one({"username": cleaned})
