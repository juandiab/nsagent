"""JPilot chat roles: Architect, Operator, and Analyst."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel

from app.services.prompt_loader import load_operator_design_implementation_suffix, load_role_prompt
from app.services.vendor_registry import DEFAULT_VENDOR_ID, get_vendor_manifest


class JPilotRole(StrEnum):
    ARCHITECT = "architect"
    OPERATOR = "operator"
    ANALYST = "analyst"


DEFAULT_ROLE = JPilotRole.OPERATOR


class CopilotRoleInfo(BaseModel):
    id: str
    label: str
    description: str
    requiresAppliance: bool
    suggestedPaneLabel: str
    handoffTarget: str | None = None


ROLE_CATALOG: list[CopilotRoleInfo] = [
    CopilotRoleInfo(
        id=JPilotRole.ARCHITECT,
        label="Architect",
        description="Plan deployments, HA, migrations, and designs without a live appliance.",
        requiresAppliance=False,
        suggestedPaneLabel="Plan",
        handoffTarget=JPilotRole.OPERATOR,
    ),
    CopilotRoleInfo(
        id=JPilotRole.OPERATOR,
        label="Operator",
        description="Build and change configuration on a connected NetScaler.",
        requiresAppliance=True,
        suggestedPaneLabel="Operate",
        handoffTarget=None,
    ),
    CopilotRoleInfo(
        id=JPilotRole.ANALYST,
        label="Analyst",
        description="Troubleshoot incidents with read-first checks on a connected appliance.",
        requiresAppliance=True,
        suggestedPaneLabel="Analyze",
        handoffTarget=JPilotRole.OPERATOR,
    ),
]

# Tools that never touch a specific appliance (Architect + Analyst baseline).
_PLANNING_TOOLS = frozenset(
    {
        "search_netscaler_nextgen_api",
        "search_netscaler_cli_reference",
        "search_jpilot_architect_resources",
        "jpilot_check_doc_connectivity",
        "netscaler_list_inventory",
    }
)

# Analyst: planning tools plus read/diagnostic MCP tools (no provisioning writes).
_ANALYST_TOOLS = _PLANNING_TOOLS | frozenset(
    {
        "netscaler_test_connection",
        "netscaler_get_system_info",
        "netscaler_list_applications",
        "netscaler_list_virtual_servers",
        "netscaler_list_virtual_ips",
        "netscaler_list_ip_addresses",
        "netscaler_nextgen_get",
        "netscaler_run_diagnostic",
        "netscaler_telnet",
        "netscaler_collect_nsconmsg",
        "netscaler_ssh_run_command",
        "netscaler_run_cli_command",
    }
)

_ANALYST_BLOCKED = frozenset(
    {
        "netscaler_create_application",
        "netscaler_add_ip_address",
        "netscaler_nextgen_request",
        "netscaler_run_cli_commands",
    }
)


def operator_design_implementation_suffix(appliance_name: str, vendor: str | None = None) -> str:
    return load_operator_design_implementation_suffix(appliance_name, vendor)


def normalize_role(role: str | None) -> JPilotRole:
    if not role:
        return DEFAULT_ROLE
    normalized = role.strip().lower()
    if normalized == "investigator":
        normalized = JPilotRole.ANALYST.value
    try:
        return JPilotRole(normalized)
    except ValueError:
        return DEFAULT_ROLE


def role_requires_appliance(role: JPilotRole | str | None) -> bool:
    parsed = role if isinstance(role, JPilotRole) else normalize_role(role if isinstance(role, str) else None)
    return parsed != JPilotRole.ARCHITECT


def get_role_catalog() -> list[dict[str, Any]]:
    return [item.model_dump() for item in ROLE_CATALOG]


def build_system_prompt(
    role: JPilotRole | str | None,
    appliance_name: str = "",
    vendor: str | None = DEFAULT_VENDOR_ID,
) -> str:
    parsed = role if isinstance(role, JPilotRole) else normalize_role(role if isinstance(role, str) else None)
    if parsed == JPilotRole.ARCHITECT:
        base = load_role_prompt(JPilotRole.ARCHITECT.value, vendor)
        if appliance_name:
            return (
                f"{base}\n"
                f"Reference appliance (planning context only, do not run appliance tools): {appliance_name}\n"
            )
        return (
            f"{base}\n"
            "No appliance is connected. Use inventory and documentation only.\n"
        )
    if parsed == JPilotRole.ANALYST:
        base = load_role_prompt(JPilotRole.ANALYST.value, vendor)
        suffix = (
            f"Active appliance: {appliance_name}\n"
            f"Next-Gen API login is confirmed. Always pass appliance_name \"{appliance_name}\" to NetScaler tools.\n"
        )
        return f"{base}\n{suffix}"

    base = load_role_prompt(JPilotRole.OPERATOR.value, vendor)
    return (
        f"{base}\n"
        f"Active appliance: {appliance_name}\n"
        f"Next-Gen API login is confirmed. Always pass appliance_name \"{appliance_name}\" to NetScaler tools.\n"
        "Official CLI/API behavioral rules are loaded on demand — do not assume syntax without searching first."
    )


def filter_tools_for_role(
    tools: list[dict[str, Any]],
    role: JPilotRole | str | None,
    vendor: str | None = None,
) -> list[dict[str, Any]]:
    parsed = role if isinstance(role, JPilotRole) else normalize_role(role if isinstance(role, str) else None)
    chat_vendor = (vendor or DEFAULT_VENDOR_ID).strip().lower()
    manifest = get_vendor_manifest(chat_vendor)

    if parsed == JPilotRole.OPERATOR:
        return tools

    if parsed == JPilotRole.ARCHITECT:
        allowed = manifest.planning_tool_names if manifest else _PLANNING_TOOLS
        return [tool for tool in tools if tool.get("name") in allowed]

    allowed = manifest.analyst_tool_names if manifest else _ANALYST_TOOLS
    return [tool for tool in tools if tool.get("name") in allowed]


def assert_tool_allowed_for_role(
    name: str,
    role: JPilotRole | str | None,
    vendor: str | None = None,
) -> None:
    parsed = role if isinstance(role, JPilotRole) else normalize_role(role if isinstance(role, str) else None)
    if parsed == JPilotRole.OPERATOR:
        return
    chat_vendor = (vendor or DEFAULT_VENDOR_ID).strip().lower()
    manifest = get_vendor_manifest(chat_vendor)
    if parsed == JPilotRole.ARCHITECT:
        allowed = manifest.planning_tool_names if manifest else _PLANNING_TOOLS
    else:
        allowed = manifest.analyst_tool_names if manifest else _ANALYST_TOOLS
    if name not in allowed:
        raise ValueError(
            f"Tool '{name}' is not available in {parsed.value} role for vendor '{chat_vendor}'. "
            f"Switch to Operator to make configuration changes."
        )
    if parsed == JPilotRole.ANALYST and manifest and name in manifest.analyst_blocked:
        raise ValueError(
            f"Tool '{name}' is not allowed for Analyst (read/diagnostic only). "
            "Use Operator role to apply changes."
        )
    if parsed == JPilotRole.ANALYST and not manifest and name in _ANALYST_BLOCKED:
        raise ValueError(
            f"Tool '{name}' is not allowed for Analyst (read/diagnostic only). "
            "Use Operator role to apply changes."
        )
