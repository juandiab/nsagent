import base64
import json
from datetime import datetime, timezone

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.services.license_crypto_service import (
    LICENSE_CRYPTO_VERSION,
    NEXXUS_OFFLINE_ALGORITHM,
    NEXXUS_OFFLINE_FORMAT,
    NONCE_LENGTH,
    derive_nexxus_license_key,
)
from app.services.license_service import (
    _license_status_from_expiration,
    _parse_offline_license_bytes,
    _should_sync_with_server,
    _validate_offline_license_envelope,
    import_offline_license,
)


def _build_lic_file(
    *,
    fingerprint: str = "install-fp",
    license_code: str = "RKOP-BGRM-RSA7-CUBK",
    inner: dict | None = None,
) -> bytes:
    inner = inner or {
        "appFingerprint": fingerprint,
        "appName": "JPilot",
        "licenseType": "free",
        "expirationDate": "2099-01-01T00:00:00Z",
        "name": "Jane Doe",
        "email": "jane@example.com",
        "company": "Acme",
    }
    key = derive_nexxus_license_key(app_fingerprint=fingerprint, license_code=license_code)
    nonce = b"\x05" * NONCE_LENGTH
    plaintext = json.dumps({"payload": inner}).encode("utf-8")
    ciphertext = AESGCM(key).encrypt(nonce, plaintext, None)
    raw = bytes([LICENSE_CRYPTO_VERSION]) + nonce + ciphertext
    encrypted = base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")
    envelope = {
        "format": NEXXUS_OFFLINE_FORMAT,
        "version": 1,
        "algorithm": NEXXUS_OFFLINE_ALGORITHM,
        "appFingerprint": fingerprint,
        "appName": "JPilot",
        "licenseCode": license_code,
        "encryptedLicense": encrypted,
        "exportedAt": "2026-06-04T22:43:28Z",
    }
    return json.dumps(envelope).encode("utf-8")


def test_parse_and_validate_offline_envelope():
    data = json.loads(_build_lic_file())
    _validate_offline_license_envelope(data)
    assert data["format"] == NEXXUS_OFFLINE_FORMAT


def test_should_sync_skipped_for_offline_license():
    doc = {
        "appFingerprint": "fp",
        "encryptedLicenseCode": "enc:ABCD-EF12-3456-7890",
        "obtainedOffline": True,
    }
    assert _should_sync_with_server(doc) is False


def test_license_status_from_expiration():
    future = "2099-01-01T00:00:00Z"
    past = "2020-01-01T00:00:00Z"
    assert _license_status_from_expiration(future) == "active"
    assert _license_status_from_expiration(past) == "expired"


def test_import_offline_license():
    import asyncio
    from unittest.mock import AsyncMock, MagicMock, patch

    lic_bytes = _build_lic_file(fingerprint="abc123")
    envelope = _parse_offline_license_bytes(lic_bytes)

    stored: dict = {}

    install_id = "abc123"

    async def fake_find_one(query):
        if query.get("_id") in (install_id, "default"):
            return stored.get("doc")
        return None

    async def fake_update_one(query, update):
        doc = stored.get("doc") or {"_id": install_id, "appFingerprint": install_id, "appName": "JPilot"}
        doc.update(update.get("$set", {}))
        stored["doc"] = doc

    async def fake_insert_one(doc):
        stored["doc"] = doc

    coll = MagicMock()
    coll.find_one = AsyncMock(side_effect=fake_find_one)
    coll.update_one = AsyncMock(side_effect=fake_update_one)
    coll.insert_one = AsyncMock(side_effect=fake_insert_one)
    coll.drop = AsyncMock()
    db = MagicMock()
    db.list_collection_names = AsyncMock(return_value=["license"])
    db.__getitem__ = MagicMock(return_value=coll)

    sync_mock = AsyncMock(return_value=stored.get("doc"))
    with (
        patch("app.services.license_service.licensefingerprint") as mock_fp,
        patch("app.services.license_service.sync_license", sync_mock),
        patch("app.services.license_service.encrypt_value", side_effect=lambda v: f"enc:{v}"),
        patch("app.services.license_service.decrypt_value", side_effect=lambda v: v.replace("enc:", "")),
    ):
        mock_fp.return_value = {"fingerprint": "abc123"}
        stored["doc"] = {
            "_id": install_id,
            "appFingerprint": install_id,
            "appName": "JPilot",
            "activationDate": datetime.now(timezone.utc).isoformat(),
            "encryptedLicenseCode": "",
            "encryptedLicense": "",
            "status": "pending",
        }
        resp = asyncio.run(import_offline_license(db, content=lic_bytes))

    sync_mock.assert_not_called()
    assert resp.hasLicenseCode is True
    assert resp.obtainedOffline is True
    assert resp.status == "active"
    assert resp.details is not None
    assert resp.details.customerName == "Jane Doe"
    assert resp.details.customerEmail == "jane@example.com"
    assert resp.details.company == "Acme"
    assert envelope["appFingerprint"] == "abc123"
