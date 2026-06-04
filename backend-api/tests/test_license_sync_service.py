import base64
import json
from unittest.mock import patch

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.services.license_crypto_service import LICENSE_CRYPTO_VERSION, NONCE_LENGTH, derive_nexxus_license_key
from app.services.license_service import _apply_sync_result, _extract_sync_metadata
from app.services.license_sync_service import LicenseSyncResult, normalize_license_sync_payload


def _encrypt_sync_blob(payload: dict, *, fingerprint: str, license_code: str) -> str:
    key = derive_nexxus_license_key(app_fingerprint=fingerprint, license_code=license_code)
    nonce = b"\x0b" * NONCE_LENGTH
    plaintext = json.dumps({"payload": payload}).encode("utf-8")
    ciphertext = AESGCM(key).encrypt(nonce, plaintext, None)
    raw = bytes([LICENSE_CRYPTO_VERSION]) + nonce + ciphertext
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def test_apply_sync_success_decrypts_cache():
    document = {
        "appFingerprint": "fp",
        "appName": "JPilot",
        "encryptedLicenseCode": "",
        "renewalCount": 0,
    }
    # Without license code, decrypt is skipped; only server fields apply.
    result = LicenseSyncResult(
        200,
        {
            "status": "active",
            "message": "",
            "renewalCount": 1,
            "version": 1,
            "algorithm": "AES-256-GCM+HKDF-SHA256",
        },
    )
    updates = _apply_sync_result(document, result)
    assert updates["status"] == "active"
    assert updates["renewalCount"] == 1
    assert updates["syncError"] is None


def test_apply_sync_expired_keeps_metadata():
    document = {"status": "active", "cachedLicense": {"licenseType": "free", "customerName": "Ada"}}
    result = LicenseSyncResult(
        403,
        {
            "status": "expired",
            "message": "Trial expired.",
            "licenseType": "trial",
            "expirationDate": "2026-06-04T12:00:00Z",
        },
    )
    updates = _apply_sync_result(document, result)
    assert updates["status"] == "expired"
    assert updates["licenseType"] == "trial"
    assert updates["expirationDate"] == "2026-06-04T12:00:00Z"
    assert updates["cachedLicense"]["customerName"] == "Ada"
    assert updates["encryptedLicense"] == ""


def test_normalize_license_sync_payload_flattens_detail_object():
    payload = {
        "detail": {
            "status": "expired",
            "message": "License expired.",
            "licenseType": "free",
            "expirationDate": "2026-06-04T22:50:48.776000Z",
        }
    }
    normalized = normalize_license_sync_payload(payload)
    assert normalized["status"] == "expired"
    assert normalized["licenseType"] == "free"


def test_extract_sync_metadata_parses_renewal_message():
    meta = _extract_sync_metadata(
        {"status": "renewed"},
        message="Your free license was renewed until 2026-09-02T12:00:00Z.",
    )
    assert meta["expirationDate"] == "2026-09-02T12:00:00Z"


def test_apply_sync_missing_clears_cache():
    result = LicenseSyncResult(404, {"status": "missing", "message": "No license found."})
    updates = _apply_sync_result({"cachedLicense": {"x": 1}}, result)
    assert updates["status"] == "missing"
    assert updates["cachedLicense"] is None


def test_apply_sync_deactivated():
    result = LicenseSyncResult(
        403,
        {"status": "deactivated", "message": "License was deactivated."},
    )
    updates = _apply_sync_result({}, result)
    assert updates["status"] == "deactivated"
    assert updates["cachedLicense"] is None


def test_apply_sync_success_overwrites_stale_expiration_and_type():
    document = {
        "appFingerprint": "fp",
        "appName": "JPilot",
        "licenseType": "trial",
        "expirationDate": "2026-01-01T00:00:00Z",
        "encryptedLicenseCode": "enc:ABCD-EF12-3456-7890",
        "renewalCount": 0,
    }
    result = LicenseSyncResult(
        200,
        {
            "status": "active",
            "message": "",
            "licenseType": "enterprise",
            "expirationDate": "2027-06-01T12:00:00Z",
            "registrationDate": "2025-01-15T10:00:00Z",
            "validityDays": 90,
            "renewalCount": 2,
        },
    )
    with patch(
        "app.services.license_service.decrypt_value",
        side_effect=lambda v: v.replace("enc:", ""),
    ):
        updates = _apply_sync_result(document, result)
    assert updates["licenseType"] == "enterprise"
    assert updates["expirationDate"] == "2027-06-01T12:00:00Z"
    assert updates["registrationDate"] == "2025-01-15T10:00:00Z"
    assert updates["validityDays"] == 90
    assert updates["renewalCount"] == 2


def test_apply_sync_prefers_encrypted_payload_over_top_level():
    fingerprint = "fp"
    license_code = "ABCD-EF12-3456-7890"
    encrypted = _encrypt_sync_blob(
        {
            "licenseType": "enterprise",
            "expirationDate": "2027-12-31T23:59:59Z",
            "validityDays": 365,
            "registrationDate": "2025-06-01T08:00:00Z",
        },
        fingerprint=fingerprint,
        license_code=license_code,
    )
    document = {
        "appFingerprint": fingerprint,
        "appName": "JPilot",
        "encryptedLicenseCode": f"enc:{license_code}",
        "licenseType": "trial",
        "expirationDate": "2026-01-01T00:00:00Z",
    }
    result = LicenseSyncResult(
        200,
        {
            "status": "active",
            "message": "",
            "licenseType": "trial",
            "expirationDate": "2026-06-01T00:00:00Z",
            "validityDays": 30,
            "encryptedLicense": encrypted,
            "version": 1,
            "algorithm": "AES-256-GCM+HKDF-SHA256",
        },
    )
    with patch(
        "app.services.license_service.decrypt_value",
        side_effect=lambda v: v.replace("enc:", ""),
    ):
        updates = _apply_sync_result(document, result)
    assert updates["licenseType"] == "enterprise"
    assert updates["expirationDate"] == "2027-12-31T23:59:59Z"
    assert updates["validityDays"] == 365
    assert updates["registrationDate"] == "2025-06-01T08:00:00Z"


def test_apply_sync_marks_expired_when_past_expiration_date():
    document = {
        "appFingerprint": "fp",
        "status": "active",
        "expirationDate": "2020-01-01T00:00:00Z",
    }
    result = LicenseSyncResult(
        200,
        {
            "status": "active",
            "message": "",
            "expirationDate": "2020-01-01T00:00:00Z",
        },
    )
    updates = _apply_sync_result(document, result)
    assert updates["status"] == "expired"
