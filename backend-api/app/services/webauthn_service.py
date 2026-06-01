"""WebAuthn / passkey registration and authentication."""

from __future__ import annotations

import json
from datetime import timedelta
from typing import Any

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from webauthn import (
    generate_authentication_options,
    generate_registration_options,
    options_to_json,
    verify_authentication_response,
    verify_registration_response,
)
from webauthn.helpers import base64url_to_bytes, bytes_to_base64url
from webauthn.helpers.parse_authentication_credential_json import parse_authentication_credential_json
from webauthn.helpers.parse_registration_credential_json import parse_registration_credential_json
from webauthn.helpers.structs import (
    AuthenticatorSelectionCriteria,
    AuthenticatorTransport,
    PublicKeyCredentialDescriptor,
    ResidentKeyRequirement,
    UserVerificationRequirement,
)

from app.config import settings
from app.utils.time import ensure_utc_aware, utc_now


CHALLENGE_TTL = timedelta(minutes=5)


def _user_handle(user_id: ObjectId) -> bytes:
    return user_id.binary


def _public_key_options_dict(options: Any) -> dict[str, Any]:
    """options_to_json returns a JSON string; FastAPI/clients need a dict."""
    payload = options_to_json(options)
    if isinstance(payload, str):
        return json.loads(payload)
    if isinstance(payload, dict):
        return payload
    raise ValueError("Unexpected WebAuthn options payload type")


async def _store_challenge(
    db: AsyncIOMotorDatabase,
    *,
    username: str,
    user_id: ObjectId,
    challenge: bytes,
    flow: str,
) -> None:
    await db.webauthnChallenges.delete_many({"username": username, "flow": flow})
    await db.webauthnChallenges.insert_one(
        {
            "username": username,
            "userId": user_id,
            "challenge": bytes_to_base64url(challenge),
            "flow": flow,
            "expiresAt": utc_now() + CHALLENGE_TTL,
            "createdAt": utc_now(),
        }
    )


async def _pop_challenge(
    db: AsyncIOMotorDatabase,
    *,
    username: str,
    flow: str,
) -> tuple[bytes, ObjectId]:
    doc = await db.webauthnChallenges.find_one({"username": username, "flow": flow})
    if doc is None:
        raise ValueError("Authentication challenge expired or not found — start again")
    if doc.get("expiresAt") and ensure_utc_aware(doc["expiresAt"]) < utc_now():
        await db.webauthnChallenges.delete_one({"_id": doc["_id"]})
        raise ValueError("Authentication challenge expired — start again")
    await db.webauthnChallenges.delete_one({"_id": doc["_id"]})
    return base64url_to_bytes(doc["challenge"]), doc["userId"]


async def list_user_passkeys(db: AsyncIOMotorDatabase, user_id: ObjectId) -> list[dict[str, Any]]:
    cursor = db.passkeys.find({"userId": user_id}).sort("createdAt", -1)
    return await cursor.to_list(length=None)


async def count_user_passkeys(db: AsyncIOMotorDatabase, user_id: ObjectId) -> int:
    return await db.passkeys.count_documents({"userId": user_id})


async def count_all_passkeys(db: AsyncIOMotorDatabase) -> int:
    return await db.passkeys.count_documents({})


async def get_passkey_by_credential_id(db: AsyncIOMotorDatabase, credential_id: str) -> dict[str, Any] | None:
    return await db.passkeys.find_one({"credentialId": credential_id})


def _parse_transports(transports: list[Any] | None) -> list[AuthenticatorTransport]:
    parsed: list[AuthenticatorTransport] = []
    for transport in transports or []:
        if isinstance(transport, AuthenticatorTransport):
            parsed.append(transport)
            continue
        if isinstance(transport, str):
            try:
                parsed.append(AuthenticatorTransport(transport))
            except ValueError:
                continue
    return parsed


def _transports_to_strings(transports: list[Any] | None) -> list[str]:
    values: list[str] = []
    for transport in transports or []:
        if isinstance(transport, AuthenticatorTransport):
            values.append(transport.value)
        elif isinstance(transport, str):
            values.append(transport)
    return values


def _exclude_credentials(passkeys: list[dict[str, Any]]) -> list[PublicKeyCredentialDescriptor]:
    descriptors: list[PublicKeyCredentialDescriptor] = []
    for item in passkeys:
        credential_id = item.get("credentialId")
        if not credential_id:
            continue
        descriptors.append(
            PublicKeyCredentialDescriptor(
                id=base64url_to_bytes(credential_id),
                transports=_parse_transports(item.get("transports")),
            )
        )
    return descriptors


async def begin_registration(
    db: AsyncIOMotorDatabase,
    user: dict[str, Any],
) -> dict[str, Any]:
    user_id: ObjectId = user["_id"]
    existing = await list_user_passkeys(db, user_id)
    options = generate_registration_options(
        rp_id=settings.webauthn_rp_id,
        rp_name=settings.webauthn_rp_name,
        user_id=_user_handle(user_id),
        user_name=user["username"],
        user_display_name=user.get("displayName") or user["username"],
        exclude_credentials=_exclude_credentials(existing),
        authenticator_selection=AuthenticatorSelectionCriteria(
            resident_key=ResidentKeyRequirement.PREFERRED,
            user_verification=UserVerificationRequirement.PREFERRED,
        ),
    )
    await _store_challenge(
        db,
        username=user["username"],
        user_id=user_id,
        challenge=options.challenge,
        flow="registration",
    )
    return _public_key_options_dict(options)


async def finish_registration(
    db: AsyncIOMotorDatabase,
    user: dict[str, Any],
    credential: dict[str, Any],
    *,
    label: str = "",
) -> None:
    expected_challenge, user_id = await _pop_challenge(
        db, username=user["username"], flow="registration"
    )
    if user_id != user["_id"]:
        raise ValueError("Registration challenge does not match user")

    parsed = parse_registration_credential_json(json.dumps(credential))
    verification = verify_registration_response(
        credential=parsed,
        expected_challenge=expected_challenge,
        expected_rp_id=settings.webauthn_rp_id,
        expected_origin=settings.cors_origin_list,
        require_user_verification=False,
    )

    credential_id = bytes_to_base64url(verification.credential_id)
    existing = await get_passkey_by_credential_id(db, credential_id)
    if existing is not None:
        raise ValueError("This passkey is already registered")

    await db.passkeys.insert_one(
        {
            "userId": user["_id"],
            "credentialId": credential_id,
            "publicKey": bytes_to_base64url(verification.credential_public_key),
            "signCount": verification.sign_count,
            "transports": _transports_to_strings(getattr(parsed.response, "transports", None)),
            "aaguid": str(verification.aaguid),
            "label": label.strip() or "Passkey",
            "createdAt": utc_now(),
            "lastUsedAt": None,
        }
    )


async def begin_authentication(
    db: AsyncIOMotorDatabase,
    user: dict[str, Any],
) -> dict[str, Any]:
    passkeys = await list_user_passkeys(db, user["_id"])
    if not passkeys:
        raise ValueError("No passkey registered for this user — set one up first")

    options = generate_authentication_options(
        rp_id=settings.webauthn_rp_id,
        allow_credentials=_exclude_credentials(passkeys),
        user_verification=UserVerificationRequirement.PREFERRED,
    )
    await _store_challenge(
        db,
        username=user["username"],
        user_id=user["_id"],
        challenge=options.challenge,
        flow="authentication",
    )
    return _public_key_options_dict(options)


async def finish_authentication(
    db: AsyncIOMotorDatabase,
    user: dict[str, Any],
    credential: dict[str, Any],
) -> None:
    expected_challenge, user_id = await _pop_challenge(
        db, username=user["username"], flow="authentication"
    )
    if user_id != user["_id"]:
        raise ValueError("Authentication challenge does not match user")

    parsed = parse_authentication_credential_json(json.dumps(credential))
    credential_id = bytes_to_base64url(parsed.raw_id)
    stored = await get_passkey_by_credential_id(db, credential_id)
    if stored is None or stored["userId"] != user["_id"]:
        raise ValueError("Unknown passkey for this user")

    verification = verify_authentication_response(
        credential=parsed,
        expected_challenge=expected_challenge,
        expected_rp_id=settings.webauthn_rp_id,
        expected_origin=settings.cors_origin_list,
        credential_public_key=base64url_to_bytes(stored["publicKey"]),
        credential_current_sign_count=stored.get("signCount", 0),
        require_user_verification=False,
    )

    await db.passkeys.update_one(
        {"_id": stored["_id"]},
        {
            "$set": {
                "signCount": verification.new_sign_count,
                "lastUsedAt": utc_now(),
            }
        },
    )


async def delete_passkey(db: AsyncIOMotorDatabase, passkey_id: ObjectId) -> bool:
    result = await db.passkeys.delete_one({"_id": passkey_id})
    return result.deleted_count > 0


async def ensure_webauthn_indexes(db: AsyncIOMotorDatabase) -> None:
    await db.passkeys.create_index("credentialId", unique=True)
    await db.passkeys.create_index("userId")
    await db.webauthnChallenges.create_index("expiresAt", expireAfterSeconds=0)
