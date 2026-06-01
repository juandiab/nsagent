from datetime import datetime, timezone

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.config import settings
from app.services.auth_service import hash_password


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


async def ensure_default_admin(db: AsyncIOMotorDatabase) -> None:
    existing = await db.users.find_one({"username": settings.admin_username})
    if existing is not None:
        return

    await db.users.insert_one(
        {
            "username": settings.admin_username,
            "hashedPassword": hash_password(settings.admin_password),
            "createdAt": utc_now(),
            "updatedAt": utc_now(),
        }
    )


async def get_user_by_username(db: AsyncIOMotorDatabase, username: str) -> dict | None:
    return await db.users.find_one({"username": username})
