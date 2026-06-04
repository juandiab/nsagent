from __future__ import annotations

import base64
import json
import re
from typing import Any

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

LICENSE_CRYPTO_VERSION = 1
NONCE_LENGTH = 12
KEY_LENGTH = 32
NEXXUS_OFFLINE_FORMAT = "nexxus-offline-license"
NEXXUS_OFFLINE_ALGORITHM = "AES-256-GCM+HKDF-SHA256"
NEXXUS_OFFLINE_SALT = b"nexxus-tech-license-v1"
NEXXUS_OFFLINE_INFO = b"license-payload"


def _urlsafe_b64decode(value: str) -> bytes:
    padded = value + "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(padded.encode("ascii"))


def _hkdf_derive(*, ikm: bytes, salt: bytes, info: bytes) -> bytes:
    return HKDF(algorithm=hashes.SHA256(), length=KEY_LENGTH, salt=salt, info=info).derive(ikm)


def normalize_license_code_for_crypto(license_code: str) -> str:
    """Uppercase alphanumeric only (no hyphens), for Nexxus HKDF ikm."""
    return re.sub(r"[^A-Za-z0-9]", "", (license_code or "").strip()).upper()


def derive_nexxus_license_key(*, app_fingerprint: str, license_code: str) -> bytes:
    """Nexxus ``AES-256-GCM+HKDF-SHA256`` offline / sync payload key (v1)."""
    normalized = normalize_license_code_for_crypto(license_code)
    ikm = f"{app_fingerprint.strip()}:{normalized}".encode("utf-8")
    return _hkdf_derive(ikm=ikm, salt=NEXXUS_OFFLINE_SALT, info=NEXXUS_OFFLINE_INFO)


def _unwrap_license_payload(parsed: dict[str, Any]) -> dict[str, Any]:
    inner = parsed.get("payload")
    if isinstance(inner, dict):
        return inner
    return parsed


def decrypt_nexxus_license_blob(
    encrypted_license: str,
    *,
    app_fingerprint: str,
    license_code: str,
) -> dict[str, Any]:
    """
    Decrypt Nexxus ``encryptedLicense`` (version byte + 12-byte nonce + AES-GCM ciphertext).
    Returns the inner license ``payload`` object when present.
    """
    if not encrypted_license.strip():
        raise ValueError("encryptedLicense is empty.")
    if not license_code:
        raise ValueError("License code is required to decrypt the license payload.")

    raw = _urlsafe_b64decode(encrypted_license.strip())
    if len(raw) <= 1 + NONCE_LENGTH:
        raise ValueError("encryptedLicense blob is too short.")
    if raw[0] != LICENSE_CRYPTO_VERSION:
        raise ValueError(f"Unsupported license blob version: {raw[0]}.")

    nonce = raw[1 : 1 + NONCE_LENGTH]
    ciphertext = raw[1 + NONCE_LENGTH :]
    key = derive_nexxus_license_key(
        app_fingerprint=app_fingerprint,
        license_code=license_code,
    )
    plaintext = AESGCM(key).decrypt(nonce, ciphertext, None)
    parsed = json.loads(plaintext.decode("utf-8"))
    if not isinstance(parsed, dict):
        raise ValueError("Decrypted license payload must be a JSON object.")
    return _unwrap_license_payload(parsed)


def decrypt_encrypted_license(
    encrypted_license: str,
    *,
    app_fingerprint: str,
    app_name: str,
    license_code: str,
    version: int = LICENSE_CRYPTO_VERSION,
    activation_date: str | None = None,
) -> dict[str, Any]:
    """Decrypt ``encryptedLicense`` from Nexxus sync or offline ``.lic`` files."""
    del app_name, version, activation_date  # v1 Nexxus derivation uses fingerprint + code only
    return decrypt_nexxus_license_blob(
        encrypted_license,
        app_fingerprint=app_fingerprint,
        license_code=license_code,
    )
