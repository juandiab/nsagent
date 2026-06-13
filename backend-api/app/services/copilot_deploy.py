"""Auto-deploy Next-Gen applications from configuration form submissions."""

from __future__ import annotations

import json
import re
from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.schemas.copilot import ToolCallTrace
from app.services.copilot_form import is_form_submission

_IP_RE = re.compile(r"^\d{1,3}(?:\.\d{1,3}){3}$")

_FORM_FIELD_ALIASES: dict[str, tuple[str, ...]] = {
    "name": (
        "application name",
        "app name",
    ),
    "virtual_ip": (
        "vip address",
        "virtual ip",
        "vip",
    ),
    "port": (
        "vip port",
        "front-end port",
        "frontend port",
        "front end port",
    ),
    "servers_port": (
        "backend server port",
        "backend port",
        "servers port",
        "server port",
    ),
    "protocol": (
        "protocol",
        "service type",
    ),
    "servers": (
        "backend storefront server",
        "backend server ip",
        "backend ip addresses",
        "backend ip",
        "backend iis",
        "backend server",
        "backend",
        "server ip",
    ),
}

_FIELD_PARSE_ORDER = (
    "name",
    "virtual_ip",
    "servers",
    "servers_port",
    "port",
    "protocol",
)

_CLASSIC_LB_LABELS = (
    "virtual server name",
    "vserver name",
    "lb vserver",
)


def _normalize_label(label: str) -> str:
    return " ".join(label.strip().lower().split())


def _label_matches(key: str, normalized_label: str) -> bool:
    aliases = _FORM_FIELD_ALIASES.get(key, ())
    return any(alias in normalized_label or normalized_label == alias for alias in aliases)


def parse_configuration_form_fields(user_message: str) -> dict[str, str]:
    """Parse `- Label: value` lines from a Configuration inputs submission."""
    if not is_form_submission(user_message):
        return {}

    fields: dict[str, str] = {}
    for line in user_message.splitlines():
        stripped = line.strip()
        if not stripped.startswith("- "):
            continue
        body = stripped[2:].strip()
        if ": " not in body:
            continue
        label, _, value = body.partition(": ")
        value = value.strip()
        if not value or value == "(not provided)":
            continue
        normalized_label = _normalize_label(label)
        if any(marker in normalized_label for marker in _CLASSIC_LB_LABELS):
            return {}
        matched = False
        for key in _FIELD_PARSE_ORDER:
            if _label_matches(key, normalized_label):
                fields[key] = value
                matched = True
                break
        if not matched and normalized_label.endswith(" name") and "name" not in fields:
            fields["name"] = value
    return fields


def parse_backend_servers(raw: str) -> list[str]:
    servers: list[str] = []
    for part in re.split(r"[,;\n]+", raw or ""):
        candidate = part.strip()
        if not candidate:
            continue
        token = candidate.split()[0].strip()
        if _IP_RE.match(token):
            servers.append(token)
    return servers


def detect_nextgen_application_form_submission(user_message: str) -> bool:
    fields = parse_configuration_form_fields(user_message)
    if not fields.get("name") or not fields.get("virtual_ip"):
        return False
    return bool(parse_backend_servers(fields.get("servers", "")))


def _parse_tool_result(result: str) -> dict[str, Any] | None:
    try:
        payload = json.loads(result)
    except (json.JSONDecodeError, TypeError):
        return None
    if isinstance(payload, dict) and isinstance(payload.get("data"), dict):
        return payload["data"]
    return payload if isinstance(payload, dict) else None


def format_create_application_response(appliance_name: str, data: dict[str, Any]) -> str:
    app = data.get("application") or {}
    name = str(app.get("name") or "").strip()
    vip = str(app.get("virtual_ip") or "").strip()
    port = app.get("port", 80)
    protocol = str(app.get("protocol") or "HTTP").strip()
    servers = app.get("servers") or []
    server_text = ", ".join(f"`{server}:{port}`" for server in servers) if servers else "none"
    lines = [
        f"**{appliance_name}** — application `{name}` created via Next-Gen API.",
        "",
        f"- VIP: `{vip}:{port}` ({protocol})",
        f"- Backends: {server_text}",
        "",
        "Verify health with `netscaler_list_service_status` if backends stay UNKNOWN or the vserver is DOWN.",
    ]
    return "\n".join(lines)


async def try_auto_create_application(
    db: AsyncIOMotorDatabase,
    *,
    user_message: str,
    appliance_name: str,
    enabled_tool_names: set[str],
) -> tuple[list[ToolCallTrace], str | None]:
    """POST /applications when the user submits a Next-Gen configuration form."""
    if not appliance_name:
        return [], None
    if not detect_nextgen_application_form_submission(user_message):
        return [], None
    if "netscaler_create_application" not in enabled_tool_names:
        return [], (
            "**Configuration form received** — `netscaler_create_application` is not enabled. "
            "Enable it in MCP settings and retry."
        )

    fields = parse_configuration_form_fields(user_message)
    servers = parse_backend_servers(fields.get("servers", ""))
    port_raw = fields.get("port", "80")
    try:
        port = int(str(port_raw).strip())
    except ValueError:
        port = 80
    servers_port = None
    if fields.get("servers_port"):
        try:
            servers_port = int(str(fields["servers_port"]).strip())
        except ValueError:
            servers_port = None

    from app.services.copilot_service import execute_copilot_tool

    arguments: dict[str, Any] = {
        "appliance_name": appliance_name,
        "name": fields["name"].strip(),
        "virtual_ip": fields["virtual_ip"].strip(),
        "port": port,
        "protocol": (fields.get("protocol") or "HTTP").strip().upper(),
        "servers": servers,
    }
    if servers_port is not None:
        arguments["servers_port"] = servers_port
    try:
        result = await execute_copilot_tool(
            db,
            "netscaler_create_application",
            arguments,
            default_appliance_name=appliance_name,
        )
    except Exception as exc:
        result = json.dumps({"success": False, "message": str(exc)}, indent=2)

    trace = ToolCallTrace(name="netscaler_create_application", arguments=arguments, result=result)
    data = _parse_tool_result(result) or {}
    if data.get("blocked"):
        return [trace], data.get("message") or "Application create was blocked."

    if data.get("success") is False:
        message = str(data.get("message") or data.get("error") or "Application create failed.")
        return [trace], f"**Application create failed** — {message}"

    if data.get("success") is True or data.get("application"):
        return [trace], format_create_application_response(appliance_name, data)

    return [trace], None
