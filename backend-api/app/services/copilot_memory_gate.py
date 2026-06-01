import json
from typing import Any

NEXTGEN_API_TOOLS = frozenset(
    {
        "netscaler_get_system_info",
        "netscaler_list_applications",
        "netscaler_list_virtual_servers",
        "netscaler_list_virtual_ips",
        "netscaler_list_ip_addresses",
        "netscaler_nextgen_get",
        "netscaler_test_connection",
    }
)

NEXTGEN_WRITE_TOOLS = frozenset({"netscaler_create_application", "netscaler_nextgen_request"})

NEXTGEN_MEMORY_SEARCH_TOOL = "search_netscaler_nextgen_api"
CLI_MEMORY_SEARCH_TOOL = "search_netscaler_cli_reference"
SSH_TOOL = "netscaler_ssh_run_command"
CLI_WRITE_TOOL = "netscaler_run_cli_command"
CLI_BATCH_TOOL = "netscaler_run_cli_commands"
NEXTGEN_REQUEST_TOOL = "netscaler_nextgen_request"
WRITE_IP_TOOL = "netscaler_add_ip_address"

# Classic CLI verbs that destroy or disrupt configuration/state. These require
# explicit user confirmation before the MCP executes them. Additive/setup verbs
# (add, set, bind, enable, link, save, create, import, update, sync, ...) run
# automatically once the memory file has been consulted.
DESTRUCTIVE_CLI_VERBS = frozenset(
    {
        "rm",
        "clear",
        "delete",
        "reboot",
        "shutdown",
        "disable",
        "unbind",
        "flush",
        "reset",
        "unset",
        "kill",
        "force",
    }
)

READONLY_CLI_VERBS = frozenset({"show", "stat", "get", "count"})


def nextgen_memory_review_required(tool_name: str) -> bool:
    if tool_name in NEXTGEN_WRITE_TOOLS:
        return True
    return tool_name in NEXTGEN_API_TOOLS and tool_name != "netscaler_test_connection"


def cli_memory_review_required(tool_name: str) -> bool:
    return tool_name in {SSH_TOOL, CLI_WRITE_TOOL, CLI_BATCH_TOOL, WRITE_IP_TOOL}


def classify_cli_command(command: str) -> str:
    """Return 'read', 'write', or 'destructive' for a classic CLI command."""
    tokens = (command or "").strip().lower().split()
    if not tokens:
        return "read"
    verb = tokens[0]
    if verb in READONLY_CLI_VERBS:
        return "read"
    if verb in DESTRUCTIVE_CLI_VERBS:
        return "destructive"
    return "write"


def classify_nextgen_request(method: str, path: str) -> str:
    """Return 'read', 'write', or 'destructive' for a Next-Gen API request."""
    verb = (method or "GET").strip().upper()
    lowered_path = (path or "").strip().lower().rstrip("/")
    if verb == "GET":
        return "read"
    if verb == "DELETE":
        return "destructive"
    if lowered_path.endswith("/actions/disable") or lowered_path.endswith("/actions/uninstall"):
        return "destructive"
    return "write"


def destructive_confirmation_required(tool_name: str, arguments: dict[str, Any]) -> bool:
    """True when a write tool targets a destructive operation that the user has not confirmed."""
    if arguments.get("confirmed") is True:
        return False
    if tool_name == CLI_WRITE_TOOL:
        return classify_cli_command(arguments.get("command", "")) == "destructive"
    if tool_name == CLI_BATCH_TOOL:
        for command in arguments.get("commands") or []:
            if classify_cli_command(str(command)) == "destructive":
                return True
        return False
    if tool_name == NEXTGEN_REQUEST_TOOL:
        return (
            classify_nextgen_request(arguments.get("method", "GET"), arguments.get("path", ""))
            == "destructive"
        )
    return False


def block_result_for_unconfirmed_destructive(tool_name: str, arguments: dict[str, Any]) -> str:
    if tool_name == CLI_WRITE_TOOL:
        operation = arguments.get("command", "")
    elif tool_name == CLI_BATCH_TOOL:
        operation = "; ".join(str(cmd) for cmd in (arguments.get("commands") or []))
    else:
        operation = f"{arguments.get('method', '')} {arguments.get('path', '')}".strip()
    return json.dumps(
        {
            "success": False,
            "blocked": True,
            "needsConfirmation": True,
            "operation": operation,
            "message": (
                "This is a destructive operation. Do NOT execute it yet. "
                "Show the user the exact command/request above, explain its impact, and ask them to "
                "confirm. Only after the user explicitly agrees, call the tool again with confirmed=true."
            ),
            "requiredAction": (
                "Ask the user to confirm, then retry the same tool call with confirmed=true."
            ),
        },
        indent=2,
    )


def block_result_for_missing_nextgen_memory(tool_name: str) -> str:
    return json.dumps(
        {
            "success": False,
            "blocked": True,
            "message": (
                f"Tool '{tool_name}' blocked: call search_netscaler_nextgen_api first "
                "and read memoryExcerpts + suggestedGetPaths from netscaler_nextgen_api_memory.md."
            ),
            "requiredAction": "Call search_netscaler_nextgen_api with the user's question, then retry.",
        },
        indent=2,
    )


def block_result_for_missing_cli_memory(tool_name: str) -> str:
    return json.dumps(
        {
            "success": False,
            "blocked": True,
            "message": (
                f"Tool '{tool_name}' blocked: call search_netscaler_cli_reference first "
                "and read memoryExcerpts + recommendedCommands from netscaler_adc_cli_memory.md."
            ),
            "requiredAction": "Call search_netscaler_cli_reference with the user's question, then retry.",
        },
        indent=2,
    )


def apply_memory_review_gates(
    tool_name: str,
    nextgen_memory_reviewed: bool,
    cli_memory_reviewed: bool,
) -> tuple[bool, str | None]:
    if nextgen_memory_review_required(tool_name) and not nextgen_memory_reviewed:
        return False, block_result_for_missing_nextgen_memory(tool_name)
    if cli_memory_review_required(tool_name) and not cli_memory_reviewed:
        return False, block_result_for_missing_cli_memory(tool_name)
    return True, None


# Backward-compatible aliases
MEMORY_SEARCH_TOOL = NEXTGEN_MEMORY_SEARCH_TOOL
NEXTGEN_API_TOOLS_EXPORT = NEXTGEN_API_TOOLS


def memory_review_required(tool_name: str) -> bool:
    return nextgen_memory_review_required(tool_name)


def apply_memory_review_gate(tool_name: str, memory_reviewed: bool) -> tuple[bool, str | None]:
    allowed, blocked = apply_memory_review_gates(tool_name, memory_reviewed, cli_memory_reviewed=True)
    return allowed, blocked
