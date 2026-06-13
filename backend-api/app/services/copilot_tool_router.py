"""Intent-based tool selection to reduce tokens sent to the LLM on each request."""

from __future__ import annotations

from typing import Any

from app.services.copilot_architect_discovery import user_wants_deliverable_now
from app.services.copilot_form import is_form_submission, user_requests_design_implementation
from app.services.copilot_inventory import detect_ip_inventory_request
from app.services.copilot_service_status import detect_service_status_request

# Pack names map to tool names included when that intent is detected.
PACK_TOOLS: dict[str, frozenset[str]] = {
    "core_read": frozenset(
        {
            "netscaler_get_system_info",
            "netscaler_test_connection",
        }
    ),
    "inventory": frozenset({"netscaler_list_inventory"}),
    "read": frozenset(
        {
            "netscaler_list_applications",
            "netscaler_list_virtual_servers",
            "netscaler_list_virtual_ips",
            "netscaler_list_ip_addresses",
            "netscaler_list_service_status",
            "netscaler_nextgen_get",
            "netscaler_run_cli_command",
        }
    ),
    "ip_inventory": frozenset({"netscaler_list_ip_addresses"}),
    "service_status": frozenset({"netscaler_list_service_status"}),
    "diagnostic": frozenset(
        {
            "netscaler_run_diagnostic",
            "netscaler_telnet",
            "netscaler_collect_nsconmsg",
        }
    ),
    "cli_write": frozenset(
        {
            "netscaler_run_cli_commands",
            "netscaler_add_ip_address",
            "netscaler_ssh_run_command",
        }
    ),
    "nextgen_write": frozenset(
        {
            "netscaler_create_application",
            "netscaler_nextgen_request",
        }
    ),
    "cli_search": frozenset({"search_netscaler_cli_reference"}),
    "nextgen_search": frozenset({"search_netscaler_nextgen_api"}),
    "doc_connectivity": frozenset({"jpilot_check_doc_connectivity"}),
    "architect_search": frozenset({"search_jpilot_architect_resources"}),
}

ROLE_BASE_PACKS: dict[str, frozenset[str]] = {
    "architect": frozenset({"inventory"}),
    "analyst": frozenset({"core_read", "read", "diagnostic", "cli_search", "nextgen_search"}),
    "operator": frozenset({"core_read", "read"}),
}

CISCO_PACK_TOOLS: dict[str, frozenset[str]] = {
    "core_read": frozenset({"cisco_test_connection"}),
    "read": frozenset({"cisco_ssh_run_command"}),
    "cli_write": frozenset({"cisco_run_cli_command", "cisco_run_cli_commands"}),
    "cli_search": frozenset({"search_cisco_cli_reference"}),
    "doc_connectivity": frozenset({"jpilot_check_doc_connectivity"}),
    "inventory": frozenset({"netscaler_list_inventory"}),
}

CISCO_ROLE_BASE_PACKS: dict[str, frozenset[str]] = {
    "analyst": frozenset({"core_read", "read", "cli_search"}),
    "operator": frozenset({"core_read", "read", "cli_search"}),
}

SDX_PACK_TOOLS: dict[str, frozenset[str]] = {
    "core_read": frozenset({"sdx_test_connection"}),
    "read": frozenset({"sdx_ssh_run_command"}),
    "cli_write": frozenset({"sdx_run_cli_command", "sdx_run_cli_commands"}),
    "cli_search": frozenset({"search_sdx_cli_reference"}),
    "doc_connectivity": frozenset({"jpilot_check_doc_connectivity"}),
    "inventory": frozenset({"netscaler_list_inventory"}),
}

SDX_ROLE_BASE_PACKS: dict[str, frozenset[str]] = {
    "analyst": frozenset({"core_read", "read", "cli_search"}),
    "operator": frozenset({"core_read", "read", "cli_search"}),
}

F5_PACK_TOOLS: dict[str, frozenset[str]] = {
    "core_read": frozenset({"f5_test_connection"}),
    "read": frozenset({"f5_ssh_run_command"}),
    "cli_write": frozenset({"f5_run_tmsh_command", "f5_run_tmsh_commands"}),
    "cli_search": frozenset({"search_f5_tmsh_reference"}),
    "architect_search": frozenset({"search_f5_documentation"}),
    "doc_connectivity": frozenset({"jpilot_check_doc_connectivity"}),
    "inventory": frozenset({"netscaler_list_inventory"}),
}

F5_ROLE_BASE_PACKS: dict[str, frozenset[str]] = {
    "architect": frozenset({"architect_search", "doc_connectivity", "inventory"}),
    "analyst": frozenset({"core_read", "read", "cli_search"}),
    "operator": frozenset({"core_read", "read", "cli_search"}),
}

MIN_ROUTED_TOOLS = 3


def _contains_any(text: str, phrases: tuple[str, ...]) -> bool:
    return any(phrase in text for phrase in phrases)


def classify_tool_packs(
    user_message: str,
    *,
    role: str,
    attachment_names: list[str] | None = None,
    vendor: str = "netscaler",
) -> set[str]:
    lowered = (user_message or "").lower()
    attachments = attachment_names or []
    if vendor == "cisco":
        packs: set[str] = set(CISCO_ROLE_BASE_PACKS.get(role, CISCO_ROLE_BASE_PACKS["operator"]))
    elif vendor == "f5":
        packs = set(F5_ROLE_BASE_PACKS.get(role, F5_ROLE_BASE_PACKS["operator"]))
    elif vendor == "sdx":
        packs = set(SDX_ROLE_BASE_PACKS.get(role, SDX_ROLE_BASE_PACKS["operator"]))
    else:
        packs = set(ROLE_BASE_PACKS.get(role, ROLE_BASE_PACKS["operator"]))

    if vendor == "netscaler" and role != "architect" and detect_service_status_request(user_message):
        return packs | {"service_status"}
    if vendor == "netscaler" and role != "architect" and detect_ip_inventory_request(user_message):
        return packs | {"ip_inventory"}

    if role == "architect" and vendor == "netscaler":
        architect_packs: set[str] = set()
        if user_wants_deliverable_now(user_message):
            architect_packs.update({"architect_search", "cli_search", "nextgen_search"})
        return architect_packs

    if _contains_any(
        lowered,
        (
            "can you reach",
            "can jpilot reach",
            "doc connectivity",
            "documentation site",
            "reach the documentation",
        ),
    ):
        packs.add("doc_connectivity")

    if _contains_any(
        lowered,
        (
            "internet access",
            "internet connectivity",
            "reach the internet",
            "outbound internet",
            "has internet",
            "access the internet",
            "connect to the internet",
            "external connectivity",
        ),
    ):
        if _contains_any(
            lowered,
            (
                "netscaler",
                "adc",
                "appliance",
                "nsip",
                "the box",
                "this box",
                "vpx",
            ),
        ) or not _contains_any(
            lowered,
            (
                "can you reach",
                "can jpilot",
                "jpilot reach",
                "your server",
                "the backend",
                "documentation site",
            ),
        ):
            packs.add("diagnostic")
        else:
            packs.add("doc_connectivity")

    if _contains_any(
        lowered,
        (
            "ping",
            "traceroute",
            "telnet",
            "reachable",
            "tcp port",
            "port check",
            "nsconmsg",
            "cpu",
            "memory util",
            "performance counter",
            "diag",
        ),
    ):
        packs.add("diagnostic")

    if _contains_any(
        lowered,
        (
            "show ",
            "list ",
            "get ",
            "stat ",
            "how many",
            "what is the",
            "inventory",
            "version",
            "firmware",
            "hostname",
            "serial",
        ),
    ):
        packs.add("read")

    if _contains_any(
        lowered,
        (
            "nsip",
            "snip",
            "all ip",
            "list ip",
            "every ip",
            "ip address",
            "ip addresses",
            "show ns ip",
        ),
    ):
        packs.add("read")

    if role == "architect" and user_wants_deliverable_now(user_message):
        packs.update({"architect_search", "cli_search", "nextgen_search"})

    if is_form_submission(user_message):
        if role == "architect":
            packs.discard("architect_search")
            packs.discard("cli_search")
            packs.discard("nextgen_search")
            packs.discard("cli_write")
            packs.discard("nextgen_write")
            packs.discard("read")
            packs.discard("inventory")
        else:
            packs.update({"cli_write", "cli_search", "nextgen_write", "nextgen_search", "read"})

    if role == "architect":
        return packs

    cli_write_signal = _contains_any(
        lowered,
        (
            "add ",
            "set ",
            "bind ",
            "unbind",
            "rm ",
            "remove ",
            "delete ",
            "create lb",
            "create a lb",
            "new lb",
            "new vip",
            "save ns config",
            "configure",
            "implement",
            "route",
            "static route",
            "routing",
            "vlan",
            "interface",
            "provision",
            "run cli",
            "cli command",
        ),
    )
    nextgen_write_signal = _contains_any(
        lowered,
        (
            "application",
            "next-gen",
            "nextgen",
            "config-set",
            "config set",
            "/applications",
            "post application",
        ),
    )

    if user_requests_design_implementation(user_message, attachments):
        packs.update({"cli_write", "cli_search", "read", "core_read"})

    if cli_write_signal:
        packs.update({"cli_write", "cli_search", "read"})

    if nextgen_write_signal:
        packs.update({"nextgen_write", "nextgen_search", "read"})

    if role in {"operator", "analyst"} and not packs.intersection(
        {"diagnostic", "cli_write", "nextgen_write", "read", "doc_connectivity"}
    ):
        packs.add("read")

    return packs


def pack_tool_names(packs: set[str], vendor: str = "netscaler") -> set[str]:
    names: set[str] = set()
    if vendor == "cisco":
        source = CISCO_PACK_TOOLS
    elif vendor == "f5":
        source = F5_PACK_TOOLS
    elif vendor == "sdx":
        source = SDX_PACK_TOOLS
    else:
        source = PACK_TOOLS
    for pack in packs:
        names.update(source.get(pack, frozenset()))
    return names


def should_use_full_tool_set(user_message: str, role: str) -> bool:
    """Fallback to all role-enabled tools when routing would be unreliable."""
    text = (user_message or "").strip()
    if len(text) < 3:
        return True
    if role == "architect":
        return False
    lowered = text.lower()
    if _contains_any(lowered, ("and also", "then ", "after that", "multi-step", "step 1")):
        return True
    if lowered.count(",") >= 3:
        return True
    return False


def route_copilot_tools(
    enabled_tools: list[dict[str, Any]],
    *,
    role: str,
    user_message: str,
    attachment_names: list[str] | None = None,
    vendor: str = "netscaler",
) -> list[dict[str, Any]]:
    """Return a subset of enabled_tools matching detected intents."""
    if not enabled_tools:
        return enabled_tools

    if vendor in {"cisco", "sdx", "f5"}:
        return enabled_tools

    if vendor != "netscaler":
        return enabled_tools

    if should_use_full_tool_set(user_message, role):
        return enabled_tools

    packs = classify_tool_packs(
        user_message, role=role, attachment_names=attachment_names, vendor=vendor
    )
    allowed_names = pack_tool_names(packs, vendor=vendor)
    enabled_names = {tool["name"] for tool in enabled_tools}
    selected_names = allowed_names & enabled_names

    if role == "architect":
        return [tool for tool in enabled_tools if tool["name"] in selected_names]

    if "ip_inventory" in packs:
        selected = [tool for tool in enabled_tools if tool["name"] in selected_names]
        return selected or enabled_tools

    if "service_status" in packs:
        selected = [tool for tool in enabled_tools if tool["name"] in selected_names]
        return selected or enabled_tools

    if len(selected_names) < MIN_ROUTED_TOOLS:
        return enabled_tools

    selected = [tool for tool in enabled_tools if tool["name"] in selected_names]
    return selected or enabled_tools
