"""Detect inventory read requests and run curated tools without relying on the LLM."""

from __future__ import annotations

import json
from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.schemas.copilot import ToolCallTrace
from app.services.copilot_form import is_form_submission

_WRITE_SIGNALS = (
    "add ",
    "create ",
    "new ",
    "configure ",
    "set ",
    "bind ",
    "remove ",
    "delete ",
    "implement ",
)


def user_asks_for_all_ips(user_message: str) -> bool:
    lowered = (user_message or "").lower()
    if any(term in lowered for term in ("all ip", "list ip", "every ip", "show ns ip", "show ip", "ns ip")):
        return True
    if "ip" in lowered and any(term in lowered for term in ("all", "list", "every", "each")):
        return True
    return any(term in lowered for term in ("nsip", "snip"))


def user_asks_for_management_ip_only(user_message: str) -> bool:
    lowered = (user_message or "").lower()
    if user_asks_for_all_ips(user_message):
        return False
    if "vip" in lowered or "virtual server" in lowered or "virtual ip" in lowered:
        return False
    return any(term in lowered for term in ("management ip", "mgmt ip", "management address"))


_BROADER_NETWORK_TERMS = (
    "route",
    "routing",
    "vlan",
    "interface",
    "gateway",
    "network information",
    "network info",
    "network config",
    "topology",
)


def detect_ip_inventory_request(message: str) -> bool:
    """High-confidence read-only request for the full appliance IP inventory."""
    if is_form_submission(message):
        return False
    lowered = (message or "").lower()
    if not lowered.strip():
        return False
    if any(signal in lowered for signal in _WRITE_SIGNALS):
        return False
    if any(term in lowered for term in _BROADER_NETWORK_TERMS):
        return False
    if user_asks_for_management_ip_only(message):
        return False
    if any(
        term in lowered
        for term in (
            "all ip",
            "list ip",
            "every ip",
            "show ns ip",
            "ip addresses",
            "ip address",
        )
    ):
        return True
    if "ip" in lowered and any(term in lowered for term in ("all", "list", "every", "each")):
        return True
    type_terms = sum(1 for term in ("nsip", "snip", "vip") if term in lowered)
    return type_terms >= 2


def _parse_tool_result(result: str) -> dict[str, Any] | None:
    try:
        payload = json.loads(result)
    except (json.JSONDecodeError, TypeError):
        return None
    if isinstance(payload, dict) and isinstance(payload.get("data"), dict):
        return payload["data"]
    return payload if isinstance(payload, dict) else None


def format_ip_inventory_response(appliance_name: str, data: dict[str, Any]) -> str:
    addresses = data.get("addresses") or []
    count = int(data.get("ipCount") or len(addresses))
    management_ip = str(data.get("managementIp") or "").strip()
    header = f"**{appliance_name}** — {count} IP address(es)"
    if management_ip:
        header += f" · management `{management_ip}`"
    return header


async def try_auto_ip_inventory(
    db: AsyncIOMotorDatabase,
    *,
    user_message: str,
    appliance_name: str,
    enabled_tool_names: set[str],
) -> tuple[list[ToolCallTrace], str | None]:
    """Run netscaler_list_ip_addresses when the user asks for the full IP inventory."""
    if not appliance_name:
        return [], None
    if not detect_ip_inventory_request(user_message):
        return [], None
    if "netscaler_list_ip_addresses" not in enabled_tool_names:
        return [], None

    from app.services.copilot_service import execute_copilot_tool

    arguments = {"appliance_name": appliance_name}
    try:
        result = await execute_copilot_tool(
            db,
            "netscaler_list_ip_addresses",
            arguments,
            default_appliance_name=appliance_name,
        )
    except Exception as exc:
        result = json.dumps({"success": False, "message": str(exc)}, indent=2)

    trace = ToolCallTrace(name="netscaler_list_ip_addresses", arguments=arguments, result=result)
    data = _parse_tool_result(result) or {}
    if data.get("blocked"):
        return [trace], data.get("message") or "IP inventory tool was blocked."

    addresses = data.get("addresses") or []
    if addresses:
        return [trace], format_ip_inventory_response(appliance_name, data)

    context = (
        "\n\n[Auto-executed netscaler_list_ip_addresses returned no addresses]\n"
        f"{result}\n"
        "Follow SSH fallback if needed: search_netscaler_cli_reference for 'show ns ip', "
        "then netscaler_ssh_run_command. Answer only what the user asked.\n"
    )
    return [trace], context
