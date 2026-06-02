import json
import logging
import re
import sys
from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger("copilot.tools")
# Uvicorn does not configure app loggers, so attach our own stdout handler once
# to guarantee the tool-call audit trail shows up in `docker compose logs`.
if not logger.handlers:
    logger.setLevel(logging.INFO)
    _handler = logging.StreamHandler(sys.stdout)
    _handler.setFormatter(logging.Formatter("%(levelname)s:%(name)s:%(message)s"))
    logger.addHandler(_handler)
    logger.propagate = False

from app.schemas.copilot import ChatResponse, ChatAttachment, CopilotSettings, ToolCallTrace
from app.services.copilot_attachment_service import (
    build_anthropic_user_content,
    build_gemini_user_parts,
    build_openai_user_content,
    validate_attachments,
)
from app.services.ai_provider_service import lm_studio_endpoint_candidates, resolve_base_url
from app.services.copilot_service import (
    chat_anthropic,
    chat_gemini,
    chat_openai_compatible,
    execute_copilot_tool,
    get_enabled_copilot_tools,
    to_anthropic_tools,
    to_gemini_tools,
    to_openai_tools,
)
from app.services.copilot_form import (
    attach_default_lb_form_if_missing,
    parse_input_form,
    to_response_input_form,
)
from app.services.copilot_memory_gate import (
    CLI_MEMORY_SEARCH_TOOL,
    MEMORY_SEARCH_TOOL,
    apply_memory_review_gates,
    block_result_for_unconfirmed_destructive,
    destructive_confirmation_required,
)
from app.services.copilot_retry import build_tool_retry_hint
from app.services.encryption_service import decrypt_value

MAX_TOOL_ITERATIONS = 20
MAX_HISTORY_MESSAGES = 16
MAX_TOOL_RESULT_CHARS = 6000

# Tools that change appliance state. Used to detect fabricated execution claims.
WRITE_EXEC_TOOL_NAMES = frozenset(
    {
        "netscaler_create_application",
        "netscaler_add_ip_address",
        "netscaler_run_cli_command",
        "netscaler_run_cli_commands",
        "netscaler_nextgen_request",
    }
)

# Phrases that assert a configuration change was completed (not instructions/how-to).
_ACTION_CLAIM_PATTERN = re.compile(
    r"\b(executed successfully|commands? (were )?executed|running the following commands?|"
    r"the following commands? (will be |were )?(run|executed)|"
    r"successfully "
    r"(created|added|bound|deleted|removed|configured|applied|saved|updated|enabled|disabled)|"
    r"(have|has) been (created|added|bound|deleted|removed|configured|applied|saved|updated|enabled|disabled)|"
    r"i('ve| have)?\s*(created|added|bound|deleted|removed|configured|applied|saved|updated|enabled|disabled|run|ran)|"
    r"config(uration)? saved|saved (the )?config)\b",
    re.IGNORECASE,
)

# Prose that lists CLI verbs without a successful tool run — treat as unexecuted.
_CLI_LISTING_PATTERN = re.compile(
    r"(?m)^\s*(add|bind|set|enable|disable|rm|clear|save)\s+(lb|service|servicegroup|ns|vlan|route)\b",
    re.IGNORECASE,
)

CONFIG_CHANGE_VERBS = (
    "create",
    "add",
    "bind",
    "configure",
    "set up",
    "setup",
    "delete",
    "remove",
    "enable",
    "disable",
    "modify",
    "update",
)
CONFIG_CHANGE_NOUNS = (
    "vserver",
    "virtual server",
    "service group",
    "servicegroup",
    "lb ",
    "load balancer",
    "load-balancer",
    "backend",
    "service",
    "vip",
    "application",
    "monitor",
    "vlan",
    "route",
    "certificate",
    "policy",
)

FORCE_TOOL_EXECUTION_MESSAGE = (
    "STOP — you must EXECUTE the configuration with tools, not describe CLI commands in prose. "
    "If search_netscaler_cli_reference has not run yet, call it first. "
    "Then call netscaler_run_cli_commands with the full command list in order "
    "(preferred for multi-step LB setup), or netscaler_run_cli_command once per command. "
    "Include 'save ns config' at the end for classic config. "
    "Do not reply to the user until every command has succeeded."
)

UNEXECUTED_ACTION_BANNER = (
    "> ⚠️ **No changes were applied to the appliance.** The reply below claims a "
    "configuration change, but no NetScaler tool ran successfully this turn — so nothing "
    "was actually sent to the appliance. This usually means the current model is not reliably "
    "emitting tool calls. Switch to a more capable model (Anthropic Claude or a GPT-4o-class "
    "model) in **AI Providers**, retry, and verify on the appliance."
)


def _claims_config_change(content: str) -> bool:
    if not content:
        return False
    if _ACTION_CLAIM_PATTERN.search(content):
        return True
    return bool(_CLI_LISTING_PATTERN.search(content))


def _user_requests_config_change(user_message: str) -> bool:
    lowered = user_message.lower()
    has_verb = any(verb in lowered for verb in CONFIG_CHANGE_VERBS)
    has_noun = any(noun in lowered for noun in CONFIG_CHANGE_NOUNS)
    return has_verb and has_noun


def _user_wants_discovery_first(user_message: str) -> bool:
    lowered = user_message.lower()
    return any(
        phrase in lowered
        for phrase in (
            "ask me",
            "ask questions",
            "questions you need",
            "what do you need",
            "tell me what you need",
            "before you configure",
            "before configuring",
            "what information",
            "what details",
        )
    )


def _assistant_is_gathering_requirements(content: str) -> bool:
    if not content or not content.strip():
        return False
    lowered = content.lower()
    if "?" in content:
        return True
    return any(
        phrase in lowered
        for phrase in (
            "please provide",
            "please share",
            "please confirm",
            "i need the following",
            "could you provide",
            "can you provide",
            "let me know",
            "before i configure",
            "before i can configure",
            "missing information",
            "still need",
        )
    )


def _response_has_input_form(content: str) -> bool:
    _, form = parse_input_form(content)
    return form is not None


def _should_force_tool_execution(user_message: str, tool_traces: list[ToolCallTrace], content: str) -> bool:
    if content and _response_has_input_form(content):
        return False

    if _user_wants_discovery_first(user_message):
        return bool(content and (_CLI_LISTING_PATTERN.search(content) or _ACTION_CLAIM_PATTERN.search(content)))

    if content and _assistant_is_gathering_requirements(content) and not _had_successful_action(tool_traces):
        return False

    if not _user_requests_config_change(user_message):
        return False
    if _had_successful_action(tool_traces):
        return False
    if content and (_CLI_LISTING_PATTERN.search(content) or _ACTION_CLAIM_PATTERN.search(content)):
        return True
    exec_tools = {trace.name for trace in tool_traces} & WRITE_EXEC_TOOL_NAMES
    if not exec_tools and tool_traces:
        if content and _assistant_is_gathering_requirements(content):
            return False
        return True
    if not tool_traces:
        if _user_wants_discovery_first(user_message):
            return False
        return True
    return False


def _had_successful_action(tool_traces: list[ToolCallTrace]) -> bool:
    """True if at least one state-changing tool actually executed successfully this turn."""
    for trace in tool_traces:
        if trace.name not in WRITE_EXEC_TOOL_NAMES:
            continue
        try:
            payload = json.loads(trace.result)
        except (json.JSONDecodeError, TypeError):
            # A write/exec tool returned non-JSON output — treat as a real attempt.
            return True
        if not isinstance(payload, dict):
            return True
        if payload.get("blocked") or payload.get("needsConfirmation") or payload.get("success") is False:
            continue
        if trace.name == "netscaler_nextgen_request":
            method = str((trace.arguments or {}).get("method", "GET")).upper()
            if method == "GET":
                continue
        if trace.name in {"netscaler_run_cli_command", "netscaler_ssh_run_command"}:
            if payload.get("commandFailed"):
                continue
        return True
    return False


def guard_fabricated_execution(content: str, tool_traces: list[ToolCallTrace]) -> str:
    """Prepend a warning when the reply claims a config change that no tool actually performed."""
    if _claims_config_change(content) and not _had_successful_action(tool_traces):
        logger.warning(
            "fabricated_execution_guard fired — response claims a config change but no "
            "write/exec tool ran successfully (toolCalls=%d)",
            len(tool_traces),
        )
        return f"{UNEXECUTED_ACTION_BANNER}\n\n---\n\n{content}"
    return content

SYSTEM_PROMPT = """You are JPilot, an intelligent assistant for Citrix NetScaler ADC appliances.

Mandatory rules:
1. Answer only what the user asked. Do not add troubleshooting steps, verification checklists, or follow-up offers unless explicitly requested.
2. The user already selected and authenticated to the active appliance — use it for every NetScaler tool call.
3. Use only official documentation domains: developer-docs.netscaler.com, docs.netscaler.com, docs.citrix.com (plus any extra domains the admin allowed). When a search tool returns webResults (domain-restricted live web search), you may use and cite those URLs. Never cite or rely on other websites.
4. **Before any Next-Gen API tool call**, you MUST call search_netscaler_nextgen_api and read memoryExcerpts + suggestedGetPaths from netscaler_nextgen_api_memory.md.
5. **Before any SSH CLI command**, you MUST call search_netscaler_cli_reference and read **recommendedCommands** (exact syntax). When retrievalMode is `section`, also read memoryExcerpts. **Exception:** connectivity diagnostics (ping, ping6, traceroute, traceroute6) use netscaler_run_diagnostic directly and require NO search.
6. **ICMP connectivity checks ALWAYS use netscaler_run_diagnostic.** For "can the appliance ping X", "is X reachable" (no port), ping, or traceroute, call netscaler_run_diagnostic(operation, target) immediately. This tool is always available — never claim ping/traceroute is unavailable, never say the CLI reference lacks ping, and never tell the user to run it from the shell. A failed/unreachable result is a valid answer to report.
6b. **TCP port checks use netscaler_telnet or netscaler_run_diagnostic(operation=tcp_port, target, port).** For "is port N open on X", "can the appliance reach X:PORT", call immediately — do NOT use ping. Uses `shell sh -c '/usr/bin/telnet HOST PORT </dev/null'` on NetScaler (no GNU timeout, no netcat). NEVER claim port-check tools are broken without calling them. Report verdict open/refused/no_response. Ignore "ERROR: Export failed" CLI noise when telnet shows Connected to.
6c. **"Can YOU / JPilot reach the documentation or internet" uses jpilot_check_doc_connectivity — NOT an appliance ping.** That question is about the JPilot backend's own HTTPS reach to the official docs (and web search), which is a different host on a different network path than any appliance. Never answer "can you reach the docs" with a ping/telnet from a NetScaler; appliance reachability ≠ JPilot's reachability.
7. You can READ and WRITE configuration. Prefer NetScaler Next-Gen API tools:
   netscaler_get_system_info, netscaler_list_virtual_servers, netscaler_list_applications,
   netscaler_list_ip_addresses, netscaler_list_virtual_ips, netscaler_nextgen_get,
   netscaler_create_application (POST /applications),
   netscaler_nextgen_request (generic GET/POST/PUT/DELETE on any Next-Gen path),
   netscaler_run_diagnostic (ping/ping6/traceroute/traceroute6 — connectivity troubleshooting),
   netscaler_run_cli_command (any classic CLI verb: add/set/bind/unbind/enable/disable/rm/clear/save/...),
   netscaler_run_cli_commands (run multiple classic CLI commands in one call — preferred for multi-step LB setup).
8. Choosing how to fulfill a request:
   a. For application-centric or Next-Gen resources (applications, certificates, routes, config_sets):
      search_netscaler_nextgen_api first, then netscaler_create_application or netscaler_nextgen_request
      with the exact path + JSON body from netscaler_nextgen_api_memory.md.
   b. For classic-only config (lb/cs vserver, services, monitors, vlan, routes, features, modes, policies):
      search_netscaler_cli_reference first, then netscaler_run_cli_commands (multi-step) or netscaler_run_cli_command.
   c. Never invent syntax. Copy paths/payloads/commands from the memory files. For statistics use 'stat ...', never 'show ... statistics'.
   d. After classic CLI writes, run 'save ns config' to persist (Next-Gen API config persists automatically).
   e. If a write or command fails, read retryHint/suggestedCommand/errorMessage, fix it, and retry. Do not answer until it succeeds.
   f. For reads, if Next-Gen API tools do not return the data, fall back to a read-only command via netscaler_run_cli_command (or netscaler_ssh_run_command) after searching the CLI reference.
9. DESTRUCTIVE OPERATIONS require explicit user confirmation BEFORE execution:
   - Classic CLI: rm, clear, delete, reboot, shutdown, disable, unbind, flush, reset, unset, kill, force.
   - Next-Gen API: DELETE requests, and disable/uninstall actions.
   - For these, first show the user the exact command/request and its impact, and ask them to confirm.
     Only after the user explicitly agrees, call the tool again with confirmed=true.
   - Additive/setup operations (add, set, bind, enable, link, save, create, POST, PUT) run immediately — no confirmation needed.
   - If a destructive tool returns needsConfirmation, stop and ask the user; do not retry without confirmed=true.
10. Never tell the user to run manual CLI or GUI steps — perform the operation yourself with the tools.
11. Multi-step configuration (load balancers, StoreFront/Citrix, Delivery Controllers, CS vservers, SSL offload):
   a. **First** call search_netscaler_cli_reference (and search_netscaler_nextgen_api when application-centric). Use official syntax from memory excerpts.
   b. When VIP, backends, ports, SSL, or names are missing, reply with a **short intro** then a ```jpilot-form``` JSON block with inputForm.fields — **no prose after the fence**. Use sensible defaults (HTTP/80 or SSL/443 for Delivery Controllers, LEASTCONNECTION, tcp-default monitor). For service type, offer HTTP, SSL, TCP, UDP, and SSL_BRIDGE when relevant.
   c. If official docs have no workload-specific pattern, use the **default classic LB** shape: add lb vserver → service group → bind members → bind monitor → save ns config.
   d. **Do NOT** run write tools until the user submits the form or explicitly provided every value in chat.
   e. Form JSON shape: select options may be plain strings or {"value":"HTTPS","label":"HTTPS (port 443)"}. **Health monitor and load-balancing method must use `"type":"select"` with an `options` array** (e.g. monitor: tcp-default, http, ping, none). Example: {"inputForm":{"title":"...","fields":[{"id":"vip","label":"VIP","type":"text","required":true},{"id":"monitor","label":"Health monitor","type":"select","default":"tcp-default","options":["tcp-default","http","ping","none"]}]}}

Tool routing:
- All IPs / NSIP / SNIP / VIP / "show ns ip": netscaler_list_ip_addresses
- Add VIP / SNIP / NSIP (classic): search_netscaler_cli_reference (add ns ip), then netscaler_add_ip_address
- Create Next-Gen application / app with VIP and backends: search_netscaler_nextgen_api (AddApplication), then netscaler_create_application
- Modify / delete a Next-Gen resource (PUT/DELETE app, cert, route, config_set): search_netscaler_nextgen_api, then netscaler_nextgen_request
- Create / modify / delete classic config (add lb vserver, bind service, set/rm, enable feature):
  search_netscaler_cli_reference, then netscaler_run_cli_commands (preferred) or netscaler_run_cli_command
- Virtual servers / lb vserver / "show virtual servers": netscaler_list_virtual_servers (includes classic + Next-Gen)
- Firmware, version, build, hostname, serial, management IP only: netscaler_get_system_info
- Load-balancing VIPs only: netscaler_list_virtual_ips
- Next-Gen applications only: netscaler_list_applications
- VLAN / routing table / classic-only networking: search_netscaler_cli_reference, then netscaler_run_cli_command (show vlan, show route)
- "Can YOU / JPilot reach the documentation / internet" / "do you have internet access" / "can you fetch the docs": jpilot_check_doc_connectivity. This tests the JPilot BACKEND's own HTTPS reach to the official docs (and web search). Do NOT answer this with an appliance ping — the appliance and the JPilot backend are different hosts on different network paths.
- APPLIANCE connectivity ("can the appliance/NetScaler reach X", "is X reachable from NS01") / ping / traceroute / network path: netscaler_run_diagnostic (operation=ping|ping6|traceroute|traceroute6, target=<host>) — runs immediately, no memory search or confirmation needed. ICMP only; a failed ping just means the host is unreachable from the appliance — report that, don't retry. For reaching a web service, prefer a TCP/443 check (netscaler_telnet) over ICMP.
- TCP port reachability / "is port N open on X" / "can the appliance reach X on port N" / verify a backend service port: netscaler_telnet (target=<host>, port=<n>) — runs immediately, no memory search or confirmation needed. Reports verdict open/refused/no_response.
- Deeper network diagnostics (ARP table, interface/link status, packet capture): search_netscaler_cli_reference, then netscaler_ssh_run_command (show arp, show interface, stat interface, show nstrace)
- Performance statistics / counters / CPU or memory usage / event logs / newnslog analysis: netscaler_collect_nsconmsg (operation=current|stats|statswt0|event|memstats|consmsg|settime|oldconmsg, optional counter/vserver/selectors) — read-only nsconmsg, runs immediately, no memory search or confirmation needed
- Unknown Next-Gen resource: search_netscaler_nextgen_api (memory file), then netscaler_nextgen_get or netscaler_nextgen_request

Report tool results directly. State the command/request that was run and summarize its output.

When the user attaches files or images, analyze them in NetScaler context only if relevant to the question.
"""


def build_system_prompt(appliance_name: str) -> str:
    return (
        f"{SYSTEM_PROMPT}\n"
        f"Active appliance: {appliance_name}\n"
        f"Next-Gen API login is confirmed. Always pass appliance_name \"{appliance_name}\" to NetScaler tools.\n"
        "Official CLI/API behavioral rules are loaded on demand via search_netscaler_cli_reference and "
        "search_netscaler_nextgen_api — do not assume syntax without searching first."
    )


def trim_chat_history(history: list[dict]) -> list[dict]:
    if len(history) <= MAX_HISTORY_MESSAGES:
        return history
    return history[-MAX_HISTORY_MESSAGES:]


def _truncate_tool_result(result: str) -> str:
    if len(result) <= MAX_TOOL_RESULT_CHARS:
        return result
    return result[:MAX_TOOL_RESULT_CHARS] + "\n...[truncated for context]"


def _finalize_chat_response(
    content: str,
    *,
    provider_name: str,
    provider_type: str,
    model: str,
    tool_traces: list[ToolCallTrace],
    user_message: str = "",
) -> ChatResponse:
    cleaned, input_form = parse_input_form(content)
    cleaned, input_form = attach_default_lb_form_if_missing(user_message, cleaned, input_form)
    return ChatResponse(
        content=cleaned,
        providerName=provider_name,
        providerType=provider_type,
        model=model,
        toolCalls=tool_traces,
        inputForm=to_response_input_form(input_form),
    )


async def _execute_tool_with_memory_gate(
    db: AsyncIOMotorDatabase,
    name: str,
    arguments: dict[str, Any],
    appliance_name: str,
    nextgen_memory_reviewed: bool,
    cli_memory_reviewed: bool,
) -> tuple[str, bool, bool]:
    logger.info("tool_call name=%s args=%s", name, json.dumps(arguments, default=str)[:500])

    allowed, blocked = apply_memory_review_gates(name, nextgen_memory_reviewed, cli_memory_reviewed)
    if not allowed and blocked:
        logger.info("tool_call name=%s BLOCKED (memory review not satisfied)", name)
        return blocked, nextgen_memory_reviewed, cli_memory_reviewed

    if destructive_confirmation_required(name, arguments):
        logger.info("tool_call name=%s BLOCKED (awaiting destructive-op confirmation)", name)
        return (
            block_result_for_unconfirmed_destructive(name, arguments),
            nextgen_memory_reviewed,
            cli_memory_reviewed,
        )

    result = await execute_copilot_tool(db, name, arguments, default_appliance_name=appliance_name)
    logger.info("tool_call name=%s executed result=%s", name, (result or "")[:600])
    if name == MEMORY_SEARCH_TOOL:
        nextgen_memory_reviewed = True
    if name == CLI_MEMORY_SEARCH_TOOL:
        cli_memory_reviewed = True
    return result, nextgen_memory_reviewed, cli_memory_reviewed


async def get_default_provider(db: AsyncIOMotorDatabase) -> dict | None:
    provider = await db.aiProviders.find_one({"isDefault": True, "enabled": True})
    if provider is None:
        provider = await db.aiProviders.find_one({"enabled": True})
    return provider


async def resolve_chat_provider(db: AsyncIOMotorDatabase, provider_id: str | None) -> dict | None:
    """Pick the provider for this chat: the explicitly requested one, else the default."""
    if provider_id:
        from bson import ObjectId
        from bson.errors import InvalidId

        try:
            chosen = await db.aiProviders.find_one(
                {"_id": ObjectId(provider_id), "enabled": True}
            )
        except (InvalidId, TypeError):
            chosen = None
        if chosen is not None:
            return chosen
    return await get_default_provider(db)


async def run_copilot_chat(
    db: AsyncIOMotorDatabase,
    user_message: str,
    history: list[dict],
    attachments: list[ChatAttachment] | None = None,
    settings: CopilotSettings | None = None,
    appliance_name: str = "",
    provider_id: str | None = None,
    web_search: bool = True,
) -> ChatResponse:
    from app.services.copilot_service import set_web_search_allowed

    set_web_search_allowed(web_search)
    provider = await resolve_chat_provider(db, provider_id)
    if provider is None:
        raise ValueError("No enabled AI provider configured. Add one and set it as default.")

    chat_settings = settings or CopilotSettings()
    attachment_list = attachments or []
    validate_attachments(attachment_list, chat_settings)

    if not user_message.strip() and not attachment_list:
        raise ValueError("Message or attachments are required")

    api_key = decrypt_value(provider["encryptedApiKey"])
    provider_type = provider["providerType"]
    model = provider["model"]
    endpoint = provider.get("endpoint", "")

    tool_traces: list[ToolCallTrace] = []
    enabled_tools = await get_enabled_copilot_tools(db)
    enabled_tool_names = {tool["name"] for tool in enabled_tools}
    system_prompt = build_system_prompt(appliance_name)
    history = trim_chat_history(history)

    from app.services.copilot_port_check import try_auto_tcp_port_check

    auto_traces, auto_response = await try_auto_tcp_port_check(
        db,
        user_message=user_message,
        appliance_name=appliance_name,
        enabled_tool_names=enabled_tool_names,
    )
    if auto_traces:
        tool_traces.extend(auto_traces)
    if auto_response and auto_traces:
        provider_name = provider["providerName"]
        if auto_response.startswith("**") and "Verdict:" in auto_response:
            return _finalize_chat_response(
                auto_response,
                provider_name=provider_name,
                provider_type=provider_type,
                model=model,
                tool_traces=tool_traces,
                user_message=user_message,
            )
        system_prompt += auto_response

    provider_name = provider["providerName"]

    if provider_type == "Anthropic":
        content = await _run_anthropic_loop(
            db,
            api_key,
            model,
            user_message,
            history,
            tool_traces,
            attachment_list,
            enabled_tools,
            system_prompt,
            appliance_name,
            provider_name,
        )
    elif provider_type == "Gemini":
        content = await _run_gemini_loop(
            db,
            api_key,
            model,
            user_message,
            history,
            tool_traces,
            attachment_list,
            enabled_tools,
            system_prompt,
            appliance_name,
            provider_name,
        )
    elif provider_type in {"OpenAI", "Grok", "DeepSeek", "LM Studio", "OpenAI-Compatible"}:
        if provider_type == "LM Studio":
            lm_base_urls = lm_studio_endpoint_candidates(endpoint.strip())
            base_url = lm_base_urls[0]
            base_url_candidates = lm_base_urls
        else:
            base_url = resolve_base_url(provider_type, endpoint)
            base_url_candidates = None
        content = await _run_openai_loop(
            db,
            base_url,
            api_key,
            model,
            user_message,
            history,
            tool_traces,
            attachment_list,
            enabled_tools,
            system_prompt,
            appliance_name,
            base_url_candidates,
            provider_type,
            provider_name,
        )
    else:
        raise ValueError(f"Unsupported provider type: {provider_type}")

    logger.info(
        "chat_complete provider=%s model=%s toolCalls=%d names=%s",
        provider_type,
        model,
        len(tool_traces),
        [t.name for t in tool_traces],
    )
    if not tool_traces:
        logger.warning(
            "chat_complete produced an answer with ZERO tool calls — if it claims it changed "
            "the appliance, the model fabricated execution (no MCP tool ran). provider=%s model=%s",
            provider_type,
            model,
        )

    content = guard_fabricated_execution(content, tool_traces)

    return _finalize_chat_response(
        content,
        provider_name=provider["providerName"],
        provider_type=provider_type,
        model=model,
        tool_traces=tool_traces,
        user_message=user_message,
    )


async def _run_openai_loop(
    db: AsyncIOMotorDatabase,
    base_url: str,
    api_key: str,
    model: str,
    user_message: str,
    history: list[dict],
    tool_traces: list[ToolCallTrace],
    attachments: list[ChatAttachment],
    enabled_tools: list[dict[str, Any]],
    system_prompt: str,
    appliance_name: str,
    base_url_candidates: list[str] | None = None,
    provider_type: str = "OpenAI-Compatible",
    provider_name: str = "",
) -> str:
    messages: list[dict[str, Any]] = [{"role": "system", "content": system_prompt}]
    for item in history:
        messages.append({"role": item["role"], "content": item["content"]})
    messages.append(
        {
            "role": "user",
            "content": build_openai_user_content(user_message, attachments),
        }
    )

    tools = to_openai_tools(enabled_tools)
    active_base_url = base_url
    fallback_candidates = base_url_candidates
    nextgen_memory_reviewed = False
    cli_memory_reviewed = False

    for _ in range(MAX_TOOL_ITERATIONS):
        data, active_base_url = await chat_openai_compatible(
            base_url=active_base_url,
            api_key=api_key,
            model=model,
            messages=messages,
            tools=tools,
            base_url_candidates=fallback_candidates,
            provider_type=provider_type,
            provider_name=provider_name,
        )
        fallback_candidates = None
        choice = data["choices"][0]["message"]
        tool_calls = choice.get("tool_calls") or []

        if not tool_calls:
            content = choice.get("content") or ""
            if _should_force_tool_execution(user_message, tool_traces, content):
                logger.warning(
                    "execution_nudge — model replied without running write tools; forcing another iteration"
                )
                if content.strip():
                    messages.append({"role": "assistant", "content": content})
                messages.append({"role": "system", "content": FORCE_TOOL_EXECUTION_MESSAGE})
                continue
            return content or "I couldn't generate a response."

        messages.append(choice)

        retry_hints: list[str] = []
        for tool_call in tool_calls:
            fn = tool_call.get("function") or {}
            name = fn.get("name") or ""
            raw_arguments = fn.get("arguments") or "{}"
            try:
                arguments = json.loads(raw_arguments) if isinstance(raw_arguments, str) else dict(raw_arguments)
            except (json.JSONDecodeError, TypeError):
                arguments = {}
            try:
                result, nextgen_memory_reviewed, cli_memory_reviewed = await _execute_tool_with_memory_gate(
                    db, name, arguments, appliance_name, nextgen_memory_reviewed, cli_memory_reviewed
                )
            except Exception as exc:
                logger.exception("tool_call name=%s failed", name)
                result = json.dumps({"success": False, "errorMessage": str(exc)})

            tool_traces.append(ToolCallTrace(name=name, arguments=arguments, result=result))
            tool_call_id = tool_call.get("id") or f"call_{len(tool_traces)}"
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call_id,
                    "content": _truncate_tool_result(result),
                }
            )
            retry_hint = build_tool_retry_hint(name, result, user_message)
            if retry_hint:
                retry_hints.append(retry_hint)

        if retry_hints:
            messages.append({"role": "system", "content": "\n\n".join(retry_hints)})

    return "I reached the maximum number of tool calls. Please try a simpler request."


async def _run_gemini_loop(
    db: AsyncIOMotorDatabase,
    api_key: str,
    model: str,
    user_message: str,
    history: list[dict],
    tool_traces: list[ToolCallTrace],
    attachments: list[ChatAttachment],
    enabled_tools: list[dict[str, Any]],
    system_prompt: str,
    appliance_name: str,
    provider_name: str = "",
) -> str:
    contents: list[dict[str, Any]] = []
    for item in history:
        role = "model" if item["role"] == "assistant" else "user"
        contents.append({"role": role, "parts": [{"text": item["content"]}]})
    contents.append(
        {
            "role": "user",
            "parts": build_gemini_user_parts(user_message, attachments),
        }
    )

    tools = to_gemini_tools(enabled_tools)
    nextgen_memory_reviewed = False
    cli_memory_reviewed = False

    for _ in range(MAX_TOOL_ITERATIONS):
        data = await chat_gemini(
            api_key=api_key,
            model=model,
            system=system_prompt,
            contents=contents,
            tools=tools,
            provider_name=provider_name,
        )

        candidate = (data.get("candidates") or [{}])[0]
        content = candidate.get("content", {})
        parts = content.get("parts", [])

        function_calls = [part["functionCall"] for part in parts if part.get("functionCall")]
        text_parts = [part.get("text", "") for part in parts if part.get("text")]

        if not function_calls:
            content = "\n".join(text_parts).strip()
            if _should_force_tool_execution(user_message, tool_traces, content):
                logger.warning(
                    "execution_nudge — model replied without running write tools; forcing another iteration"
                )
                if content:
                    contents.append({"role": "model", "parts": [{"text": content}]})
                contents.append({"role": "user", "parts": [{"text": FORCE_TOOL_EXECUTION_MESSAGE}]})
                continue
            return content or "I couldn't generate a response."

        contents.append({"role": "model", "parts": parts})

        response_parts = []
        for function_call in function_calls:
            name = function_call["name"]
            arguments = function_call.get("args", {})
            result, nextgen_memory_reviewed, cli_memory_reviewed = await _execute_tool_with_memory_gate(
                db, name, arguments, appliance_name, nextgen_memory_reviewed, cli_memory_reviewed
            )
            tool_traces.append(ToolCallTrace(name=name, arguments=arguments, result=result))
            response_parts.append(
                {
                    "functionResponse": {
                        "name": name,
                        "response": {"result": result},
                    }
                }
            )
            retry_hint = build_tool_retry_hint(name, result, user_message)
            if retry_hint:
                response_parts.append({"text": retry_hint})

        contents.append({"role": "user", "parts": response_parts})

    return "I reached the maximum number of tool calls. Please try a simpler request."


async def _run_anthropic_loop(
    db: AsyncIOMotorDatabase,
    api_key: str,
    model: str,
    user_message: str,
    history: list[dict],
    tool_traces: list[ToolCallTrace],
    attachments: list[ChatAttachment],
    enabled_tools: list[dict[str, Any]],
    system_prompt: str,
    appliance_name: str,
    provider_name: str = "",
) -> str:
    messages: list[dict[str, Any]] = []
    for item in history:
        messages.append({"role": item["role"], "content": item["content"]})
    messages.append(
        {
            "role": "user",
            "content": build_anthropic_user_content(user_message, attachments),
        }
    )

    tools = to_anthropic_tools(enabled_tools)
    nextgen_memory_reviewed = False
    cli_memory_reviewed = False

    for _ in range(MAX_TOOL_ITERATIONS):
        data = await chat_anthropic(
            api_key=api_key,
            model=model,
            system=system_prompt,
            messages=messages,
            tools=tools,
            provider_name=provider_name,
        )

        content_blocks = data.get("content", [])
        tool_uses = [block for block in content_blocks if block.get("type") == "tool_use"]
        text_blocks = [block.get("text", "") for block in content_blocks if block.get("type") == "text"]
        stop_reason = data.get("stop_reason")

        if stop_reason != "tool_use" and not tool_uses:
            content = "\n".join(text_blocks).strip()
            if _should_force_tool_execution(user_message, tool_traces, content):
                logger.warning(
                    "execution_nudge — model replied without running write tools; forcing another iteration"
                )
                if content_blocks:
                    messages.append({"role": "assistant", "content": content_blocks})
                messages.append({"role": "user", "content": [{"type": "text", "text": FORCE_TOOL_EXECUTION_MESSAGE}]})
                continue
            return content or "I couldn't generate a response."

        messages.append({"role": "assistant", "content": content_blocks})

        tool_results = []
        for tool_use in tool_uses:
            name = tool_use["name"]
            arguments = tool_use.get("input", {})
            result, nextgen_memory_reviewed, cli_memory_reviewed = await _execute_tool_with_memory_gate(
                db, name, arguments, appliance_name, nextgen_memory_reviewed, cli_memory_reviewed
            )
            tool_traces.append(ToolCallTrace(name=name, arguments=arguments, result=result))
            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": tool_use["id"],
                    "content": result,
                }
            )
            retry_hint = build_tool_retry_hint(name, result, user_message)
            if retry_hint:
                tool_results.append({"type": "text", "text": retry_hint})

        messages.append({"role": "user", "content": tool_results})

    return "I reached the maximum number of tool calls. Please try a simpler request."
