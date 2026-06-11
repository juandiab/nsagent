"""NSAgent / JPilot first-run web installer.

A tiny, self-contained FastAPI service that collects setup values, generates secrets
and a TLS certificate, writes the project `.env` and `nginx/ssl/` files, and drops a
sentinel file. The host-side `install.sh` watches for the sentinel and launches the
real stack (this service intentionally does NOT touch Docker).
"""
from __future__ import annotations

import datetime as dt
import html
import ipaddress
import os
import re
import secrets
import ssl
import time
import urllib.error
import urllib.request
from pathlib import Path

from cryptography import x509
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

WORKSPACE = Path(os.environ.get("WORKSPACE", "/workspace"))
STATIC_DIR = Path(__file__).parent / "static"
LEGAL_DIR = Path(__file__).parent / "legal"
if not LEGAL_DIR.exists():
    LEGAL_DIR = WORKSPACE / "frontend" / "src" / "legal"

LEGAL_DOCS = {
    "terms": ("Terms of Service", "terms-of-service.md"),
    "privacy": ("Privacy Policy", "privacy-policy.md"),
    "eula": ("EULA", "eula.md"),
    "acceptable-use": ("Acceptable Use Policy", "acceptable-use-policy.md"),
}

ENV_PATH = WORKSPACE / ".env"
SSL_DIR = WORKSPACE / "nginx" / "ssl"
CERT_PATH = SSL_DIR / "cert.crt"
KEY_PATH = SSL_DIR / "cert.key"
SENTINEL_PATH = WORKSPACE / ".installer-complete"

DOMAIN_RE = re.compile(
    r"^(?=.{1,253}$)(localhost|"
    r"(\d{1,3}\.){3}\d{1,3}|"
    r"([a-zA-Z0-9](-?[a-zA-Z0-9])*\.)+[a-zA-Z]{2,})$"
)
USERNAME_RE = re.compile(r"^[a-zA-Z0-9._-]{2,64}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

app = FastAPI(title="JPilot Installer", docs_url=None, redoc_url=None)


# --------------------------------------------------------------------------- models
class CertCheck(BaseModel):
    certificate: str
    private_key: str
    chain: str = ""


class InstallRequest(BaseModel):
    reconfigure: bool = False
    accepted_terms: bool = False
    deploy_mode: str = Field(default="prod")  # "prod" | "dev"
    admin_username: str = Field(default="admin")
    admin_password: str
    admin_email: str = ""
    domain: str = Field(default="localhost")
    app_name: str = Field(default="NSAgent")
    cert_mode: str = Field(default="self_signed")  # "self_signed" | "custom"
    certificate: str = ""
    private_key: str = ""
    chain: str = ""
    # optional SMTP
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_address: str = ""
    smtp_use_tls: bool = True
    smtp_use_ssl: bool = False


# ----------------------------------------------------------------------- helpers
def _inline_markdown(text: str) -> str:
    escaped = html.escape(text)
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(
        r"\[([^\]]+)\]\(([^)]+)\)",
        r'<a href="\2" target="_blank" rel="noopener noreferrer">\1</a>',
        escaped,
    )
    return escaped


def render_legal_markdown(text: str) -> str:
    blocks: list[str] = []
    in_list = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            if in_list:
                blocks.append("</ul>")
                in_list = False
            blocks.append(f"<h1>{_inline_markdown(stripped[2:])}</h1>")
        elif stripped.startswith("## "):
            if in_list:
                blocks.append("</ul>")
                in_list = False
            blocks.append(f"<h2>{_inline_markdown(stripped[3:])}</h2>")
        elif stripped.startswith("### "):
            if in_list:
                blocks.append("</ul>")
                in_list = False
            blocks.append(f"<h3>{_inline_markdown(stripped[4:])}</h3>")
        elif stripped == "":
            if in_list:
                blocks.append("</ul>")
                in_list = False
        elif stripped.startswith("- "):
            if not in_list:
                blocks.append("<ul>")
                in_list = True
            blocks.append(f"<li>{_inline_markdown(stripped[2:])}</li>")
        else:
            if in_list:
                blocks.append("</ul>")
                in_list = False
            blocks.append(f"<p>{_inline_markdown(line)}</p>")
    if in_list:
        blocks.append("</ul>")
    return "\n".join(blocks)


def _public_bytes(key) -> bytes:
    return key.public_bytes(
        serialization.Encoding.DER,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )


def inspect_cert(certificate: str, private_key: str):
    """Parse cert + key, confirm they match and the cert is not expired.

    Returns a dict describing the cert, or raises ValueError with a clear message.
    """
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
        san = [n.value for n in cert.extensions.get_extension_for_class(
            x509.SubjectAlternativeName).value]
    except x509.ExtensionNotFound:
        san = []

    return {
        "common_name": cn,
        "subject_alt_names": san,
        "expires": not_after.strftime("%Y-%m-%d"),
        "expires_in_days": (not_after - now).days,
    }


def generate_self_signed(domain: str) -> tuple[str, str]:
    """Return (cert_pem, key_pem) for a self-signed cert valid for `domain`."""
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    san_entries: list[x509.GeneralName] = []
    try:
        ip = ipaddress.ip_address(domain)
        san_entries.append(x509.IPAddress(ip))
    except ValueError:
        san_entries.append(x509.DNSName(domain))
        if domain == "localhost":
            san_entries.append(x509.IPAddress(ipaddress.ip_address("127.0.0.1")))

    now = dt.datetime.now(dt.timezone.utc)
    cert = (
        x509.CertificateBuilder()
        .subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, domain)]))
        .issuer_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, domain)]))
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - dt.timedelta(minutes=5))
        .not_valid_after(now + dt.timedelta(days=825))
        .add_extension(x509.SubjectAlternativeName(san_entries), critical=False)
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .sign(key, hashes.SHA256())
    )

    cert_pem = cert.public_bytes(serialization.Encoding.PEM).decode()
    key_pem = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.TraditionalOpenSSL,
        serialization.NoEncryption(),
    ).decode()
    return cert_pem, key_pem


def _env_value(value: str) -> str:
    """Escape a value for a docker-compose `.env` file.

    Compose interpolates `${...}` and `$VAR` in .env values, so a literal `$` must be
    doubled. Newlines are not allowed in a single .env entry.
    """
    return str(value).replace("\n", " ").replace("\r", "").replace("$", "$$")


def render_env(req: InstallRequest, encryption_key: str, jwt_secret: str) -> str:
    domain = req.domain.strip()
    base = f"https://{domain}"
    lines = [
        "# Generated by the NSAgent web installer. Keep the secrets below safe —",
        "# you need NSAGENT_ENCRYPTION_KEY to decrypt stored credentials after a restore.",
        "",
        f"NSAGENT_ENCRYPTION_KEY={_env_value(encryption_key)}",
        f"JWT_SECRET_KEY={_env_value(jwt_secret)}",
        f"ADMIN_USERNAME={_env_value(req.admin_username.strip() or 'admin')}",
        f"ADMIN_PASSWORD={_env_value(req.admin_password)}",
        f"ADMIN_EMAIL={_env_value(req.admin_email.strip())}",
        "",
        "# Deploy mode: prod = compiled stack (recommended); dev = hot reload for hacking",
        f"NSAGENT_DEPLOY_MODE={_env_value(req.deploy_mode.strip().lower() or 'prod')}",
        "",
        "# Public hostname (nginx TLS termination)",
        f"NGINX_HOSTNAME={_env_value(domain)}",
        "SSL_CERTS_PATH=./nginx/ssl",
        "",
        "# Frontend API base URL (must match nginx /api/ proxy prefix)",
        f"VITE_API_BASE_URL={_env_value(base)}/api",
        "",
        "# WebAuthn / passkeys (derived from the domain; passkeys are enrolled in-app)",
        f"WEBAUTHN_RP_ID={_env_value(domain)}",
        f"WEBAUTHN_RP_NAME={_env_value(req.app_name.strip() or 'NSAgent')}",
        f"WEBAUTHN_ORIGIN={_env_value(base)}",
        "",
        "# Comma-separated browser origins allowed for API CORS",
        f"CORS_ORIGINS={_env_value(base)}",
        "",
        "# SMTP for password reset emails (optional)",
        f"SMTP_HOST={_env_value(req.smtp_host)}",
        f"SMTP_PORT={req.smtp_port}",
        f"SMTP_USERNAME={_env_value(req.smtp_username)}",
        f"SMTP_PASSWORD={_env_value(req.smtp_password)}",
        f"SMTP_FROM_ADDRESS={_env_value(req.smtp_from_address)}",
        f"SMTP_USE_TLS={'true' if req.smtp_use_tls else 'false'}",
        f"SMTP_USE_SSL={'true' if req.smtp_use_ssl else 'false'}",
        "PASSWORD_RESET_LOG_CODES=false",
        "",
    ]
    return "\n".join(lines)


def _launch_domain() -> str | None:
    if not SENTINEL_PATH.is_file():
        return None
    line = SENTINEL_PATH.read_text(encoding="utf-8").strip().splitlines()[0].strip()
    return line or "localhost"


def _app_base_url(domain: str) -> str:
    cleaned = domain.strip() or "localhost"
    if cleaned in ("localhost", "127.0.0.1", "::1") or cleaned.startswith("127."):
        return "https://host.docker.internal"
    return f"https://{cleaned}"


def app_is_ready(domain: str) -> bool:
    cleaned = domain.strip() or "localhost"
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    paths = ("/api/health", "/")
    probes: list[tuple[str, str | None]] = [
        (f"https://host.docker.internal{path}", cleaned) for path in paths
    ]
    if cleaned not in ("localhost", "127.0.0.1", "::1") and not cleaned.startswith("127."):
        probes.extend((f"https://{cleaned}{path}", None) for path in paths)
    for url, host in probes:
        try:
            req = urllib.request.Request(url)
            if host:
                req.add_header("Host", host)
            with urllib.request.urlopen(req, context=ctx, timeout=5) as resp:
                if resp.status in (200, 301, 302, 304):
                    return True
        except (urllib.error.URLError, TimeoutError, OSError):
            continue
    return False


def _launch_message(elapsed: int, ready: bool) -> str:
    if ready:
        return "JPilot is ready! Opening your app…"
    if elapsed < 15:
        return "Building JPilot — please keep this tab open."
    if elapsed < 60:
        return "Starting services — first install can take a few minutes."
    if elapsed < 180:
        return "Almost there — hang tight, we're still starting JPilot."
    return "Still working… large installs can take up to 10 minutes."


# ----------------------------------------------------------------------- routes
@app.get("/api/status")
def status():
    return {"already_installed": ENV_PATH.exists()}


@app.get("/api/launch-status")
def launch_status():
    domain = _launch_domain()
    if domain is None:
        return {
            "ready": False,
            "phase": "waiting",
            "message": "Waiting for your configuration…",
            "app_url": None,
            "elapsed_seconds": 0,
        }
    app_url = f"https://{domain}"
    elapsed = 0
    if SENTINEL_PATH.is_file():
        elapsed = max(0, int(time.time() - SENTINEL_PATH.stat().st_mtime))
    ready = app_is_ready(domain)
    return {
        "ready": ready,
        "phase": "ready" if ready else "starting",
        "message": _launch_message(elapsed, ready),
        "app_url": app_url,
        "elapsed_seconds": elapsed,
    }


@app.post("/api/validate-cert")
def validate_cert(body: CertCheck):
    try:
        info = inspect_cert(body.certificate, body.private_key)
    except ValueError as exc:
        return JSONResponse(status_code=422, content={"ok": False, "error": str(exc)})
    return {"ok": True, **info}


@app.get("/legal/{slug}")
def legal_doc(slug: str):
    doc = LEGAL_DOCS.get(slug)
    if doc is None:
        raise HTTPException(status_code=404, detail="Legal document not found.")
    title, filename = doc
    path = LEGAL_DIR / filename
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Legal document file is missing.")
    body = render_legal_markdown(path.read_text(encoding="utf-8"))
    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{html.escape(title)} — JPilot Setup</title>
  <link rel="stylesheet" href="/static/styles.css" />
</head>
<body class="legal-page">
  <main class="legal-shell">
    <p class="legal-back"><a href="/">← Back to setup</a></p>
    <article class="legal-body">{body}</article>
  </main>
</body>
</html>"""
    return HTMLResponse(page)


@app.post("/api/install")
def install(req: InstallRequest):
    if not req.accepted_terms:
        raise HTTPException(
            status_code=422,
            detail="You must accept the Terms of Service, Privacy Policy, Acceptable Use Policy, and EULA.",
        )
    if ENV_PATH.exists() and not req.reconfigure:
        raise HTTPException(
            status_code=409,
            detail="An existing .env was found. Re-run with reconfigure to overwrite it.",
        )

    domain = req.domain.strip() or "localhost"
    if not DOMAIN_RE.match(domain):
        raise HTTPException(status_code=422, detail=f"'{domain}' is not a valid hostname or IP.")
    username = req.admin_username.strip() or "admin"
    if not USERNAME_RE.match(username):
        raise HTTPException(
            status_code=422,
            detail="Username must be 2–64 characters and use only letters, numbers, dots, underscores, or hyphens.",
        )
    email = req.admin_email.strip()
    if not email:
        raise HTTPException(status_code=422, detail="Admin email is required for password recovery.")
    if not EMAIL_RE.match(email):
        raise HTTPException(status_code=422, detail="Enter a valid email address.")
    if len(req.admin_password) < 8:
        raise HTTPException(status_code=422, detail="Admin password must be at least 8 characters.")
    if req.deploy_mode.strip().lower() not in ("prod", "dev"):
        raise HTTPException(status_code=422, detail="deploy_mode must be 'prod' or 'dev'.")

    # Resolve certificate material before writing anything.
    if req.cert_mode == "custom":
        try:
            inspect_cert(req.certificate, req.private_key)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        cert_pem = req.certificate.strip() + "\n"
        if req.chain.strip():
            cert_pem += req.chain.strip() + "\n"
        key_pem = req.private_key.strip() + "\n"
    else:
        cert_pem, key_pem = generate_self_signed(domain)

    encryption_key = Fernet.generate_key().decode()
    jwt_secret = secrets.token_urlsafe(48)

    # Write cert files.
    SSL_DIR.mkdir(parents=True, exist_ok=True)
    CERT_PATH.write_text(cert_pem)
    KEY_PATH.write_text(key_pem)
    os.chmod(KEY_PATH, 0o600)

    # Write .env.
    ENV_PATH.write_text(render_env(req, encryption_key, jwt_secret))

    # Signal the host orchestrator (install.sh) to launch the real stack.
    SENTINEL_PATH.write_text(domain + "\n")

    return {
        "ok": True,
        "domain": domain,
        "app_url": f"https://{domain}",
        "deploy_mode": req.deploy_mode.strip().lower() or "prod",
        "secrets": {
            "NSAGENT_ENCRYPTION_KEY": encryption_key,
            "JWT_SECRET_KEY": jwt_secret,
        },
        "cert_mode": req.cert_mode,
    }


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
