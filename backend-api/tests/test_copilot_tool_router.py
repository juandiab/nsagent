"""Tests for intent-based copilot tool routing."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.copilot_tool_router import (  # noqa: E402
    classify_tool_packs,
    pack_tool_names,
    route_copilot_tools,
)


def _tools(*names: str) -> list[dict]:
    return [{"name": name, "description": name, "parameters": {"type": "object", "properties": {}}} for name in names]


ALL_OPERATOR = _tools(
    "netscaler_get_system_info",
    "netscaler_list_virtual_servers",
    "netscaler_run_diagnostic",
    "netscaler_telnet",
    "netscaler_run_cli_command",
    "netscaler_run_cli_commands",
    "search_netscaler_cli_reference",
    "search_netscaler_nextgen_api",
    "netscaler_create_application",
    "jpilot_check_doc_connectivity",
)


def test_ping_routes_diagnostic_not_cli_write():
    packs = classify_tool_packs("Can the appliance ping 10.0.0.1?", role="operator")
    names = pack_tool_names(packs)
    assert "netscaler_run_diagnostic" in names
    assert "netscaler_run_cli_commands" not in names

    routed = route_copilot_tools(ALL_OPERATOR, role="operator", user_message="ping 10.0.0.1")
    routed_names = {t["name"] for t in routed}
    assert "netscaler_run_diagnostic" in routed_names
    assert "netscaler_run_cli_commands" not in routed_names


def test_add_lb_routes_cli_write_pack():
    routed = route_copilot_tools(
        ALL_OPERATOR,
        role="operator",
        user_message="add lb vserver web_example HTTP 10.0.0.50 80",
    )
    routed_names = {t["name"] for t in routed}
    assert "search_netscaler_cli_reference" in routed_names
    assert "netscaler_run_cli_commands" in routed_names
    assert "netscaler_create_application" not in routed_names


def test_show_vserver_routes_read_only():
    routed = route_copilot_tools(
        ALL_OPERATOR,
        role="operator",
        user_message="show lb vserver",
    )
    routed_names = {t["name"] for t in routed}
    assert "netscaler_list_virtual_servers" in routed_names or "netscaler_run_cli_command" in routed_names
    assert "netscaler_run_cli_commands" not in routed_names


def test_ambiguous_short_message_uses_full_tool_set():
    routed = route_copilot_tools(ALL_OPERATOR, role="operator", user_message="ok")
    assert len(routed) == len(ALL_OPERATOR)


def test_architect_design_adds_architect_search():
    tools = _tools(
        "netscaler_list_inventory",
        "search_netscaler_cli_reference",
        "search_netscaler_nextgen_api",
        "search_jpilot_architect_resources",
        "jpilot_check_doc_connectivity",
    )
    routed = route_copilot_tools(
        tools,
        role="architect",
        user_message="Help me plan a dual-site GSLB design with Gateway",
    )
    routed_names = {t["name"] for t in routed}
    assert "search_jpilot_architect_resources" in routed_names
