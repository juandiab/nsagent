from __future__ import annotations

import asyncio
import re
from datetime import datetime, timezone
from email.message import EmailMessage

import aiosmtplib
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.schemas.smtp_settings import SMTPSettingsResponse, SMTPSettingsUpdate, SMTPTestRequest
from app.services.encryption_service import decrypt_value, encrypt_value

SETTINGS_ID = "default"

# Known provider presets. The frontend uses these to pre-fill host/port/security;
# they are kept here so the backend can validate and document the supported set.
PROVIDER_PRESETS: dict[str, dict] = {
    "gmail": {"host": "smtp.gmail.com", "port": 587, "useTls": True, "useSsl": False},
    "outlook": {"host": "smtp.office365.com", "port": 587, "useTls": True, "useSsl": False},
    "custom": {},
}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _clean_password(value: str | None) -> str:
    """Strip all whitespace from a password.

    Gmail and Outlook display app passwords as space-separated groups (e.g.
    'ghyr dbis uenx cllz') for readability, but the real secret has no spaces.
    Removing whitespace lets users paste the password exactly as shown.
    """
    return re.sub(r"\s+", "", value or "")


def default_document() -> dict:
    return {
        "_id": SETTINGS_ID,
        "provider": "custom",
        "host": "",
        "port": 587,
        "username": "",
        "encryptedPassword": encrypt_value(""),
        "fromAddress": "",
        "useTls": True,
        "useSsl": False,
        "updatedAt": utc_now(),
    }


async def ensure_default_settings(db: AsyncIOMotorDatabase) -> None:
    existing = await db.smtpSettings.find_one({"_id": SETTINGS_ID})
    if existing is None:
        await db.smtpSettings.insert_one(default_document())


async def get_smtp_settings(db: AsyncIOMotorDatabase) -> SMTPSettingsResponse:
    await ensure_default_settings(db)
    document = await db.smtpSettings.find_one({"_id": SETTINGS_ID}) or {}
    password = decrypt_value(document.get("encryptedPassword", ""))
    return SMTPSettingsResponse(
        provider=document.get("provider", "custom"),
        host=document.get("host", ""),
        port=document.get("port", 587),
        username=document.get("username", ""),
        hasPassword=bool(password.strip()),
        fromAddress=document.get("fromAddress", ""),
        useTls=document.get("useTls", True),
        useSsl=document.get("useSsl", False),
        updatedAt=document.get("updatedAt"),
    )


async def get_smtp_password(db: AsyncIOMotorDatabase) -> str:
    await ensure_default_settings(db)
    document = await db.smtpSettings.find_one({"_id": SETTINGS_ID}) or {}
    return decrypt_value(document.get("encryptedPassword", ""))


async def update_smtp_settings(
    db: AsyncIOMotorDatabase,
    payload: SMTPSettingsUpdate,
) -> SMTPSettingsResponse:
    await ensure_default_settings(db)
    if payload.useTls and payload.useSsl:
        raise ValueError("Choose either STARTTLS or implicit SSL, not both")

    update_data: dict = {
        "provider": payload.provider,
        "host": payload.host.strip(),
        "port": payload.port,
        "username": payload.username.strip(),
        "fromAddress": payload.fromAddress.strip(),
        "useTls": payload.useTls,
        "useSsl": payload.useSsl,
        "updatedAt": utc_now(),
    }

    # Only overwrite the stored password when a new one is supplied, so saving other
    # fields doesn't wipe an existing secret.
    new_password = _clean_password(payload.password)
    if new_password:
        update_data["encryptedPassword"] = encrypt_value(new_password)

    await db.smtpSettings.update_one({"_id": SETTINGS_ID}, {"$set": update_data}, upsert=True)
    return await get_smtp_settings(db)


async def test_smtp_settings(
    db: AsyncIOMotorDatabase,
    payload: SMTPTestRequest,
) -> tuple[bool, str]:
    host = payload.host.strip()
    if not host:
        return False, "SMTP host is required"

    recipient = payload.testRecipient.strip()
    if not recipient:
        return False, "A recipient address is required to send the test email"

    if payload.useTls and payload.useSsl:
        return False, "Choose either STARTTLS or implicit SSL, not both"

    # Use the supplied password, or fall back to the stored one when the field was
    # left blank (so an already-saved secret can be tested without re-entering it).
    password = _clean_password(payload.password)
    if not password:
        password = _clean_password(await get_smtp_password(db))

    from_address = payload.fromAddress.strip() or payload.username.strip() or recipient

    message = EmailMessage()
    message["From"] = from_address
    message["To"] = recipient
    message["Subject"] = "NSAgent SMTP test"
    message.set_content(
        "This is a test message from NSAgent. "
        "If you received it, your SMTP settings are working correctly."
    )

    try:
        await aiosmtplib.send(
            message,
            hostname=host,
            port=payload.port,
            username=payload.username.strip() or None,
            password=password or None,
            start_tls=payload.useTls,
            use_tls=payload.useSsl,
            timeout=15,
        )
    except aiosmtplib.SMTPAuthenticationError as exc:
        return False, f"Authentication failed: {exc}"
    except aiosmtplib.SMTPConnectError as exc:
        return False, f"Could not connect to {host}:{payload.port}: {exc}"
    except aiosmtplib.SMTPException as exc:
        return False, f"SMTP error: {exc}"
    except asyncio.TimeoutError:
        return False, f"Connection to {host}:{payload.port} timed out"
    except OSError as exc:
        return False, f"Could not reach {host}:{payload.port}: {exc}"

    return True, f"Test email sent to {recipient}."
