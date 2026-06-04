import mcp.types as types

from app.services.netscaler_service import format_tool_result
from app.services.sdx_ssh_service import (
    run_cli_command,
    run_cli_commands,
    ssh_run_command,
    test_connection,
)

SDX_TOOLS = [
    types.Tool(
        name="sdx_test_connection",
        description="Test SSH connectivity to a NetScaler SDX Management Service using show version.",
        inputSchema={
            "type": "object",
            "properties": {
                "host": {"type": "string", "description": "SDX SVM hostname or IP"},
                "username": {"type": "string", "description": "SSH username"},
                "password": {"type": "string", "description": "SSH password"},
            },
            "required": ["host", "username", "password"],
        },
    ),
    types.Tool(
        name="sdx_ssh_run_command",
        description=(
            "Run a read-only NetScaler SDX SVM command over SSH (show only). "
            "Use after search_sdx_cli_reference when syntax is uncertain."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "host": {"type": "string"},
                "username": {"type": "string"},
                "password": {"type": "string"},
                "command": {"type": "string", "description": "Read-only show command"},
                "purpose": {"type": "string", "description": "Why this command is needed"},
            },
            "required": ["host", "username", "password", "command", "purpose"],
        },
    ),
    types.Tool(
        name="sdx_run_cli_command",
        description=(
            "Run a single NetScaler SDX SVM CLI command over SSH (VPX lifecycle, VLAN, firmware). "
            "Use ONLY after search_sdx_cli_reference confirms syntax."
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
        name="sdx_run_cli_commands",
        description=(
            "Run ordered NetScaler SDX SVM CLI commands over SSH. "
            "Use ONLY after search_sdx_cli_reference confirms syntax."
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
                    "description": "Ordered SDX SVM commands",
                },
                "purpose": {"type": "string"},
            },
            "required": ["host", "username", "password", "commands", "purpose"],
        },
    ),
]


def get_enabled_sdx_tools() -> list[types.Tool]:
    from app.services.config_service import is_tool_enabled

    return [tool for tool in SDX_TOOLS if is_tool_enabled(tool.name)]


def _tool_error(message: str) -> list[types.TextContent]:
    return [types.TextContent(type="text", text=format_tool_result({"success": False, "message": message}))]


async def call_sdx_tool(name: str, arguments: dict) -> list[types.TextContent]:
    from app.services.config_service import is_tool_enabled

    if not is_tool_enabled(name):
        raise ValueError(f"Tool '{name}' is disabled in MCP server configuration")

    host = arguments.get("host", "")
    username = arguments.get("username", "")
    password = arguments.get("password", "")

    if name == "sdx_test_connection":
        success, message = await test_connection(host, username, password)
        return [types.TextContent(type="text", text=format_tool_result({"success": success, "message": message}))]

    if name == "sdx_ssh_run_command":
        command = arguments.get("command", "").strip()
        purpose = arguments.get("purpose", "").strip()
        if not command:
            return _tool_error("command is required")
        if not purpose:
            return _tool_error("purpose is required")
        payload = await ssh_run_command(host, username, password, command)
        return [types.TextContent(type="text", text=format_tool_result(payload))]

    if name == "sdx_run_cli_command":
        command = arguments.get("command", "").strip()
        purpose = arguments.get("purpose", "").strip()
        if not command:
            return _tool_error("command is required")
        if not purpose:
            return _tool_error("purpose is required")
        payload = await run_cli_command(host, username, password, command)
        return [types.TextContent(type="text", text=format_tool_result(payload))]

    if name == "sdx_run_cli_commands":
        commands = arguments.get("commands") or []
        purpose = arguments.get("purpose", "").strip()
        if not commands:
            return _tool_error("commands is required")
        if not purpose:
            return _tool_error("purpose is required")
        payload = await run_cli_commands(host, username, password, commands)
        return [types.TextContent(type="text", text=format_tool_result(payload))]

    raise ValueError(f"Unknown SDX tool: {name}")
