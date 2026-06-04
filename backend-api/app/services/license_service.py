from __future__ import annotations

import hashlib
import json
import logging
import os
import re
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.config import settings
from app.schemas.license import LicenseCodeUpdate, LicenseDetailsResponse, LicenseResponse
from app.services.encryption_service import decrypt_value, encrypt_value
from app.services.license_crypto_service import (
    NEXXUS_OFFLINE_ALGORITHM,
    NEXXUS_OFFLINE_FORMAT,
    decrypt_nexxus_license_blob,
    decrypt_encrypted_license,
)
from app.services.license_sync_service import LicenseSyncError, LicenseSyncResult, post_license_sync

LICENSE_COLLECTION = "license"
LEGACY_LICENSE_COLLECTION = "license_state"
LEGACY_LICENSES_COLLECTION = "licenses"
LEGACY_LICENSE_DOCUMENT_ID = "default"


def license_document_id(app_fingerprint: str | None = None) -> str:
    """MongoDB ``_id`` for this installation (stable app fingerprint)."""
    if app_fingerprint and str(app_fingerprint).strip():
        return str(app_fingerprint).strip()
    return licensefingerprint()["fingerprint"]


def _document_id(document: dict[str, Any]) -> str:
    doc_id = document.get("_id")
    if doc_id is not None and str(doc_id).strip():
        return str(doc_id).strip()
    return license_document_id(document.get("appFingerprint"))


def _app_name() -> str:
    return os.environ.get("JPILOT_APP_NAME", "").strip() or settings.jpilot_app_name


_LICENSE_CODE_RE = re.compile(r"^[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}$")
_EXPIRATION_IN_MESSAGE_RE = re.compile(
    r"until\s+(\d{4}-\d{2}-\d{2}T[\d:.]+(?:Z|[+-]\d{2}:?\d{2})?|\d{4}-\d{2}-\d{2})",
    re.IGNORECASE,
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


async def ensure_license_collection(db: AsyncIOMotorDatabase) -> None:
    """Use the ``license`` collection (documents created on first Settings → License visit)."""
    names = await db.list_collection_names()
    if LEGACY_LICENSE_COLLECTION in names:
        await db[LEGACY_LICENSE_COLLECTION].drop()
    if LEGACY_LICENSES_COLLECTION in names:
        await db[LEGACY_LICENSES_COLLECTION].drop()
        logger.info("Dropped legacy %s collection; JPilot uses %s only.", LEGACY_LICENSES_COLLECTION, LICENSE_COLLECTION)
    if LICENSE_COLLECTION not in names:
        await db.create_collection(LICENSE_COLLECTION)


def build_license_fingerprint(
    nsagent_encryption_key: str,
    nginx_hostname: str,
    date: str,
) -> str:
    """Deterministic SHA-256 fingerprint from the three license binding values."""
    payload = "\n".join((nsagent_encryption_key, nginx_hostname, date))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def licensefingerprint() -> dict[str, str]:
    """Compute the current installation fingerprint (used only when seeding the license record)."""
    nsagent_encryption_key = settings.nsagent_encryption_key
    nginx_hostname = os.environ.get("NGINX_HOSTNAME", "").strip() or settings.nginx_hostname
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return {
        "nsagent_encryption_key": nsagent_encryption_key,
        "nginx_hostname": nginx_hostname,
        "date": date,
        "fingerprint": build_license_fingerprint(nsagent_encryption_key, nginx_hostname, date),
    }


def normalize_license_code(raw: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]", "", (raw or "").strip()).upper()
    if len(cleaned) != 16:
        raise ValueError("License code must be 16 characters (format XXXX-XXXX-XXXX-XXXX).")
    code = "-".join(cleaned[i : i + 4] for i in range(0, 16, 4))
    if not _LICENSE_CODE_RE.match(code):
        raise ValueError("Invalid license code format.")
    return code


def _new_license_document() -> dict[str, Any]:
    fingerprint = licensefingerprint()
    now = utc_now()
    install_fp = fingerprint["fingerprint"]
    return {
        "_id": install_fp,
        "appFingerprint": install_fp,
        "appName": _app_name(),
        "activationDate": now.isoformat().replace("+00:00", "Z"),
        "encryptedLicenseCode": "",
        "encryptedLicense": "",
        "cachedLicense": None,
        "status": "pending",
        "message": "",
        "renewalCount": 0,
        "licenseType": None,
        "expirationDate": None,
        "registrationDate": None,
        "validityDays": None,
        "customerName": None,
        "customerEmail": None,
        "company": None,
        "algorithm": None,
        "version": None,
        "lastSyncedAt": None,
        "syncError": None,
        "obtainedOffline": False,
        "offlineImportedAt": None,
        "createdAt": now,
        "updatedAt": now,
    }


def _has_license_code(document: dict[str, Any]) -> bool:
    cipher = document.get("encryptedLicenseCode") or ""
    if not cipher:
        return False
    try:
        return bool(decrypt_value(cipher).strip())
    except Exception:
        return False


def _decrypt_license_code(document: dict[str, Any]) -> str | None:
    cipher = document.get("encryptedLicenseCode") or ""
    if not cipher:
        return None
    try:
        value = decrypt_value(cipher).strip()
        return value or None
    except Exception:
        return None


def _coerce_datetime_string(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        dt = value.astimezone(timezone.utc) if value.tzinfo else value.replace(tzinfo=timezone.utc)
        return dt.isoformat().replace("+00:00", "Z")
    text = str(value).strip()
    return text or None


def _parse_datetime(value: Any) -> datetime | None:
    text = _coerce_datetime_string(value)
    if not text:
        return None
    try:
        if text.endswith("Z"):
            parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        else:
            parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _days_until_expiration(expiration: str | None) -> int | None:
    exp = _parse_datetime(expiration)
    if exp is None:
        return None
    return max(0, (exp.date() - utc_now().date()).days)


def _profile_sources(payload: dict[str, Any]) -> list[dict[str, Any]]:
    sources: list[dict[str, Any]] = [payload]
    for key in ("license", "record", "registration", "holder", "customer", "data", "detail"):
        nested = payload.get(key)
        if isinstance(nested, dict) and nested not in sources:
            sources.append(nested)
    return sources


def _document_profile(document: dict[str, Any]) -> dict[str, Any]:
    cached = document.get("cachedLicense") if isinstance(document.get("cachedLicense"), dict) else {}
    profile: dict[str, Any] = {}
    for key in (
        "customerName",
        "customerEmail",
        "company",
        "licenseType",
        "expirationDate",
        "registrationDate",
        "validityDays",
    ):
        value = document.get(key) or cached.get(key)
        if value is not None and str(value).strip():
            profile[key] = value
    return profile


def _coerce_validity_days(value: Any) -> int | None:
    if value is None:
        return None
    try:
        days = int(value)
    except (TypeError, ValueError):
        return None
    return days if days >= 0 else None


def _extract_sync_metadata(payload: dict[str, Any], *, message: str = "") -> dict[str, Any]:
    """Plaintext license fields returned by Nexxus sync (no decrypt required)."""
    meta: dict[str, Any] = {}
    field_map = (
        ("licenseType", "licenseType"),
        ("expirationDate", "expirationDate"),
        ("registrationDate", "registrationDate"),
        ("validityDays", "validityDays"),
        ("name", "customerName"),
        ("email", "customerEmail"),
        ("customerName", "customerName"),
        ("customerEmail", "customerEmail"),
        ("company", "company"),
        ("usageType", "usageType"),
    )
    for source in _profile_sources(payload):
        for source_key, target_key in field_map:
            if meta.get(target_key) is not None:
                continue
            raw = source.get(source_key)
            if raw is None:
                continue
            if target_key == "validityDays":
                days = _coerce_validity_days(raw)
                if days is not None:
                    meta[target_key] = days
                continue
            if str(raw).strip():
                meta[target_key] = str(raw).strip()

    if not meta.get("expirationDate"):
        text = (message or str(payload.get("message") or "")).strip()
        match = _EXPIRATION_IN_MESSAGE_RE.search(text)
        if match:
            date_text = match.group(1)
            meta["expirationDate"] = date_text if "T" in date_text else f"{date_text}T23:59:59Z"

    for key in ("expirationDate", "registrationDate"):
        if key in meta:
            normalized = _coerce_datetime_string(meta[key])
            if normalized:
                meta[key] = normalized
    return meta


def _merge_license_cache(
    existing: dict[str, Any] | None,
    *layers: dict[str, Any] | None,
) -> dict[str, Any] | None:
    merged: dict[str, Any] = dict(existing) if isinstance(existing, dict) else {}
    for layer in layers:
        if not isinstance(layer, dict):
            continue
        for key, value in layer.items():
            if value is None:
                continue
            if key == "validityDays":
                days = _coerce_validity_days(value)
                if days is not None:
                    merged[key] = days
                continue
            if str(value).strip():
                merged[key] = value
    return merged or None


def _sync_payload_metadata(
    document: dict[str, Any],
    payload: dict[str, Any],
    *,
    message: str = "",
) -> dict[str, Any]:
    """Merge stored profile with Nexxus sync body; later layers win (server over stale DB)."""
    return (
        _merge_license_cache(
            _document_profile(document),
            _extract_sync_metadata(payload, message=message),
        )
        or {}
    )


def _warn_sync_field_mismatches(server: dict[str, Any], decrypted: dict[str, Any]) -> None:
    """Log when top-level sync fields disagree with the signed encrypted payload."""
    for key in ("expirationDate", "licenseType", "registrationDate", "validityDays"):
        server_val = server.get(key)
        decrypted_val = decrypted.get(key)
        if server_val is None or decrypted_val is None:
            continue
        if key == "expirationDate":
            server_cmp = _coerce_datetime_string(server_val)
            decrypted_cmp = _coerce_datetime_string(decrypted_val)
        elif key == "validityDays":
            server_cmp = _coerce_validity_days(server_val)
            decrypted_cmp = _coerce_validity_days(decrypted_val)
        else:
            server_cmp = str(server_val).strip()
            decrypted_cmp = str(decrypted_val).strip()
        if server_cmp != decrypted_cmp:
            logger.warning(
                "License sync: %s from server (%s) differs from encrypted payload (%s); using encrypted.",
                key,
                server_cmp,
                decrypted_cmp,
            )


def _apply_sync_metadata(updates: dict[str, Any], metadata: dict[str, Any]) -> None:
    if not metadata:
        return
    if metadata.get("licenseType"):
        updates["licenseType"] = str(metadata["licenseType"])
    expiration = _coerce_datetime_string(metadata.get("expirationDate"))
    if expiration:
        updates["expirationDate"] = expiration
    registration = _coerce_datetime_string(metadata.get("registrationDate"))
    if registration:
        updates["registrationDate"] = registration
    validity_days = _coerce_validity_days(metadata.get("validityDays"))
    if validity_days is not None:
        updates["validityDays"] = validity_days
    if metadata.get("customerName"):
        updates["customerName"] = str(metadata["customerName"])
    if metadata.get("customerEmail"):
        updates["customerEmail"] = str(metadata["customerEmail"])
    if metadata.get("company") is not None:
        updates["company"] = str(metadata["company"])
    if metadata.get("usageType"):
        updates["usageType"] = str(metadata["usageType"])
    updates["cachedLicense"] = _merge_license_cache(updates.get("cachedLicense"), metadata)


def _expiration_from_payload(payload: dict[str, Any]) -> str | None:
    expiration = _coerce_datetime_string(
        payload.get("expirationDate")
        or payload.get("expiresAt")
        or payload.get("validUntil")
        or payload.get("expiryDate")
    )
    if expiration:
        return expiration
    unix = payload.get("expirationDateUnix")
    if unix is None:
        return None
    try:
        ts = int(unix)
    except (TypeError, ValueError):
        return None
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat().replace("+00:00", "Z")


def _license_status_from_expiration(expiration: str | None) -> str:
    exp = _parse_datetime(expiration)
    if exp is not None and exp <= utc_now():
        return "expired"
    return "active"


def _is_jpilot_app_name(name: str) -> bool:
    return name.strip().lower() == _app_name().strip().lower()


def _cache_from_decrypted(decrypted: dict[str, Any]) -> dict[str, Any]:
    """Normalize decrypted Nexxus license JSON for MongoDB cache and API details."""
    license_type = (
        decrypted.get("licenseType")
        or decrypted.get("type")
        or decrypted.get("edition")
        or decrypted.get("licenseUseType")
    )
    expiration = _expiration_from_payload(decrypted)
    customer_name = (
        decrypted.get("customerName")
        or decrypted.get("name")
        or decrypted.get("fullName")
        or decrypted.get("contactName")
    )
    customer_email = (
        decrypted.get("customerEmail")
        or decrypted.get("email")
        or decrypted.get("contactEmail")
    )
    cached: dict[str, Any] = {}
    if license_type:
        cached["licenseType"] = str(license_type)
    if expiration:
        cached["expirationDate"] = str(expiration)
    registration = _coerce_datetime_string(decrypted.get("registrationDate"))
    if registration:
        cached["registrationDate"] = registration
    validity_days = _coerce_validity_days(decrypted.get("validityDays"))
    if validity_days is not None:
        cached["validityDays"] = validity_days
    if customer_name:
        cached["customerName"] = str(customer_name)
    if customer_email:
        cached["customerEmail"] = str(customer_email)
    for key in ("status", "features", "company"):
        if key in decrypted and decrypted[key] is not None:
            cached[key] = decrypted[key]
    return cached


def _build_license_details(document: dict[str, Any]) -> LicenseDetailsResponse | None:
    if not _has_license_code(document):
        return None

    cached = document.get("cachedLicense") if isinstance(document.get("cachedLicense"), dict) else {}
    license_code = _decrypt_license_code(document)
    expiration = document.get("expirationDate") or cached.get("expirationDate")
    registration = document.get("registrationDate") or cached.get("registrationDate")
    validity_days = document.get("validityDays")
    if validity_days is None:
        validity_days = cached.get("validityDays")
    license_type = document.get("licenseType") or cached.get("licenseType")
    customer_name = document.get("customerName") or cached.get("customerName")
    customer_email = document.get("customerEmail") or cached.get("customerEmail")
    company = document.get("company")
    if company is None:
        company = cached.get("company")
    expiration_text = _coerce_datetime_string(expiration)

    return LicenseDetailsResponse(
        licenseType=str(license_type) if license_type else None,
        licenseCode=license_code,
        daysToExpire=_days_until_expiration(expiration_text),
        expirationDate=expiration_text,
        registrationDate=_coerce_datetime_string(registration),
        validityDays=_coerce_validity_days(validity_days),
        customerName=str(customer_name) if customer_name else None,
        customerEmail=str(customer_email) if customer_email else None,
        company=str(company) if company is not None else None,
    )


def _serialize_license(document: dict[str, Any]) -> LicenseResponse:
    cached = document.get("cachedLicense")
    expiration = _coerce_datetime_string(document.get("expirationDate"))
    registration = _coerce_datetime_string(document.get("registrationDate"))
    validity_days = _coerce_validity_days(document.get("validityDays"))
    license_type = document.get("licenseType")
    if isinstance(cached, dict):
        expiration = expiration or _coerce_datetime_string(cached.get("expirationDate"))
        registration = registration or _coerce_datetime_string(cached.get("registrationDate"))
        if validity_days is None:
            validity_days = _coerce_validity_days(cached.get("validityDays"))
        license_type = license_type or cached.get("licenseType")

    return LicenseResponse(
        appFingerprint=document.get("appFingerprint", ""),
        appName=document.get("appName", _app_name()),
        activationDate=document.get("activationDate", ""),
        hasLicenseCode=_has_license_code(document),
        status=document.get("status") or "pending",
        message=document.get("message") or "",
        renewalCount=int(document.get("renewalCount") or 0),
        licenseType=str(license_type) if license_type else None,
        expirationDate=expiration,
        registrationDate=registration,
        validityDays=validity_days,
        algorithm=document.get("algorithm"),
        version=document.get("version"),
        lastSyncedAt=document.get("lastSyncedAt"),
        syncError=document.get("syncError"),
        hasCachedLicense=isinstance(cached, dict) and bool(cached),
        obtainedOffline=bool(document.get("obtainedOffline")),
        details=_build_license_details(document),
    )


def _try_decrypt_and_cache(
    document: dict[str, Any],
    *,
    encrypted_license: str,
    crypto_version: int,
) -> tuple[dict[str, Any] | None, str | None]:
    license_code = _decrypt_license_code(document)
    if not license_code:
        return None, "License code is required to decrypt the license payload."
    try:
        decrypted = decrypt_encrypted_license(
            encrypted_license,
            app_fingerprint=document["appFingerprint"],
            app_name=document.get("appName") or _app_name(),
            license_code=license_code,
            version=crypto_version,
            activation_date=document.get("activationDate"),
        )
    except Exception as exc:
        name = type(exc).__name__
        detail = str(exc).strip() or name
        return None, f"Could not decrypt license payload ({detail})."
    return _cache_from_decrypted(decrypted) or decrypted, None


def _reconcile_local_expiration_status(updates: dict[str, Any]) -> None:
    """Enforce expiry from persisted ``expirationDate`` when sync left status active."""
    if updates.get("status") in ("deactivated", "missing"):
        return
    expiration = _coerce_datetime_string(updates.get("expirationDate"))
    if expiration and _license_status_from_expiration(expiration) == "expired":
        updates["status"] = "expired"
        if not str(updates.get("message") or "").strip():
            updates["message"] = "License has expired."


def _apply_sync_result(document: dict[str, Any], result: LicenseSyncResult) -> dict[str, Any]:
    now = utc_now()
    payload = result.payload
    server_metadata = _sync_payload_metadata(document, payload, message=result.message)
    updates: dict[str, Any] = {
        "lastSyncedAt": now,
        "updatedAt": now,
        "syncError": None,
    }

    if result.is_success:
        status = result.status or "active"
        updates.update(
            {
                "status": status,
                "message": result.message,
                "renewalCount": int(payload.get("renewalCount") or document.get("renewalCount") or 0),
            }
        )
        if payload.get("encryptedLicense"):
            updates["encryptedLicense"] = str(payload["encryptedLicense"])
        if payload.get("algorithm"):
            updates["algorithm"] = str(payload["algorithm"])
        if payload.get("version") is not None:
            updates["version"] = int(payload["version"])

        encrypted = str(updates.get("encryptedLicense") or document.get("encryptedLicense") or "")
        crypto_version = int(updates.get("version") or document.get("version") or 1)
        authoritative = server_metadata
        if encrypted:
            cached, decrypt_error = _try_decrypt_and_cache(
                {**document, **updates},
                encrypted_license=encrypted,
                crypto_version=crypto_version,
            )
            if cached:
                _warn_sync_field_mismatches(server_metadata, cached)
                authoritative = _merge_license_cache(server_metadata, cached) or server_metadata
            elif decrypt_error:
                logger.warning("License payload decrypt failed: %s", decrypt_error)
        if authoritative:
            _apply_sync_metadata(updates, authoritative)
        _reconcile_local_expiration_status(updates)
        return updates

    if result.is_terminal:
        status = result.status or ("missing" if result.http_status == 404 else "expired")
        updates.update(
            {
                "status": status,
                "message": result.message,
                "encryptedLicense": "",
            }
        )
        _apply_sync_metadata(updates, server_metadata)
        if not updates.get("cachedLicense"):
            updates["cachedLicense"] = None
        return updates

    updates["status"] = result.status or document.get("status") or "pending"
    updates["message"] = result.message
    return updates


async def _find_license_document(db: AsyncIOMotorDatabase) -> dict[str, Any] | None:
    """Load the license row for this installation, migrating legacy ``_id: \"default\"`` if needed."""
    install_id = license_document_id()
    document = await db[LICENSE_COLLECTION].find_one({"_id": install_id})
    if document is not None:
        return document

    legacy = await db[LICENSE_COLLECTION].find_one({"_id": LEGACY_LICENSE_DOCUMENT_ID})
    if legacy is None:
        return None

    stored_fp = str(legacy.get("appFingerprint") or install_id).strip()
    new_id = stored_fp if stored_fp and stored_fp != LEGACY_LICENSE_DOCUMENT_ID else install_id
    migrated = {**legacy, "_id": new_id, "appFingerprint": new_id}
    await db[LICENSE_COLLECTION].insert_one(migrated)
    await db[LICENSE_COLLECTION].delete_one({"_id": LEGACY_LICENSE_DOCUMENT_ID})
    if new_id != install_id:
        logger.warning(
            "Migrated license document to _id=%s; current installation fingerprint is %s",
            new_id,
            install_id,
        )
    return migrated


async def _ensure_license_record(db: AsyncIOMotorDatabase) -> dict[str, Any]:
    document = await _find_license_document(db)
    if document is None:
        document = _new_license_document()
        await db[LICENSE_COLLECTION].insert_one(document)
    return document


async def sync_license(
    db: AsyncIOMotorDatabase,
    *,
    document: dict[str, Any] | None = None,
) -> dict[str, Any]:
    document = document or await _find_license_document(db)
    if document is None:
        raise LicenseSyncError("License record has not been created yet.")

    doc_id = _document_id(document)
    license_code = _decrypt_license_code(document)
    try:
        result = await post_license_sync(
            app_fingerprint=document["appFingerprint"],
            app_name=document.get("appName") or _app_name(),
            license_code=license_code,
        )
    except LicenseSyncError:
        raise

    updates = _apply_sync_result(document, result)
    await db[LICENSE_COLLECTION].update_one({"_id": doc_id}, {"$set": updates})
    refreshed = await db[LICENSE_COLLECTION].find_one({"_id": doc_id})
    return refreshed or {**document, **updates}


def _should_sync_with_server(document: dict[str, Any]) -> bool:
    """Sync when online activation applies (skipped for offline ``.lic`` imports)."""
    if document.get("obtainedOffline"):
        return False
    return bool(document.get("appFingerprint")) and _has_license_code(document)


async def run_scheduled_license_sync(db: AsyncIOMotorDatabase) -> None:
    """Startup and daily POST /licensing/sync (fingerprint + app name + license code)."""
    document = await _find_license_document(db)
    if document is None or not _should_sync_with_server(document):
        return
    doc_id = _document_id(document)
    try:
        await sync_license(db, document=document)
    except LicenseSyncError as exc:
        await db[LICENSE_COLLECTION].update_one(
            {"_id": doc_id},
            {"$set": {"syncError": str(exc), "updatedAt": utc_now()}},
        )


async def get_or_create_license(db: AsyncIOMotorDatabase) -> LicenseResponse:
    document = await _ensure_license_record(db)

    if _should_sync_with_server(document):
        try:
            document = await sync_license(db, document=document)
        except LicenseSyncError as exc:
            doc_id = _document_id(document)
            await db[LICENSE_COLLECTION].update_one(
                {"_id": doc_id},
                {"$set": {"syncError": str(exc), "updatedAt": utc_now()}},
            )
            document = await db[LICENSE_COLLECTION].find_one({"_id": doc_id}) or document

    return _serialize_license(document)


async def save_license_code(db: AsyncIOMotorDatabase, payload: LicenseCodeUpdate) -> LicenseResponse:
    document = await _ensure_license_record(db)
    doc_id = _document_id(document)
    try:
        code = normalize_license_code(payload.licenseCode)
    except ValueError as exc:
        raise LicenseSyncError(str(exc)) from exc

    await db[LICENSE_COLLECTION].update_one(
        {"_id": doc_id},
        {
            "$set": {
                "encryptedLicenseCode": encrypt_value(code),
                "obtainedOffline": False,
                "offlineImportedAt": None,
                "updatedAt": utc_now(),
            }
        },
    )

    try:
        await sync_license(db, document=document)
    except LicenseSyncError as exc:
        await db[LICENSE_COLLECTION].update_one(
            {"_id": doc_id},
            {"$set": {"syncError": str(exc), "updatedAt": utc_now()}},
        )

    document = await db[LICENSE_COLLECTION].find_one({"_id": doc_id}) or {}
    return _serialize_license(document)


def _license_reset_fields() -> dict[str, Any]:
    """Fields cleared when the user removes a license (installation record stays)."""
    return {
        "encryptedLicenseCode": "",
        "encryptedLicense": "",
        "cachedLicense": None,
        "status": "pending",
        "message": "",
        "renewalCount": 0,
        "licenseType": None,
        "expirationDate": None,
        "registrationDate": None,
        "validityDays": None,
        "customerName": None,
        "customerEmail": None,
        "company": None,
        "usageType": None,
        "algorithm": None,
        "version": None,
        "lastSyncedAt": None,
        "syncError": None,
        "obtainedOffline": False,
        "offlineImportedAt": None,
    }


async def remove_license(db: AsyncIOMotorDatabase) -> LicenseResponse:
    """Remove the active license but keep fingerprint and activation metadata."""
    document = await _ensure_license_record(db)
    doc_id = _document_id(document)
    updates = {**_license_reset_fields(), "updatedAt": utc_now()}
    await db[LICENSE_COLLECTION].update_one({"_id": doc_id}, {"$set": updates})
    document = await db[LICENSE_COLLECTION].find_one({"_id": doc_id}) or {**document, **updates}
    return _serialize_license(document)


def _parse_offline_license_bytes(content: bytes) -> dict[str, Any]:
    if not content:
        raise LicenseSyncError("License file is empty.")
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise LicenseSyncError("License file must be UTF-8 JSON.") from exc
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise LicenseSyncError("License file is not valid JSON.") from exc
    if not isinstance(data, dict):
        raise LicenseSyncError("License file must contain a JSON object.")
    return data


def _validate_offline_license_envelope(data: dict[str, Any]) -> None:
    if data.get("format") != NEXXUS_OFFLINE_FORMAT:
        raise LicenseSyncError('Invalid license file (expected format "nexxus-offline-license").')
    if int(data.get("version") or 0) != 1:
        raise LicenseSyncError("Unsupported offline license version.")
    if data.get("algorithm") != NEXXUS_OFFLINE_ALGORITHM:
        raise LicenseSyncError(f'Unsupported algorithm (expected "{NEXXUS_OFFLINE_ALGORITHM}").')
    for field in ("appFingerprint", "licenseCode", "encryptedLicense"):
        if not str(data.get(field) or "").strip():
            raise LicenseSyncError(f'License file is missing "{field}".')


async def import_offline_license(db: AsyncIOMotorDatabase, *, content: bytes) -> LicenseResponse:
    """Import a Nexxus ``.lic`` file into the local license record (DB is source of truth)."""
    await ensure_license_collection(db)
    document = await _ensure_license_record(db)
    envelope = _parse_offline_license_bytes(content)
    _validate_offline_license_envelope(envelope)

    file_fingerprint = str(envelope["appFingerprint"]).strip()
    local_fingerprint = str(document.get("appFingerprint") or "").strip()
    if file_fingerprint != local_fingerprint:
        raise LicenseSyncError("License file fingerprint does not match this installation.")

    try:
        license_code = normalize_license_code(str(envelope["licenseCode"]))
    except ValueError as exc:
        raise LicenseSyncError(str(exc)) from exc

    encrypted = str(envelope["encryptedLicense"]).strip()
    try:
        payload = decrypt_nexxus_license_blob(
            encrypted,
            app_fingerprint=file_fingerprint,
            license_code=license_code,
        )
    except Exception as exc:
        raise LicenseSyncError(f"Could not decrypt license file: {exc}") from exc

    payload_fingerprint = str(payload.get("appFingerprint") or "").strip()
    if payload_fingerprint and payload_fingerprint != file_fingerprint:
        raise LicenseSyncError("Decrypted license fingerprint does not match the file.")

    payload_app = str(payload.get("appName") or payload.get("application") or "").strip()
    if not payload_app or not _is_jpilot_app_name(payload_app):
        raise LicenseSyncError(f"License is not for {_app_name()}.")

    cached = _cache_from_decrypted(payload)
    expiration = _expiration_from_payload(payload)
    if expiration:
        cached["expirationDate"] = expiration
    status = _license_status_from_expiration(expiration)
    message = (
        "License imported from offline file."
        if status == "active"
        else "Offline license has expired."
    )

    now = utc_now()
    updates: dict[str, Any] = {
        "encryptedLicenseCode": encrypt_value(license_code),
        "encryptedLicense": encrypted,
        "algorithm": str(envelope.get("algorithm") or NEXXUS_OFFLINE_ALGORITHM),
        "version": int(envelope.get("version") or 1),
        "status": status,
        "message": message,
        "syncError": None,
        "obtainedOffline": True,
        "offlineImportedAt": now,
        "renewalCount": int(payload.get("renewalCount") or document.get("renewalCount") or 0),
        "updatedAt": now,
    }
    _apply_sync_metadata(updates, cached)

    doc_id = _document_id(document)
    await db[LICENSE_COLLECTION].update_one({"_id": doc_id}, {"$set": updates})
    document = await db[LICENSE_COLLECTION].find_one({"_id": doc_id}) or {**document, **updates}

    return _serialize_license(document)
