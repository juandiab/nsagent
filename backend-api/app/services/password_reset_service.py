from __future__ import annotations

import secrets
from datetime import timedelta

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.services.auth_service import (
    RECOVERY_TOKEN_TTL_MINUTES,
    create_recovery_token,
    hash_password,
    verify_password,
)
from app.services.email_service import send_email
from app.services.webauthn_service import count_user_passkeys, delete_all_user_passkeys
from app.utils.time import ensure_utc_aware, utc_now

RESET_CODE_TTL = timedelta(minutes=15)
RESET_CODE_LENGTH = 8
RECOVERY_MAX_ATTEMPTS = 5
_RECOVERY_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"

GENERIC_RECOVERY_MESSAGE = (
    "If an account exists with a configured email address, a recovery code was sent."
)
RECOVERY_ATTEMPTS_EXCEEDED_MESSAGE = (
    "Too many incorrect attempts. Request a new recovery code."
)


def _generate_code() -> str:
    return "".join(secrets.choice(_RECOVERY_CODE_ALPHABET) for _ in range(RESET_CODE_LENGTH))


async def _record_recovery_failure(db: AsyncIOMotorDatabase, doc: dict) -> None:
    failed_attempts = int(doc.get("failedAttempts") or 0) + 1
    if failed_attempts >= RECOVERY_MAX_ATTEMPTS:
        await db.passwordResetCodes.delete_one({"_id": doc["_id"]})
        raise ValueError(RECOVERY_ATTEMPTS_EXCEEDED_MESSAGE)

    await db.passwordResetCodes.update_one(
        {"_id": doc["_id"]},
        {"$set": {"failedAttempts": failed_attempts}},
    )
    raise ValueError("Invalid or expired recovery code")


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
            "failedAttempts": 0,
            "initiatedBy": initiated_by,
            "expiresAt": utc_now() + RESET_CODE_TTL,
            "createdAt": utc_now(),
        }
    )

    subject = "JPilot account recovery code"
    body = (
        f"Hello {user.get('displayName') or user['username']},\n\n"
        f"An account recovery was requested for your JPilot account.\n\n"
        f"Your recovery code is: {code}\n\n"
        f"This code expires in {int(RESET_CODE_TTL.total_seconds() // 60)} minutes.\n"
        f"You can use it to reset your password and/or register a new passkey.\n\n"
        f"If you did not request this, you can ignore this email.\n"
    )
    await send_email(to_address=email, subject=subject, body=body)
    return _mask_email(email)


async def request_self_service_recovery(
    db: AsyncIOMotorDatabase,
    *,
    username: str,
) -> str:
    cleaned_username = username.strip().lower()
    user = await db.users.find_one({"username": cleaned_username})
    if user is None:
        return GENERIC_RECOVERY_MESSAGE

    email = (user.get("email") or "").strip()
    if not email:
        return GENERIC_RECOVERY_MESSAGE

    try:
        await send_reset_code(db, user=user, initiated_by="self-service")
    except RuntimeError:
        return GENERIC_RECOVERY_MESSAGE

    return GENERIC_RECOVERY_MESSAGE


async def confirm_reset(
    db: AsyncIOMotorDatabase,
    *,
    username: str,
    code: str,
    new_password: str | None,
) -> tuple[str, str | None]:
    cleaned_username = username.strip().lower()
    cleaned_code = code.strip().upper()
    cleaned_password = (new_password or "").strip()

    if not cleaned_code:
        raise ValueError("Recovery code is required")

    doc = await db.passwordResetCodes.find_one({"username": cleaned_username})
    if doc is None:
        raise ValueError("Invalid or expired recovery code")
    if doc.get("expiresAt") and ensure_utc_aware(doc["expiresAt"]) < utc_now():
        await db.passwordResetCodes.delete_one({"_id": doc["_id"]})
        raise ValueError("Invalid or expired recovery code")
    if not verify_password(cleaned_code, doc["codeHash"]):
        await _record_recovery_failure(db, doc)

    user_id: ObjectId = doc["userId"]
    user = await db.users.find_one({"_id": user_id})
    if user is None:
        raise ValueError("Invalid or expired recovery code")

    had_passkeys = await count_user_passkeys(db, user_id) > 0
    await delete_all_user_passkeys(db, user_id)
    await db.passwordResetCodes.delete_many({"userId": user_id})

    recovery_token: str | None = None
    if cleaned_password:
        if len(cleaned_password) < 8:
            raise ValueError("Password must be at least 8 characters")
        await db.users.update_one(
            {"_id": user_id},
            {"$set": {"hashedPassword": hash_password(cleaned_password), "updatedAt": utc_now()}},
        )
        if had_passkeys:
            message = (
                "Password updated and existing passkeys removed. "
                "Sign in with your new password, then register a new passkey in Settings."
            )
        else:
            message = "Password updated successfully."
    elif had_passkeys:
        await db.users.update_one(
            {"_id": user_id},
            {"$unset": {"hashedPassword": ""}, "$set": {"updatedAt": utc_now()}},
        )
        recovery_token = create_recovery_token(user["username"])
        message = (
            "Passkeys removed. Register a new passkey below within "
            f"{RECOVERY_TOKEN_TTL_MINUTES} minutes."
        )
    else:
        raise ValueError("A new password is required for this account")

    return message, recovery_token
