import mcp.types as types

from app.services.f5_ssh_service import (
    run_tmsh_command,
    run_tmsh_commands,
    ssh_run_command,
    test_connection,
)
from app.services.netscaler_service import format_tool_result

F5_TOOLS = [
    types.Tool(
        name="f5_test_connection",
        description="Test SSH connectivity to an F5 BIG-IP using tmsh show sys version.",
        inputSchema={
            "type": "object",
            "properties": {
                "host": {"type": "string", "description": "BIG-IP management IP or hostname"},
                "username": {"type": "string", "description": "SSH username"},
                "password": {"type": "string", "description": "SSH password"},
            },
            "required": ["host", "username", "password"],
        },
    ),
    types.Tool(
        name="f5_ssh_run_command",
        description=(
            "Run a read-only F5 TMSH command over SSH (tmsh show/list, ping, traceroute). "
            "Use after search_f5_tmsh_reference when syntax is uncertain."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "host": {"type": "string"},
                "username": {"type": "string"},
                "password": {"type": "string"},
                "command": {"type": "string", "description": "Read-only TMSH command"},
                "purpose": {"type": "string", "description": "Why this command is needed"},
            },
            "required": ["host", "username", "password", "command", "purpose"],
        },
    ),
    types.Tool(
        name="f5_run_tmsh_command",
        description=(
            "Run a single F5 TMSH configuration command over SSH (pools, virtual servers, profiles). "
            "Use ONLY after search_f5_tmsh_reference confirms syntax."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "host": {"type": "string"},
                "username": {"type": "string"},
                "password": {"type": "string"},
                "command": {"type": "string"},
                "purpose": {"type": "string"},
            },
            "required": ["host", "username", "password", "command", "purpose"],
        },
    ),
    types.Tool(
        name="f5_run_tmsh_commands",
        description=(
            "Run ordered F5 TMSH commands over SSH. "
            "Use ONLY after search_f5_tmsh_reference confirms syntax."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "host": {"type": "string"},
                "username": {"type": "string"},
                "password": {"type": "string"},
                "commands": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Ordered TMSH commands",
                },
                "purpose": {"type": "string"},
            },
            "required": ["host", "username", "password", "commands", "purpose"],
        },
    ),
]


def get_enabled_f5_tools() -> list[types.Tool]:
    from app.services.config_service import is_tool_enabled

    return [tool for tool in F5_TOOLS if is_tool_enabled(tool.name)]


def _tool_error(message: str) -> list[types.TextContent]:
    return [types.TextContent(type="text", text=format_tool_result({"success": False, "message": message}))]


async def call_f5_tool(name: str, arguments: dict) -> list[types.TextContent]:
    from app.services.config_service import is_tool_enabled

    if not is_tool_enabled(name):
        raise ValueError(f"Tool '{name}' is disabled in MCP server configuration")

    host = arguments.get("host", "")
    username = arguments.get("username", "")
    password = arguments.get("password", "")

    if name == "f5_test_connection":
        success, message = await test_connection(host, username, password)
        return [types.TextContent(type="text", text=format_tool_result({"success": success, "message": message}))]

    if name == "f5_ssh_run_command":
        command = arguments.get("command", "").strip()
        purpose = arguments.get("purpose", "").strip()
        if not command:
            return _tool_error("command is required")
        if not purpose:
            return _tool_error("purpose is required")
        payload = await ssh_run_command(host, username, password, command)
        return [types.TextContent(type="text", text=format_tool_result(payload))]

    if name == "f5_run_tmsh_command":
        command = arguments.get("command", "").strip()
        purpose = arguments.get("purpose", "").strip()
        if not command:
            return _tool_error("command is required")
        if not purpose:
            return _tool_error("purpose is required")
        payload = await run_tmsh_command(host, username, password, command)
        return [types.TextContent(type="text", text=format_tool_result(payload))]

    if name == "f5_run_tmsh_commands":
        commands = arguments.get("commands") or []
        purpose = arguments.get("purpose", "").strip()
        if not commands:
            return _tool_error("commands is required")
        if not purpose:
            return _tool_error("purpose is required")
        payload = await run_tmsh_commands(host, username, password, commands)
        return [types.TextContent(type="text", text=format_tool_result(payload))]

    raise ValueError(f"Unknown F5 tool: {name}")
