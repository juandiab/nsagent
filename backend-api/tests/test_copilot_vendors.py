"""Tests for vendor-scoped copilot tools."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.copilot_vendors import filter_tools_by_vendor  # noqa: E402
from app.services.vendor_registry import allowed_tool_names_for_vendor  # noqa: E402


def test_cisco_vendor_gets_cisco_tools():
    allowed = allowed_tool_names_for_vendor("cisco")
    assert "cisco_run_cli_commands" in allowed
    assert "netscaler_run_cli_commands" not in allowed


def test_filter_tools_by_vendor_cisco():
    tools = [
        {"name": "netscaler_list_inventory"},
        {"name": "cisco_ssh_run_command"},
        {"name": "netscaler_run_cli_commands"},
    ]
    filtered = filter_tools_by_vendor(tools, "cisco")
    names = {t["name"] for t in filtered}
    assert names == {"netscaler_list_inventory", "cisco_ssh_run_command"}


def test_f5_vendor_gets_f5_tools():
    allowed = allowed_tool_names_for_vendor("f5")
    assert "f5_run_tmsh_commands" in allowed
    assert "search_f5_documentation" in allowed
    assert "cisco_run_cli_commands" not in allowed


def test_filter_tools_by_vendor_f5():
    tools = [
        {"name": "netscaler_list_inventory"},
        {"name": "f5_ssh_run_command"},
        {"name": "cisco_ssh_run_command"},
    ]
    filtered = filter_tools_by_vendor(tools, "f5")
    names = {t["name"] for t in filtered}
    assert names == {"netscaler_list_inventory", "f5_ssh_run_command"}
