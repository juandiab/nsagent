from typing import Any

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.config import settings
from app.models.user import serialize_user
from app.services.auth_service import hash_password
from app.utils.time import utc_now


async def ensure_default_admin(db: AsyncIOMotorDatabase) -> None:
    cleaned_username = settings.admin_username.strip().lower()
    existing = await db.users.find_one({"username": cleaned_username})
    if existing is not None:
        updates: dict = {"updatedAt": utc_now()}
        if not existing.get("role"):
            updates["role"] = "admin"
        if not existing.get("hashedPassword"):
            updates["hashedPassword"] = hash_password(settings.admin_password)
        if len(updates) > 1:
            await db.users.update_one({"_id": existing["_id"]}, {"$set": updates})
        return

    await db.users.insert_one(
        {
            "username": cleaned_username,
            "displayName": cleaned_username.title(),
            "role": "admin",
            "hashedPassword": hash_password(settings.admin_password),
            "createdAt": utc_now(),
            "updatedAt": utc_now(),
        }
    )


async def get_user_by_username(db: AsyncIOMotorDatabase, username: str) -> dict | None:
    return await db.users.find_one({"username": username.strip().lower()})


async def get_user_by_email(db: AsyncIOMotorDatabase, email: str) -> dict | None:
    cleaned = email.strip().lower()
    if not cleaned:
        return None
    return await db.users.find_one({"email": cleaned})


async def get_user_by_id(db: AsyncIOMotorDatabase, user_id: str) -> dict | None:
    try:
        oid = ObjectId(user_id)
    except Exception:
        return None
    return await db.users.find_one({"_id": oid})


async def list_users(db: AsyncIOMotorDatabase) -> list[dict[str, Any]]:
    users = await db.users.find().sort("username", 1).to_list(length=None)
    rows: list[dict[str, Any]] = []
    for user in users:
        row = serialize_user(user)
        row["passkeyCount"] = await db.passkeys.count_documents({"userId": user["_id"]})
        rows.append(row)
    return rows


async def create_user(
    db: AsyncIOMotorDatabase,
    *,
    username: str,
    display_name: str,
    email: str,
    password: str,
    role: str = "user",
) -> dict[str, Any]:
    cleaned_username = username.strip().lower()
    if await get_user_by_username(db, cleaned_username):
        raise ValueError(f"Username '{cleaned_username}' already exists")

    cleaned_email = email.strip().lower()
    if await get_user_by_email(db, cleaned_email):
        raise ValueError(f"Email '{cleaned_email}' is already in use")

    cleaned_password = password.strip()
    if len(cleaned_password) < 8:
        raise ValueError("Password must be at least 8 characters")

    doc = {
        "username": cleaned_username,
        "displayName": display_name.strip(),
        "email": cleaned_email,
        "role": role,
        "hashedPassword": hash_password(cleaned_password),
        "createdAt": utc_now(),
        "updatedAt": utc_now(),
    }
    result = await db.users.insert_one(doc)
    doc["_id"] = result.inserted_id
    row = serialize_user(doc)
    row["passkeyCount"] = 0
    return row


async def update_user(
    db: AsyncIOMotorDatabase,
    user_id: str,
    *,
    display_name: str | None = None,
    email: str | None = None,
    role: str | None = None,
) -> dict[str, Any] | None:
    user = await get_user_by_id(db, user_id)
    if user is None:
        return None

    updates: dict[str, Any] = {"updatedAt": utc_now()}
    if display_name is not None:
        updates["displayName"] = display_name.strip()
    if email is not None:
        cleaned_email = email.strip().lower()
        existing = await get_user_by_email(db, cleaned_email)
        if existing and existing["_id"] != user["_id"]:
            raise ValueError(f"Email '{cleaned_email}' is already in use")
        updates["email"] = cleaned_email
    if role is not None:
        updates["role"] = role

    await db.users.update_one({"_id": user["_id"]}, {"$set": updates})
    updated = await get_user_by_id(db, user_id)
    if updated is None:
        return None
    row = serialize_user(updated)
    row["passkeyCount"] = await db.passkeys.count_documents({"userId": updated["_id"]})
    return row


async def delete_user(db: AsyncIOMotorDatabase, user_id: str) -> bool:
    user = await get_user_by_id(db, user_id)
    if user is None:
        return False

    await db.passkeys.delete_many({"userId": user["_id"]})
    result = await db.users.delete_one({"_id": user["_id"]})
    return result.deleted_count > 0


async def count_admins(db: AsyncIOMotorDatabase) -> int:
    return await db.users.count_documents({"role": "admin"})
