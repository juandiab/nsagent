"""Generate SSL keys, CSRs, and self-signed certificates on NetScaler."""

from __future__ import annotations

import re
import shlex
from dataclasses import dataclass
from typing import Any

_SSL_FILENAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,62}$")
_DNS_NAME_RE = re.compile(
    r"^(?:\*\.)?(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*)$"
)
_IPV4_RE = re.compile(
    r"^(?:(?:25[0-5]|2[0-4]\d|[01]?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d?\d)$"
)
_CSR_PEM_RE = re.compile(
    r"-----BEGIN CERTIFICATE REQUEST-----[\s\S]+?-----END CERTIFICATE REQUEST-----",
    re.MULTILINE,
)
_CERT_PEM_RE = re.compile(
    r"-----BEGIN CERTIFICATE-----[\s\S]+?-----END CERTIFICATE-----",
    re.MULTILINE,
)
_SUBJECT_UNSAFE_RE = re.compile(r"[\r\n\x00]")


@dataclass
class SslSubjectContext:
    key_name: str
    cert_type: str
    key_type: str
    key_size: int
    key_password: str | None
    common_name: str
    country: str
    state: str
    locality: str
    organization: str
    organizational_unit: str
    email: str
    subject_alt_names: list[str]
    validity_days: int


def _escape_openssl_subj(value: str) -> str:
    return value.replace("\\", "\\\\").replace("/", r"\/").replace(",", r"\,")


def _cli_quote(value: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        return '""'
    if re.search(r'[\s"]', cleaned):
        return '"' + cleaned.replace('"', r"\"") + '"'
    return cleaned


def _validate_subject_field(name: str, value: str, *, required: bool = False) -> str:
    cleaned = (value or "").strip()
    if not cleaned:
        if required:
            raise ValueError(f"{name} is required")
        return ""
    if _SUBJECT_UNSAFE_RE.search(cleaned):
        raise ValueError(f"{name} contains invalid characters")
    if len(cleaned) > 128:
        raise ValueError(f"{name} must be 128 characters or fewer")
    return cleaned


def _normalize_key_basename(key_name: str) -> str:
    base = (key_name or "").strip()
    if not base:
        raise ValueError("key_name is required")
    for suffix in (".key", ".pem", ".csr", ".crt", ".cert"):
        if base.lower().endswith(suffix):
            base = base[: -len(suffix)]
            break
    if not _SSL_FILENAME_RE.fullmatch(base):
        raise ValueError(
            "key_name must start with a letter or digit and contain only letters, digits, dots, dashes, or underscores"
        )
    return base


def _validate_dns_or_ip(value: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ValueError("SAN entry cannot be empty")
    if _IPV4_RE.fullmatch(cleaned):
        return cleaned
    if _DNS_NAME_RE.fullmatch(cleaned):
        return cleaned
    raise ValueError(f"Invalid SAN entry: {cleaned}")


def _validate_common_name(common_name: str, cert_type: str) -> str:
    cn = _validate_subject_field("common_name", common_name, required=True)
    if cert_type == "wildcard":
        if not cn.startswith("*."):
            raise ValueError("Wildcard certificates require common_name to start with *.")
        domain = cn[2:]
        if not _DNS_NAME_RE.fullmatch(cn) and not _DNS_NAME_RE.fullmatch(domain):
            raise ValueError("Invalid wildcard common_name")
    elif not _DNS_NAME_RE.fullmatch(cn) and not _IPV4_RE.fullmatch(cn):
        raise ValueError("Invalid common_name — use a DNS name or IPv4 address")
    return cn


def _validate_key_password(password: str | None) -> str | None:
    if password is None:
        return None
    cleaned = password.strip()
    if not cleaned:
        return None
    if "'" in cleaned or "\\" in cleaned or "\n" in cleaned or "\r" in cleaned:
        raise ValueError("Key password cannot contain quotes, backslashes, or newlines")
    if '"' in cleaned:
        raise ValueError("Key password cannot contain double quotes")
    if len(cleaned) > 128:
        raise ValueError("Key password must be 128 characters or fewer")
    return cleaned


def _collect_san_entries(cert_type: str, common_name: str, raw_sans: Any) -> list[str]:
    sans: list[str] = []
    if isinstance(raw_sans, str):
        raw_sans = [part.strip() for part in raw_sans.replace("\n", ",").split(",")]
    for entry in raw_sans or []:
        if not str(entry).strip():
            continue
        sans.append(_validate_dns_or_ip(str(entry)))

    if cert_type == "san" and not sans:
        raise ValueError("At least one subject_alt_names entry is required for SAN certificates")

    san_entries = list(sans)
    if cert_type in {"wildcard", "san"} and common_name not in san_entries:
        san_entries.insert(0, common_name)
    return san_entries


def parse_ssl_subject_context(params: dict[str, Any]) -> SslSubjectContext:
    key_name = _normalize_key_basename(str(params.get("key_name", "")))
    cert_type = str(params.get("cert_type", "standard")).strip().lower()
    key_type = str(params.get("key_type", "rsa")).strip().lower()
    key_size = int(params.get("key_size", 2048))
    key_password = _validate_key_password(params.get("key_password"))
    validity_days = int(params.get("validity_days", 365))

    if cert_type not in {"standard", "wildcard", "san"}:
        raise ValueError("cert_type must be standard, wildcard, or san")
    if key_type not in {"rsa", "ecdsa"}:
        raise ValueError("key_type must be rsa or ecdsa")
    if validity_days < 1 or validity_days > 3650:
        raise ValueError("validity_days must be between 1 and 3650")

    common_name = _validate_common_name(str(params.get("common_name", "")), cert_type)
    country = _validate_subject_field("country", str(params.get("country", "US")), required=True)
    state = _validate_subject_field("state", str(params.get("state", "")))
    locality = _validate_subject_field("locality", str(params.get("locality", "")))
    organization = _validate_subject_field("organization", str(params.get("organization", "")))
    organizational_unit = _validate_subject_field(
        "organizational_unit", str(params.get("organizational_unit", ""))
    )
    email = _validate_subject_field("email", str(params.get("email") or ""))
    subject_alt_names = _collect_san_entries(
        cert_type,
        common_name,
        params.get("subject_alt_names") or [],
    )

    if key_type == "rsa":
        if key_size not in {2048, 3072, 4096}:
            raise ValueError("RSA key_size must be 2048, 3072, or 4096")
    else:
        key_size = 256

    return SslSubjectContext(
        key_name=key_name,
        cert_type=cert_type,
        key_type=key_type,
        key_size=key_size,
        key_password=key_password,
        common_name=common_name,
        country=country,
        state=state,
        locality=locality,
        organization=organization,
        organizational_unit=organizational_unit,
        email=email,
        subject_alt_names=subject_alt_names,
        validity_days=validity_days,
    )


def _openssl_subject(context: SslSubjectContext) -> str:
    subj_parts = [f"C={_escape_openssl_subj(context.country)}"]
    if context.state:
        subj_parts.append(f"ST={_escape_openssl_subj(context.state)}")
    if context.locality:
        subj_parts.append(f"L={_escape_openssl_subj(context.locality)}")
    if context.organization:
        subj_parts.append(f"O={_escape_openssl_subj(context.organization)}")
    if context.organizational_unit:
        subj_parts.append(f"OU={_escape_openssl_subj(context.organizational_unit)}")
    subj_parts.append(f"CN={_escape_openssl_subj(context.common_name)}")
    if context.email:
        subj_parts.append(f"emailAddress={_escape_openssl_subj(context.email)}")
    return "/" + "/".join(subj_parts)


def _openssl_keygen(context: SslSubjectContext, key_file: str) -> tuple[str, str]:
    if context.key_type == "rsa":
        if context.key_password:
            pass_arg = shlex.quote(f"pass:{context.key_password}")
            keygen = f"openssl genrsa -aes256 -passout {pass_arg} -out {shlex.quote(key_file)} {context.key_size}"
            passin = f"-passin {pass_arg}"
        else:
            keygen = f"openssl genrsa -out {shlex.quote(key_file)} {context.key_size}"
            passin = ""
    elif context.key_password:
        pass_arg = shlex.quote(f"pass:{context.key_password}")
        keygen = (
            f"openssl ecparam -name prime256v1 -genkey | "
            f"openssl ec -aes256 -passout {pass_arg} -out {shlex.quote(key_file)}"
        )
        passin = f"-passin {pass_arg}"
    else:
        keygen = f"openssl ecparam -name prime256v1 -genkey -noout -out {shlex.quote(key_file)}"
        passin = ""
    return keygen, passin


def _openssl_san_extension(context: SslSubjectContext) -> str:
    if not context.subject_alt_names:
        return ""
    san_values = []
    for entry in context.subject_alt_names:
        prefix = "IP" if _IPV4_RE.fullmatch(entry) else "DNS"
        san_values.append(f"{prefix}:{entry}")
    return f"-addext {shlex.quote('subjectAltName=' + ','.join(san_values))}"


def build_openssl_csr_shell_script(params: dict[str, Any]) -> dict[str, str]:
    """Build a scoped shell script that creates key + CSR under /nsconfig/ssl."""
    context = parse_ssl_subject_context(params)
    key_file = f"{context.key_name}.key"
    csr_file = f"{context.key_name}.csr"
    key_path = f"/nsconfig/ssl/{key_file}"
    csr_path = f"/nsconfig/ssl/{csr_file}"
    subj = _openssl_subject(context)
    keygen, passin = _openssl_keygen(context, key_file)
    addext = _openssl_san_extension(context)

    req_cmd = (
        f"openssl req -new -key {shlex.quote(key_file)} {passin} "
        f"-out {shlex.quote(csr_file)} -subj {shlex.quote(subj)} {addext}".strip()
    )
    script = (
        f"cd /nsconfig/ssl && "
        f"{keygen} && "
        f"{req_cmd} && "
        f"cat {shlex.quote(csr_file)}"
    )

    return {
        "script": script,
        "key_name": context.key_name,
        "key_path": key_path,
        "csr_path": csr_path,
        "key_file": key_file,
        "csr_file": csr_file,
        "common_name": context.common_name,
        "cert_type": context.cert_type,
        "key_type": context.key_type,
    }


def _netscaler_certreq_subject(context: SslSubjectContext) -> dict[str, str]:
    """NetScaler create ssl certReq requires countryName, stateName, and organizationName."""
    return {
        "country": context.country,
        "state": context.state or "NA",
        "organization": context.organization or "Default Organization",
        "organizational_unit": context.organizational_unit,
        "locality": context.locality,
        "common_name": context.common_name,
        "email": context.email,
    }


def build_netscaler_self_signed_plan(params: dict[str, Any]) -> dict[str, Any]:
    """Build NetScaler classic CLI commands for a self-signed certificate."""
    context = parse_ssl_subject_context(params)
    subject = _netscaler_certreq_subject(context)
    key_file = context.key_name
    req_file = f"{context.key_name}_req"
    cert_file = f"{context.key_name}_cert"
    key_path = f"/nsconfig/ssl/{key_file}"
    req_path = f"/nsconfig/ssl/{req_file}"
    cert_path = f"/nsconfig/ssl/{cert_file}"

    if context.key_type == "rsa":
        key_cmd = (
            f"create ssl rsakey {key_file} {context.key_size} -exponent F4 -keyform PEM"
        )
    else:
        key_cmd = f"create ssl ecdsakey {key_file} P_256 -keyform PEM"

    if context.key_password:
        key_cmd += f" -password {_cli_quote(context.key_password)}"

    req_parts = [
        f"create ssl certReq {req_file}",
        f"-keyFile {key_file}",
        "-keyForm PEM",
        f"-countryName {_cli_quote(subject['country'])}",
        f"-stateName {_cli_quote(subject['state'])}",
        f"-organizationName {_cli_quote(subject['organization'])}",
        f"-commonName {_cli_quote(subject['common_name'])}",
    ]
    if subject["organizational_unit"]:
        req_parts.append(f"-organizationUnitName {_cli_quote(subject['organizational_unit'])}")
    if subject["locality"]:
        req_parts.append(f"-localityName {_cli_quote(subject['locality'])}")
    if subject["email"]:
        req_parts.append(f"-emailAddress {_cli_quote(subject['email'])}")
    if context.subject_alt_names:
        san_values = []
        for entry in context.subject_alt_names:
            prefix = "IP" if _IPV4_RE.fullmatch(entry) else "DNS"
            san_values.append(f"{prefix}:{entry}")
        req_parts.append(f'-subjectAltName "{",".join(san_values)}"')

    cert_parts = [
        f"create ssl cert {cert_file} {req_file} ROOT_CERT",
        f"-keyFile {key_file}",
        f"-days {context.validity_days}",
    ]
    if context.key_password:
        cert_parts.append(f"-password {_cli_quote(context.key_password)}")

    certkey_name = context.key_name
    certkey_parts = [
        f"add ssl certKey {certkey_name}",
        f"-cert {cert_file}",
        f"-key {key_file}",
    ]
    if context.key_password:
        certkey_parts.append(f"-passcrypt {_cli_quote(context.key_password)}")

    return {
        "commands": [
            key_cmd,
            " ".join(req_parts),
            " ".join(cert_parts),
            " ".join(certkey_parts),
        ],
        "key_name": context.key_name,
        "certkey_name": certkey_name,
        "key_path": key_path,
        "req_path": req_path,
        "cert_path": cert_path,
        "cert_file": cert_file,
        "common_name": context.common_name,
        "cert_type": context.cert_type,
        "key_type": context.key_type,
        "validity_days": context.validity_days,
    }


def extract_csr_pem(output: str) -> str:
    match = _CSR_PEM_RE.search(output or "")
    if not match:
        raise ValueError("CSR was not found in appliance output — OpenSSL may have failed")
    return _normalize_pem(match.group(0))


def extract_cert_pem(output: str) -> str:
    match = _CERT_PEM_RE.search(output or "")
    if not match:
        raise ValueError("Certificate was not found in appliance output")
    return _normalize_pem(match.group(0))


def _normalize_pem(pem: str) -> str:
    lines = [line.strip() for line in pem.strip().splitlines() if line.strip()]
    return "\n".join(lines) + "\n"
