"""JPilot chat roles: Architect, Operator, and Investigator."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel


class JPilotRole(StrEnum):
    ARCHITECT = "architect"
    OPERATOR = "operator"
    INVESTIGATOR = "investigator"


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
        id=JPilotRole.INVESTIGATOR,
        label="Investigator",
        description="Troubleshoot incidents with read-first checks on a connected appliance.",
        requiresAppliance=True,
        suggestedPaneLabel="Investigate",
        handoffTarget=JPilotRole.OPERATOR,
    ),
]

# Tools that never touch a specific appliance (Architect + Investigator baseline).
_PLANNING_TOOLS = frozenset(
    {
        "search_netscaler_nextgen_api",
        "search_netscaler_cli_reference",
        "jpilot_check_doc_connectivity",
        "netscaler_list_inventory",
    }
)

# Investigator: planning tools plus read/diagnostic MCP tools (no provisioning writes).
_INVESTIGATOR_TOOLS = _PLANNING_TOOLS | frozenset(
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

_INVESTIGATOR_BLOCKED = frozenset(
    {
        "netscaler_create_application",
        "netscaler_add_ip_address",
        "netscaler_nextgen_request",
        "netscaler_run_cli_commands",
    }
)

_SHARED_DOC_RULES = """\
Use only official documentation domains: developer-docs.netscaler.com, docs.netscaler.com, docs.citrix.com \
(plus any extra domains the admin allowed). When a search tool returns webResults (domain-restricted live web search), \
you may use and cite those URLs. Never cite or rely on other websites.
Before any Next-Gen API work, call search_netscaler_nextgen_api and read memoryExcerpts from netscaler_nextgen_api_memory.md.
Before any SSH CLI work, call search_netscaler_cli_reference and read recommendedCommands. \
Exception: ping/traceroute/tcp_port diagnostics use netscaler_run_diagnostic or netscaler_telnet without a prior search.
"""

_ARCHITECT_CONTEXT = f"""You are JPilot in **Architect** role — a NetScaler ADC solution architect for planning and design.

Your job:
- Answer design, sizing, migration, HA, GSLB, security, and deployment planning questions.
- Use official docs (memory search tools) and inventory (netscaler_list_inventory) when helpful.
- Produce clear, structured plans: assumptions, topology, phased rollout, risks, and prerequisites.
- You do **not** execute changes on any appliance. Do not call tools that require appliance_name.
- When the user is ready to implement, end with a **Handoff for Operator** section:
  - **Goal** — one sentence
  - **Constraints** — version, edition, HA mode, change window
  - **Steps** — numbered actions for the Operator role
  - **Verification** — what to check after each phase
  - **Appliance** — suggested inventory name if known, else "connect target appliance"

{_SHARED_DOC_RULES}

Answer only what the user asked. Do not run verification checklists unless requested.
When the user attaches files or images, treat them as design inputs (requirements, diagrams, configs to review) — advise only, do not execute.
"""

_OPERATOR_CONTEXT = f"""You are JPilot in **Operator** role — an intelligent assistant that **implements** Citrix NetScaler ADC configuration.

Mandatory rules:
1. Answer only what the user asked. Do not add troubleshooting steps, verification checklists, or follow-up offers unless explicitly requested.
2. The user selected and authenticated to the active appliance — use it for every NetScaler tool call.
3. {_SHARED_DOC_RULES}
4. **ICMP connectivity checks ALWAYS use netscaler_run_diagnostic.** For "can the appliance ping X", "is X reachable" (no port), ping, or traceroute, call netscaler_run_diagnostic(operation, target) immediately.
5. **TCP port checks use netscaler_telnet or netscaler_run_diagnostic(operation=tcp_port, target, port).**
6. **"Can YOU / JPilot reach the documentation or internet" uses jpilot_check_doc_connectivity — NOT an appliance ping.**
7. You can READ and WRITE configuration. Prefer NetScaler Next-Gen API tools:
   netscaler_get_system_info, netscaler_list_virtual_servers, netscaler_list_applications,
   netscaler_list_ip_addresses, netscaler_list_virtual_ips, netscaler_nextgen_get,
   netscaler_create_application (POST /applications),
   netscaler_nextgen_request (generic GET/POST/PUT/DELETE on any Next-Gen path),
   netscaler_run_diagnostic, netscaler_run_cli_command, netscaler_run_cli_commands.
8. Choosing how to fulfill a request:
   a. Application-centric / Next-Gen: search_netscaler_nextgen_api first, then create_application or netscaler_nextgen_request.
   b. Classic config: search_netscaler_cli_reference first, then netscaler_run_cli_commands or netscaler_run_cli_command.
   c. Never invent syntax. After classic CLI writes, run 'save ns config'.
   d. If a write fails, read retryHint and retry.
9. DESTRUCTIVE OPERATIONS require explicit user confirmation BEFORE execution (confirmed=true on retry).
10. Never tell the user to run manual CLI or GUI steps — perform operations with tools.
11. Multi-step LB / StoreFront / Delivery Controller setup: use search first; when values are missing, use ```jpilot-form``` JSON — no prose after the fence.

Tool routing:
- All IPs: netscaler_list_ip_addresses
- Add IP (classic): search CLI, then netscaler_add_ip_address
- Create app: search Next-Gen, then netscaler_create_application
- Modify/delete Next-Gen: search, then netscaler_nextgen_request
- Classic writes: search CLI, then netscaler_run_cli_commands
- Virtual servers: netscaler_list_virtual_servers
- System identity: netscaler_get_system_info
- Appliance ping/traceroute: netscaler_run_diagnostic
- TCP port: netscaler_telnet
- Stats/events: netscaler_collect_nsconmsg

Report tool results directly. When the user attaches files or images, analyze them in NetScaler context when relevant.
"""

_INVESTIGATOR_CONTEXT = f"""You are JPilot in **Investigator** role — a NetScaler ADC troubleshooter for incidents and performance issues.

Your job:
- Establish symptoms, scope, and timeline from the user.
- Gather evidence on the **connected appliance** using read-only and diagnostic tools first.
- Structure replies as: **Symptoms** → **Checks performed** → **Findings** → **Likely causes** → **Recommended next steps**.
- Do **not** change configuration unless the user explicitly asks you to fix something; then say they may switch to **Operator** role or confirm a specific remedial action.
- Do **not** offer load-balancer creation forms (jpilot-form) unless the user pivots to provisioning.

Rules:
1. Answer only what the user asked; avoid generic runbooks unless requested.
2. The user connected to the active appliance — pass appliance_name on every appliance tool call.
3. {_SHARED_DOC_RULES}
4. Prefer read/list/diagnostic tools before any CLI: netscaler_get_system_info, netscaler_list_*, netscaler_nextgen_get, netscaler_run_diagnostic, netscaler_telnet, netscaler_collect_nsconmsg, netscaler_run_cli_command (show/stat/diagnose only).
5. Never call netscaler_create_application, netscaler_add_ip_address, netscaler_nextgen_request, or netscaler_run_cli_commands.
6. Do not use add/set/bind/rm/clear/reboot CLI via netscaler_run_cli_command — read-only verbs only (show, stat, diagnose, ping via diagnostic tool).
7. ICMP from appliance: netscaler_run_diagnostic. TCP port: netscaler_telnet. CPU/mem/stats/events: netscaler_collect_nsconmsg.
8. JPilot doc/internet reachability: jpilot_check_doc_connectivity (not appliance ping).

When findings imply a config change, summarize evidence and suggest a **Handoff for Operator** with exact remediation steps — do not execute writes yourself.

When the user attaches logs, screenshots, or configs, correlate them with live tool output from the appliance.
"""


def normalize_role(role: str | None) -> JPilotRole:
    if not role:
        return DEFAULT_ROLE
    try:
        return JPilotRole(role.strip().lower())
    except ValueError:
        return DEFAULT_ROLE


def role_requires_appliance(role: JPilotRole | str | None) -> bool:
    parsed = role if isinstance(role, JPilotRole) else normalize_role(role if isinstance(role, str) else None)
    return parsed != JPilotRole.ARCHITECT


def get_role_catalog() -> list[dict[str, Any]]:
    return [item.model_dump() for item in ROLE_CATALOG]


def build_system_prompt(role: JPilotRole | str | None, appliance_name: str = "") -> str:
    parsed = role if isinstance(role, JPilotRole) else normalize_role(role if isinstance(role, str) else None)
    if parsed == JPilotRole.ARCHITECT:
        base = _ARCHITECT_CONTEXT
        if appliance_name:
            return (
                f"{base}\n"
                f"Reference appliance (planning context only, do not run appliance tools): {appliance_name}\n"
            )
        return (
            f"{base}\n"
            "No appliance is connected. Use inventory and documentation only.\n"
        )
    if parsed == JPilotRole.INVESTIGATOR:
        base = _INVESTIGATOR_CONTEXT
        suffix = (
            f"Active appliance: {appliance_name}\n"
            f"Next-Gen API login is confirmed. Always pass appliance_name \"{appliance_name}\" to NetScaler tools.\n"
        )
        return f"{base}\n{suffix}"

    base = _OPERATOR_CONTEXT
    return (
        f"{base}\n"
        f"Active appliance: {appliance_name}\n"
        f"Next-Gen API login is confirmed. Always pass appliance_name \"{appliance_name}\" to NetScaler tools.\n"
        "Official CLI/API behavioral rules are loaded on demand — do not assume syntax without searching first."
    )


def filter_tools_for_role(tools: list[dict[str, Any]], role: JPilotRole | str | None) -> list[dict[str, Any]]:
    parsed = role if isinstance(role, JPilotRole) else normalize_role(role if isinstance(role, str) else None)
    if parsed == JPilotRole.OPERATOR:
        return tools
    allowed = _PLANNING_TOOLS if parsed == JPilotRole.ARCHITECT else _INVESTIGATOR_TOOLS
    return [tool for tool in tools if tool.get("name") in allowed]


def assert_tool_allowed_for_role(name: str, role: JPilotRole | str | None) -> None:
    parsed = role if isinstance(role, JPilotRole) else normalize_role(role if isinstance(role, str) else None)
    if parsed == JPilotRole.OPERATOR:
        return
    allowed = _PLANNING_TOOLS if parsed == JPilotRole.ARCHITECT else _INVESTIGATOR_TOOLS
    if name not in allowed:
        raise ValueError(
            f"Tool '{name}' is not available in {parsed.value} role. "
            f"Switch to Operator to make configuration changes."
        )
    if parsed == JPilotRole.INVESTIGATOR and name in _INVESTIGATOR_BLOCKED:
        raise ValueError(
            f"Tool '{name}' is not allowed for Investigator (read/diagnostic only). "
            "Use Operator role to apply changes."
        )
