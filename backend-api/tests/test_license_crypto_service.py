import base64
import json

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.services.license_crypto_service import (
    LICENSE_CRYPTO_VERSION,
    NONCE_LENGTH,
    decrypt_encrypted_license,
    decrypt_nexxus_license_blob,
    derive_nexxus_license_key,
)


def _encrypt_nexxus_blob(
    payload: dict,
    *,
    fingerprint: str,
    license_code: str,
    wrap_payload: bool = True,
) -> str:
    key = derive_nexxus_license_key(app_fingerprint=fingerprint, license_code=license_code)
    body = {"payload": payload} if wrap_payload else payload
    nonce = b"\x0a" * NONCE_LENGTH
    plaintext = json.dumps(body).encode("utf-8")
    ciphertext = AESGCM(key).encrypt(nonce, plaintext, None)
    raw = bytes([LICENSE_CRYPTO_VERSION]) + nonce + ciphertext
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def test_decrypt_nexxus_license_blob_roundtrip_with_payload_wrapper():
    inner = {
        "appFingerprint": "abc123",
        "appName": "JPilot",
        "licenseType": "free",
        "expirationDate": "2026-09-02T12:00:00Z",
        "name": "Test User",
        "email": "user@example.com",
    }
    encrypted = _encrypt_nexxus_blob(
        inner,
        fingerprint="abc123",
        license_code="A9KM-ULUA-RKUA-4SYI",
    )
    decrypted = decrypt_nexxus_license_blob(
        encrypted,
        app_fingerprint="abc123",
        license_code="A9KM-ULUA-RKUA-4SYI",
    )
    assert decrypted["licenseType"] == "free"
    assert decrypted["name"] == "Test User"


def test_decrypt_encrypted_license_accepts_dashed_code():
    payload = {
        "appFingerprint": "fp1",
        "application": "JPilot",
        "licenseType": "trial",
        "expirationDateUnix": 1893456000,
    }
    encrypted = _encrypt_nexxus_blob(
        payload,
        fingerprint="fp1",
        license_code="ABCD-EF12-3456-7890",
        wrap_payload=False,
    )
    decrypted = decrypt_encrypted_license(
        encrypted,
        app_fingerprint="fp1",
        app_name="JPilot",
        license_code="ABCD-EF12-3456-7890",
    )
    assert decrypted["licenseType"] == "trial"
