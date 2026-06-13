"""Detect service-health requests and run curated NITRO status reads without the LLM."""

from __future__ import annotations

import json
from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.schemas.copilot import ToolCallTrace
from app.services.copilot_form import is_form_submission

_DOWN_SIGNALS = (
    "down",
    "unhealthy",
    "out of service",
    "failed backend",
    "failed server",
)

_SERVICE_SIGNALS = (
    "service",
    "backend",
    "server",
    "member",
    "pool",
)


def detect_service_status_request(message: str) -> bool:
    if is_form_submission(message):
        return False
    lowered = (message or "").lower()
    if not lowered.strip():
        return False
    if any(term in lowered for term in ("route", "routing", "vlan", "network information", "network info")):
        if not any(term in lowered for term in _DOWN_SIGNALS):
            return False
    if "services that are down" in lowered or "service status" in lowered:
        return True
    if any(term in lowered for term in _DOWN_SIGNALS) and any(term in lowered for term in _SERVICE_SIGNALS):
        return True
    if "stat service" in lowered or "show service" in lowered:
        return True
    return False


def _parse_tool_result(result: str) -> dict[str, Any] | None:
    try:
        payload = json.loads(result)
    except (json.JSONDecodeError, TypeError):
        return None
    if isinstance(payload, dict) and isinstance(payload.get("data"), dict):
        return payload["data"]
    return payload if isinstance(payload, dict) else None


def format_service_status_response(appliance_name: str, data: dict[str, Any]) -> str:
    down_count = int(data.get("downCount") or 0)
    services = data.get("services") or []
    groups = data.get("serviceGroups") or []
    if down_count == 0:
        return f"**{appliance_name}** — no DOWN backend services or service-group members were found."
    header = f"**{appliance_name}** — {down_count} DOWN backend target(s)"
    lines = [header, ""]
    for service in services:
        bound = ", ".join(service.get("boundTo") or []) or "—"
        lines.append(
            f"- **{service.get('name', 'service')}** "
            f"({service.get('ipAddress', '—')}:{service.get('port', '—')}) "
            f"· {service.get('state', 'DOWN')} · bound to {bound}"
        )
    for group in groups:
        bound = ", ".join(group.get("boundTo") or []) or "—"
        lines.append(f"- **Service group {group.get('name', 'group')}** · bound to {bound}")
        for member in group.get("members") or []:
            lines.append(
                f"  - {member.get('name') or member.get('ipAddress', 'member')} "
                f"({member.get('ipAddress', '—')}:{member.get('port', '—')}) "
                f"· {member.get('state', 'DOWN')}"
            )
    return "\n".join(lines)


async def try_auto_service_status(
    db: AsyncIOMotorDatabase,
    *,
    user_message: str,
    appliance_name: str,
    enabled_tool_names: set[str],
) -> tuple[list[ToolCallTrace], str | None]:
    if not appliance_name:
        return [], None
    if not detect_service_status_request(user_message):
        return [], None
    if "netscaler_list_service_status" not in enabled_tool_names:
        return [], None

    from app.services.copilot_service import execute_copilot_tool

    arguments = {"appliance_name": appliance_name, "down_only": True}
    try:
        result = await execute_copilot_tool(
            db,
            "netscaler_list_service_status",
            arguments,
            default_appliance_name=appliance_name,
        )
    except Exception as exc:
        result = json.dumps({"success": False, "message": str(exc)}, indent=2)

    trace = ToolCallTrace(name="netscaler_list_service_status", arguments=arguments, result=result)
    data = _parse_tool_result(result) or {}
    if data.get("blocked"):
        return [trace], data.get("message") or "Service status tool was blocked."

    if data.get("services") is not None or data.get("serviceGroups") is not None:
        return [trace], format_service_status_response(appliance_name, data)

    context = (
        "\n\n[Auto-executed netscaler_list_service_status returned no data]\n"
        f"{result}\n"
        "If NITRO stats are unavailable, call search_netscaler_cli_reference for 'stat service' "
        "and retry with netscaler_run_cli_command. Do not answer from conversation memory.\n"
    )
    return [trace], context
