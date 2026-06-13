import json
from typing import Any

NEXTGEN_API_TOOLS = frozenset(
    {
        "netscaler_get_system_info",
        "netscaler_list_applications",
        "netscaler_list_virtual_servers",
        "netscaler_list_virtual_ips",
        "netscaler_list_ip_addresses",
        "netscaler_list_service_status",
        "netscaler_nextgen_get",
        "netscaler_test_connection",
    }
)

# Curated read tools with fixed Next-Gen/NITRO endpoints — no memory search before use.
NEXTGEN_CURATED_READ_TOOLS = frozenset(
    {
        "netscaler_get_system_info",
        "netscaler_list_applications",
        "netscaler_list_virtual_servers",
        "netscaler_list_virtual_ips",
        "netscaler_list_ip_addresses",
        "netscaler_list_service_status",
    }
)

NEXTGEN_WRITE_TOOLS = frozenset({"netscaler_create_application", "netscaler_nextgen_request"})

NEXTGEN_MEMORY_SEARCH_TOOL = "search_netscaler_nextgen_api"
CLI_MEMORY_SEARCH_TOOL = "search_netscaler_cli_reference"
CISCO_CLI_MEMORY_SEARCH_TOOL = "search_cisco_cli_reference"
SDX_CLI_MEMORY_SEARCH_TOOL = "search_sdx_cli_reference"
F5_CLI_MEMORY_SEARCH_TOOL = "search_f5_tmsh_reference"
SSH_TOOL = "netscaler_ssh_run_command"
CLI_WRITE_TOOL = "netscaler_run_cli_command"
CLI_BATCH_TOOL = "netscaler_run_cli_commands"
CISCO_SSH_TOOL = "cisco_ssh_run_command"
CISCO_CLI_WRITE_TOOL = "cisco_run_cli_command"
CISCO_CLI_BATCH_TOOL = "cisco_run_cli_commands"
SDX_SSH_TOOL = "sdx_ssh_run_command"
SDX_CLI_WRITE_TOOL = "sdx_run_cli_command"
SDX_CLI_BATCH_TOOL = "sdx_run_cli_commands"
F5_SSH_TOOL = "f5_ssh_run_command"
F5_CLI_WRITE_TOOL = "f5_run_tmsh_command"
F5_CLI_BATCH_TOOL = "f5_run_tmsh_commands"
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

READONLY_CLI_VERBS = frozenset(
    {"show", "stat", "get", "count", "ping", "ping6", "traceroute", "traceroute6"}
)


def nextgen_memory_review_required(tool_name: str) -> bool:
    if tool_name in NEXTGEN_WRITE_TOOLS:
        return True
    if tool_name in NEXTGEN_CURATED_READ_TOOLS:
        return False
    return tool_name in NEXTGEN_API_TOOLS and tool_name != "netscaler_test_connection"


def cli_memory_review_required(tool_name: str) -> bool:
    return tool_name in {
        SSH_TOOL,
        CLI_WRITE_TOOL,
        CLI_BATCH_TOOL,
        WRITE_IP_TOOL,
        CISCO_CLI_WRITE_TOOL,
        CISCO_CLI_BATCH_TOOL,
        SDX_CLI_WRITE_TOOL,
        SDX_CLI_BATCH_TOOL,
        F5_CLI_WRITE_TOOL,
        F5_CLI_BATCH_TOOL,
    }


CISCO_DESTRUCTIVE_VERBS = frozenset({"reload", "erase", "delete", "write"})


def classify_cisco_command(command: str) -> str:
    tokens = (command or "").strip().lower().split()
    if not tokens:
        return "read"
    if tokens[0] in {"show", "display", "ping", "traceroute", "traceroute6"}:
        return "read"
    joined = " ".join(tokens)
    if any(term in joined for term in ("reload", "erase", "write erase", "delete")):
        return "destructive"
    return "write"


def classify_f5_command(command: str) -> str:
    lowered = (command or "").strip().lower()
    if not lowered:
        return "read"
    if lowered.startswith(
        (
            "tmsh show ",
            "tmsh list ",
            "show ",
            "list ",
            "ping ",
            "traceroute ",
        )
    ):
        return "read"
    destructive_terms = ("delete ", "restart ", "reboot ", "remove ", "uninstall ", "load sys config")
    if any(term in lowered for term in destructive_terms):
        return "destructive"
    return "write"


def classify_sdx_command(command: str) -> str:
    lowered = (command or "").strip().lower()
    if not lowered:
        return "read"
    if lowered.startswith("show "):
        return "read"
    destructive_terms = (
        "force-stop",
        "delete virtualserver",
        "delete vlan",
        "install firmware",
        "upgrade virtualserver",
        "shutdown virtualserver",
        "restart virtualserver",
        "service svm restart",
        " reboot",
        "reboot ",
    )
    if any(term in lowered for term in destructive_terms):
        return "destructive"
    return "write"


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
    if tool_name == CISCO_CLI_WRITE_TOOL:
        return classify_cisco_command(arguments.get("command", "")) == "destructive"
    if tool_name == F5_CLI_WRITE_TOOL:
        return classify_f5_command(arguments.get("command", "")) == "destructive"
    if tool_name == SDX_CLI_WRITE_TOOL:
        return classify_sdx_command(arguments.get("command", "")) == "destructive"
    if tool_name == CLI_BATCH_TOOL:
        for command in arguments.get("commands") or []:
            if classify_cli_command(str(command)) == "destructive":
                return True
        return False
    if tool_name == CISCO_CLI_BATCH_TOOL:
        for command in arguments.get("commands") or []:
            if classify_cisco_command(str(command)) == "destructive":
                return True
        return False
    if tool_name == F5_CLI_BATCH_TOOL:
        for command in arguments.get("commands") or []:
            if classify_f5_command(str(command)) == "destructive":
                return True
        return False
    if tool_name == SDX_CLI_BATCH_TOOL:
        for command in arguments.get("commands") or []:
            if classify_sdx_command(str(command)) == "destructive":
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
    elif tool_name == CISCO_CLI_WRITE_TOOL:
        operation = arguments.get("command", "")
    elif tool_name == CLI_BATCH_TOOL:
        operation = "; ".join(str(cmd) for cmd in (arguments.get("commands") or []))
    elif tool_name == CISCO_CLI_BATCH_TOOL:
        operation = "; ".join(str(cmd) for cmd in (arguments.get("commands") or []))
    elif tool_name == F5_CLI_WRITE_TOOL:
        operation = arguments.get("command", "")
    elif tool_name == SDX_CLI_WRITE_TOOL:
        operation = arguments.get("command", "")
    elif tool_name == F5_CLI_BATCH_TOOL:
        operation = "; ".join(str(cmd) for cmd in (arguments.get("commands") or []))
    elif tool_name == SDX_CLI_BATCH_TOOL:
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
    if tool_name.startswith("cisco_"):
        memory_hint = "cisco_ios_switch_memory.md"
        search_tool = CISCO_CLI_MEMORY_SEARCH_TOOL
    elif tool_name.startswith("f5_"):
        memory_hint = "f5_bigip_tmsh_memory.md"
        search_tool = F5_CLI_MEMORY_SEARCH_TOOL
    elif tool_name.startswith("sdx_"):
        memory_hint = "netscaler_sdx_cli_memory.md"
        search_tool = SDX_CLI_MEMORY_SEARCH_TOOL
    else:
        memory_hint = "netscaler_adc_cli_memory.md"
        search_tool = CLI_MEMORY_SEARCH_TOOL
    return json.dumps(
        {
            "success": False,
            "blocked": True,
            "message": (
                f"Tool '{tool_name}' blocked: call {search_tool} first "
                f"and read memoryExcerpts + recommendedCommands from {memory_hint}."
            ),
            "requiredAction": f"Call {search_tool} with the user's question, then retry.",
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
