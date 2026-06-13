import os
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.license_service import (
    LEGACY_LICENSE_COLLECTION,
    LEGACY_LICENSES_COLLECTION,
    LICENSE_COLLECTION,
    build_license_fingerprint,
    ensure_license_collection,
    licensefingerprint,
    normalize_license_code,
)


def test_build_license_fingerprint_is_deterministic():
    expected = build_license_fingerprint("fernet-key", "jpilot.example.com", "2026-06-04")
    assert expected == build_license_fingerprint("fernet-key", "jpilot.example.com", "2026-06-04")
    assert len(expected) == 64


def test_normalize_license_code_accepts_dashes_or_not():
    assert normalize_license_code("abcd-ef12-3456-7890") == "ABCD-EF12-3456-7890"
    assert normalize_license_code("abcdef1234567890") == "ABCD-EF12-3456-7890"


def test_normalize_license_code_rejects_wrong_length():
    with pytest.raises(ValueError):
        normalize_license_code("TOO-SHORT")


def test_ensure_license_collection_drops_legacy_and_creates_license():
    import asyncio

    drop_calls: list[str] = []

    def collection(name: str) -> MagicMock:
        coll = MagicMock()

        async def drop():
            drop_calls.append(name)

        coll.drop = drop
        return coll

    db = MagicMock()
    db.list_collection_names = AsyncMock(
        return_value=[LEGACY_LICENSE_COLLECTION, LEGACY_LICENSES_COLLECTION, "users"]
    )
    db.__getitem__ = MagicMock(side_effect=collection)
    db.create_collection = AsyncMock()

    asyncio.run(ensure_license_collection(db))

    assert LEGACY_LICENSE_COLLECTION in drop_calls
    assert LEGACY_LICENSES_COLLECTION in drop_calls
    db.create_collection.assert_awaited_once_with(LICENSE_COLLECTION)


def test_licensefingerprint_reads_configured_values():
    fixed_now = datetime(2026, 6, 4, 12, 0, 0, tzinfo=timezone.utc)
    with (
        patch("app.services.license_service.settings") as mock_settings,
        patch.dict(os.environ, {"NGINX_HOSTNAME": "jpilot.example.com"}, clear=False),
        patch("app.services.license_service.datetime") as mock_datetime,
    ):
        mock_settings.nsagent_encryption_key = "fernet-key"
        mock_settings.nginx_hostname = ""
        mock_settings.jpilot_app_name = "JPilot"
        mock_datetime.now.return_value = fixed_now
        mock_datetime.timezone = timezone

        result = licensefingerprint()

    assert result == {
        "nsagent_encryption_key": "fernet-key",
        "nginx_hostname": "jpilot.example.com",
        "date": "2026-06-04",
        "fingerprint": build_license_fingerprint("fernet-key", "jpilot.example.com", "2026-06-04"),
    }


def test_licensefingerprint_uses_activation_date_not_today():
    with (
        patch("app.services.license_service.settings") as mock_settings,
        patch.dict(os.environ, {"NGINX_HOSTNAME": "jpilot.example.com"}, clear=False),
    ):
        mock_settings.nsagent_encryption_key = "fernet-key"
        mock_settings.nginx_hostname = ""

        result = licensefingerprint("2026-06-01T08:30:00Z")

    assert result["date"] == "2026-06-01"
    assert result["fingerprint"] == build_license_fingerprint(
        "fernet-key", "jpilot.example.com", "2026-06-01"
    )


def test_find_license_document_matches_stored_activation_date():
    import asyncio

    activation = "2026-06-01T08:30:00Z"
    install_id = build_license_fingerprint("fernet-key", "jpilot.example.com", "2026-06-01")
    stored_doc = {
        "_id": install_id,
        "appFingerprint": install_id,
        "activationDate": activation,
        "appName": "JPilot",
    }

    coll = MagicMock()
    coll.find = MagicMock(
        return_value=MagicMock(
            to_list=AsyncMock(return_value=[stored_doc]),
        )
    )
    coll.find_one = AsyncMock(return_value=None)
    db = MagicMock()
    db.__getitem__ = MagicMock(return_value=coll)

    with (
        patch("app.services.license_service.settings") as mock_settings,
        patch.dict(os.environ, {"NGINX_HOSTNAME": "jpilot.example.com"}, clear=False),
        patch("app.services.license_service.datetime") as mock_datetime,
    ):
        mock_settings.nsagent_encryption_key = "fernet-key"
        mock_settings.nginx_hostname = ""
        mock_datetime.now.return_value = datetime(2026, 6, 12, 12, 0, 0, tzinfo=timezone.utc)
        mock_datetime.timezone = timezone

        from app.services.license_service import _find_license_document

        document = asyncio.run(_find_license_document(db))

    assert document is stored_doc


def test_ensure_license_record_inserts_default_document():
    import asyncio
    from app.services.license_service import _ensure_license_record

    db = MagicMock()
    db[LICENSE_COLLECTION].find_one = AsyncMock(return_value=None)
    db[LICENSE_COLLECTION].insert_one = AsyncMock()

    with patch("app.services.license_service.licensefingerprint") as mock_fp:
        mock_fp.return_value = {"fingerprint": "abc123"}
        doc = asyncio.run(_ensure_license_record(db))

    assert doc["_id"] == "abc123"
    assert doc["appFingerprint"] == "abc123"
    db[LICENSE_COLLECTION].insert_one.assert_awaited_once()


def test_remove_license_clears_code_keeps_fingerprint():
    import asyncio
    from unittest.mock import AsyncMock, MagicMock, patch

    from app.services.license_service import remove_license

    install_id = "abc123"
    stored_doc = {
        "_id": install_id,
        "appFingerprint": install_id,
        "appName": "JPilot",
        "activationDate": "2026-06-04T12:00:00Z",
        "encryptedLicenseCode": "enc:RKOP-BGRM-RSA7-CUBK",
        "encryptedLicense": "blob",
        "cachedLicense": {"licenseType": "free"},
        "status": "active",
        "createdAt": "2026-06-04T12:00:00Z",
    }

    async def fake_find_one(query):
        if query.get("_id") == install_id:
            return dict(stored_doc)
        return None

    async def fake_update_one(query, update):
        stored_doc.update(update.get("$set", {}))

    coll = MagicMock()
    coll.find_one = AsyncMock(side_effect=fake_find_one)
    coll.update_one = AsyncMock(side_effect=fake_update_one)
    coll.insert_one = AsyncMock()
    db = MagicMock()
    db.list_collection_names = AsyncMock(return_value=["license"])
    db.__getitem__ = MagicMock(return_value=coll)

    with (
        patch("app.services.license_service.licensefingerprint") as mock_fp,
        patch("app.services.license_service.decrypt_value", side_effect=lambda v: v.replace("enc:", "")),
        patch("app.services.license_service.encrypt_value", side_effect=lambda v: f"enc:{v}"),
    ):
        mock_fp.return_value = {"fingerprint": install_id}
        resp = asyncio.run(remove_license(db))

    assert resp.appFingerprint == install_id
    assert resp.activationDate == "2026-06-04T12:00:00Z"
    assert resp.hasLicenseCode is False
    assert resp.status == "pending"
    assert stored_doc["encryptedLicenseCode"] == ""
    assert stored_doc["cachedLicense"] is None
