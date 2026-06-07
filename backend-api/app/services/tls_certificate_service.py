from __future__ import annotations

import datetime as dt
import os
import re
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.x509.oid import NameOID

from app.config import settings

_CERT_FILE = "cert.crt"
_KEY_FILE = "cert.key"
_BACKUP_SUFFIX = ".bak"


def _ssl_dir() -> Path:
    return Path(os.environ.get("SSL_CERTS_PATH", "/var/jpilot/ssl"))


def _reload_signal_path() -> Path:
    return Path(os.environ.get("JPILOT_NGINX_RELOAD_SIGNAL", "/var/run/jpilot/reload-nginx"))


def _public_bytes(key) -> bytes:
    return key.public_bytes(
        serialization.Encoding.DER,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )


def _configured_hostname() -> str:
    return (settings.nginx_hostname or os.environ.get("NGINX_HOSTNAME", "")).strip()


def tls_management_available() -> bool:
    ssl_dir = _ssl_dir()
    try:
        ssl_dir.mkdir(parents=True, exist_ok=True)
    except OSError:
        return False
    return os.access(ssl_dir, os.W_OK)


def _hostname_matches(hostname: str, cn: str, subject_alt_names: list[str]) -> bool:
    host = hostname.strip().lower()
    if not host:
        return True

    def matches_pattern(pattern: str) -> bool:
        candidate = pattern.strip().lower()
        if not candidate:
            return False
        if candidate == host:
            return True
        if candidate.startswith("*."):
            suffix = candidate[1:]
            prefix = host[: -len(suffix)] if host.endswith(suffix) else ""
            return bool(prefix and "." not in prefix.rstrip("."))
        return False

    names: list[str] = []
    if cn:
        names.append(cn)
    names.extend(entry for entry in subject_alt_names if isinstance(entry, str))
    return any(matches_pattern(name) for name in names)


def inspect_certificate_material(certificate: str, private_key: str) -> dict:
    try:
        cert = x509.load_pem_x509_certificate(certificate.strip().encode())
    except Exception as exc:  # noqa: BLE001
        raise ValueError(f"Could not parse the certificate (expected PEM): {exc}") from exc

    try:
        key = serialization.load_pem_private_key(private_key.strip().encode(), password=None)
    except Exception as exc:  # noqa: BLE001
        raise ValueError(
            "Could not parse the private key. It must be an unencrypted PEM key."
        ) from exc

    if _public_bytes(cert.public_key()) != _public_bytes(key.public_key()):
        raise ValueError("The private key does not match the certificate.")

    not_after = cert.not_valid_after_utc
    now = dt.datetime.now(dt.timezone.utc)
    if not_after < now:
        raise ValueError(f"The certificate expired on {not_after:%Y-%m-%d}.")

    try:
        cn = cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value
    except IndexError:
        cn = ""
    try:
        san = [
            n.value
            for n in cert.extensions.get_extension_for_class(x509.SubjectAlternativeName).value
        ]
    except x509.ExtensionNotFound:
        san = []

    hostname = _configured_hostname()
    return {
        "common_name": cn or "",
        "subject_alt_names": san,
        "expires": not_after.strftime("%Y-%m-%d"),
        "expires_in_days": (not_after - now).days,
        "hostname": hostname,
        "hostname_matches": _hostname_matches(hostname, cn or "", san),
    }


def _read_installed_certificate() -> dict | None:
    cert_path = _ssl_dir() / _CERT_FILE
    if not cert_path.is_file():
        return None
    try:
        pem = cert_path.read_text(encoding="utf-8")
        cert = x509.load_pem_x509_certificate(pem.encode())
    except Exception:  # noqa: BLE001
        return None

    now = dt.datetime.now(dt.timezone.utc)
    not_after = cert.not_valid_after_utc
    try:
        cn = cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value
    except IndexError:
        cn = ""
    try:
        san = [
            n.value
            for n in cert.extensions.get_extension_for_class(x509.SubjectAlternativeName).value
        ]
    except x509.ExtensionNotFound:
        san = []

    return {
        "common_name": cn or "",
        "subject_alt_names": san,
        "expires": not_after.strftime("%Y-%m-%d"),
        "expires_in_days": (not_after - now).days,
    }


def get_tls_status() -> dict:
    hostname = _configured_hostname()
    available = tls_management_available()
    installed = _read_installed_certificate()
    if not available:
        return {
            "available": False,
            "hostname": hostname,
            "has_certificate": installed is not None,
            "message": "TLS files are not writable from the API container. Use nginx/ssl/ on the host or the installer.",
        }
    if not installed:
        return {
            "available": True,
            "hostname": hostname,
            "has_certificate": False,
            "message": "No certificate installed yet.",
        }
    return {
        "available": True,
        "hostname": hostname,
        "has_certificate": True,
        "common_name": installed["common_name"],
        "subject_alt_names": installed["subject_alt_names"],
        "expires": installed["expires"],
        "expires_in_days": installed["expires_in_days"],
        "message": "",
    }


def validate_tls_certificate(certificate: str, private_key: str, chain: str = "") -> dict:
    if not tls_management_available():
        return {
            "ok": False,
            "hostname": _configured_hostname(),
            "error": "TLS management is not available in this deployment.",
        }
    try:
        info = inspect_certificate_material(certificate, private_key)
    except ValueError as exc:
        return {
            "ok": False,
            "hostname": _configured_hostname(),
            "error": str(exc),
        }

    result = {"ok": True, "error": "", **info}
    if info["hostname"] and not info["hostname_matches"]:
        result["ok"] = False
        result["error"] = (
            f"Certificate does not cover NGINX_HOSTNAME ({info['hostname']}). "
            "Check the CN or Subject Alternative Names."
        )
    if chain.strip():
        try:
            for block in re.findall(
                r"-----BEGIN CERTIFICATE-----.*?-----END CERTIFICATE-----",
                chain,
                flags=re.DOTALL,
            ):
                x509.load_pem_x509_certificate(block.encode())
        except Exception as exc:  # noqa: BLE001
            return {
                "ok": False,
                "hostname": _configured_hostname(),
                "error": f"Could not parse the intermediate chain (expected PEM): {exc}",
            }
    return result


def _build_cert_chain(certificate: str, chain: str = "") -> str:
    parts = [certificate.strip()]
    if chain.strip():
        parts.append(chain.strip())
    return "\n".join(part for part in parts if part) + "\n"


def _backup_file(path: Path) -> None:
    if not path.is_file():
        return
    backup = path.with_suffix(path.suffix + _BACKUP_SUFFIX)
    backup.write_bytes(path.read_bytes())


def _write_private_key(path: Path, private_key: str) -> None:
    path.write_text(private_key.strip() + "\n", encoding="utf-8")
    os.chmod(path, 0o600)


def _write_certificate(path: Path, certificate: str) -> None:
    path.write_text(certificate, encoding="utf-8")
    os.chmod(path, 0o644)


def request_nginx_reload() -> bool:
    signal = _reload_signal_path()
    try:
        signal.parent.mkdir(parents=True, exist_ok=True)
        signal.write_text(dt.datetime.now(dt.timezone.utc).isoformat(), encoding="utf-8")
        return True
    except OSError:
        return False


def apply_tls_certificate(certificate: str, private_key: str, chain: str = "") -> dict:
    validation = validate_tls_certificate(certificate, private_key, chain)
    if not validation.get("ok"):
        return {
            "ok": False,
            "error": validation.get("error") or "Certificate validation failed.",
            "hostname": validation.get("hostname") or _configured_hostname(),
            "nginx_reloaded": False,
            "message": "",
        }

    ssl_dir = _ssl_dir()
    cert_path = ssl_dir / _CERT_FILE
    key_path = ssl_dir / _KEY_FILE
    try:
        _backup_file(cert_path)
        _backup_file(key_path)
        _write_certificate(cert_path, _build_cert_chain(certificate, chain))
        _write_private_key(key_path, private_key)
    except OSError as exc:
        return {
            "ok": False,
            "error": f"Could not write certificate files: {exc}",
            "hostname": validation.get("hostname") or _configured_hostname(),
            "nginx_reloaded": False,
            "message": "",
        }

    reloaded = request_nginx_reload()
    message = "Certificate installed."
    if reloaded:
        message += " nginx reload requested."
    else:
        message += " Run `./compose.sh exec nginx nginx -s reload` if HTTPS does not update."

    return {
        "ok": True,
        "error": "",
        "common_name": validation.get("common_name", ""),
        "expires": validation.get("expires", ""),
        "expires_in_days": validation.get("expires_in_days", 0),
        "hostname": validation.get("hostname") or _configured_hostname(),
        "nginx_reloaded": reloaded,
        "message": message,
    }
