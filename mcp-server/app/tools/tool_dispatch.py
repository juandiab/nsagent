"""Unified MCP tool listing and dispatch across vendors."""

from __future__ import annotations

import mcp.types as types

from app.tools.cisco_tools import CISCO_TOOLS, call_cisco_tool, get_enabled_cisco_tools
from app.tools.netscaler_tools import NETSCALER_TOOLS, call_netscaler_tool, get_enabled_tools as get_enabled_netscaler_tools


def get_all_tools() -> list[types.Tool]:
    return [*NETSCALER_TOOLS, *CISCO_TOOLS]


def get_enabled_tools() -> list[types.Tool]:
    return [*get_enabled_netscaler_tools(), *get_enabled_cisco_tools()]


async def call_mcp_tool(name: str, arguments: dict) -> list[types.TextContent]:
    if name.startswith("cisco_"):
        return await call_cisco_tool(name, arguments)
    return await call_netscaler_tool(name, arguments)
