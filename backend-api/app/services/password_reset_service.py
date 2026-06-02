from __future__ import annotations

import secrets
from datetime import timedelta

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.services.auth_service import hash_password, verify_password
from app.services.email_service import send_email
from app.utils.time import ensure_utc_aware, utc_now

RESET_CODE_TTL = timedelta(minutes=15)
RESET_CODE_LENGTH = 6


def _generate_code() -> str:
    return "".join(str(secrets.randbelow(10)) for _ in range(RESET_CODE_LENGTH))


def _mask_email(email: str) -> str:
    local, _, domain = email.partition("@")
    if not domain:
        return email
    if len(local) <= 2:
        masked_local = local[:1] + "***"
    else:
        masked_local = local[:2] + "***"
    return f"{masked_local}@{domain}"


async def ensure_password_reset_indexes(db: AsyncIOMotorDatabase) -> None:
    await db.passwordResetCodes.create_index("expiresAt", expireAfterSeconds=0)
    await db.users.create_index("email", unique=True, sparse=True)


async def send_reset_code(
    db: AsyncIOMotorDatabase,
    *,
    user: dict,
    initiated_by: str,
) -> str:
    email = (user.get("email") or "").strip()
    if not email:
        raise ValueError("User does not have an email address configured")

    code = _generate_code()
    await db.passwordResetCodes.delete_many({"userId": user["_id"]})
    await db.passwordResetCodes.insert_one(
        {
            "userId": user["_id"],
            "username": user["username"],
            "email": email,
            "codeHash": hash_password(code),
            "initiatedBy": initiated_by,
            "expiresAt": utc_now() + RESET_CODE_TTL,
            "createdAt": utc_now(),
        }
    )

    subject = "JPilot password reset code"
    body = (
        f"Hello {user.get('displayName') or user['username']},\n\n"
        f"A password reset was requested for your JPilot account.\n\n"
        f"Your reset code is: {code}\n\n"
        f"This code expires in {int(RESET_CODE_TTL.total_seconds() // 60)} minutes.\n"
        f"If you did not request this, you can ignore this email.\n"
    )
    await send_email(to_address=email, subject=subject, body=body)
    return _mask_email(email)


async def confirm_reset(
    db: AsyncIOMotorDatabase,
    *,
    username: str,
    code: str,
    new_password: str,
) -> None:
    cleaned_username = username.strip().lower()
    cleaned_code = code.strip()
    cleaned_password = new_password.strip()

    if len(cleaned_password) < 8:
        raise ValueError("Password must be at least 8 characters")
    if not cleaned_code:
        raise ValueError("Reset code is required")

    doc = await db.passwordResetCodes.find_one({"username": cleaned_username})
    if doc is None:
        raise ValueError("Invalid or expired reset code")
    if doc.get("expiresAt") and ensure_utc_aware(doc["expiresAt"]) < utc_now():
        await db.passwordResetCodes.delete_one({"_id": doc["_id"]})
        raise ValueError("Invalid or expired reset code")
    if not verify_password(cleaned_code, doc["codeHash"]):
        raise ValueError("Invalid or expired reset code")

    user_id: ObjectId = doc["userId"]
    await db.users.update_one(
        {"_id": user_id},
        {"$set": {"hashedPassword": hash_password(cleaned_password), "updatedAt": utc_now()}},
    )
    await db.passwordResetCodes.delete_many({"userId": user_id})
