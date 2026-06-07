import datetime as dt

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

from app.services import tls_certificate_service as svc


def _generate_pem_pair(common_name: str = "jpilot.nexxus-tech.com") -> tuple[str, str]:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    now = dt.datetime.now(dt.timezone.utc)
    cert = (
        x509.CertificateBuilder()
        .subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, common_name)]))
        .issuer_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, common_name)]))
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - dt.timedelta(minutes=5))
        .not_valid_after(now + dt.timedelta(days=30))
        .sign(key, hashes.SHA256())
    )
    cert_pem = cert.public_bytes(serialization.Encoding.PEM).decode()
    key_pem = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.TraditionalOpenSSL,
        serialization.NoEncryption(),
    ).decode()
    return cert_pem, key_pem


def test_hostname_matches_exact_and_wildcard():
    assert svc._hostname_matches("jpilot.nexxus-tech.com", "jpilot.nexxus-tech.com", [])
    assert svc._hostname_matches("jpilot.nexxus-tech.com", "", ["*.nexxus-tech.com"])
    assert not svc._hostname_matches("jpilot.nexxus-tech.com", "other.example.com", [])


def test_inspect_certificate_material_rejects_mismatched_key():
    cert_pem, _ = _generate_pem_pair()
    _, other_key = _generate_pem_pair("other.example.com")
    with pytest.raises(ValueError, match="does not match"):
        svc.inspect_certificate_material(cert_pem, other_key)


def test_validate_and_apply_tls_certificate(tmp_path, monkeypatch):
    cert_pem, key_pem = _generate_pem_pair()
    monkeypatch.setenv("SSL_CERTS_PATH", str(tmp_path))
    monkeypatch.setenv("JPILOT_NGINX_RELOAD_SIGNAL", str(tmp_path / "reload-nginx"))
    monkeypatch.setenv("NGINX_HOSTNAME", "jpilot.nexxus-tech.com")
    monkeypatch.setattr(svc.settings, "nginx_hostname", "jpilot.nexxus-tech.com")

    validation = svc.validate_tls_certificate(cert_pem, key_pem)
    assert validation["ok"] is True
    assert validation["common_name"] == "jpilot.nexxus-tech.com"

    result = svc.apply_tls_certificate(cert_pem, key_pem)
    assert result["ok"] is True
    assert (tmp_path / "cert.crt").is_file()
    assert (tmp_path / "cert.key").is_file()
    assert (tmp_path / "reload-nginx").is_file()


def test_validate_tls_certificate_rejects_wrong_hostname(tmp_path, monkeypatch):
    cert_pem, key_pem = _generate_pem_pair("other.example.com")
    monkeypatch.setenv("SSL_CERTS_PATH", str(tmp_path))
    monkeypatch.setenv("NGINX_HOSTNAME", "jpilot.nexxus-tech.com")
    monkeypatch.setattr(svc.settings, "nginx_hostname", "jpilot.nexxus-tech.com")

    validation = svc.validate_tls_certificate(cert_pem, key_pem)
    assert validation["ok"] is False
    assert "does not cover" in validation["error"]
