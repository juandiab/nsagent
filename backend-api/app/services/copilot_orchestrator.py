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
from app.services.copilot_memory_gate import (
    CLI_MEMORY_SEARCH_TOOL,
    MEMORY_SEARCH_TOOL,
    apply_memory_review_gates,
    block_result_for_unconfirmed_destructive,
    destructive_confirmation_required,
)
from app.services.copilot_retry import build_tool_retry_hint
from app.services.encryption_service import decrypt_value
from app.services.adc_cli_memory_service import get_cli_behavioral_rules
from app.services.nextgen_memory_service import get_behavioral_rules

MAX_TOOL_ITERATIONS = 20

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


def _should_force_tool_execution(user_message: str, tool_traces: list[ToolCallTrace], content: str) -> bool:
    if not _user_requests_config_change(user_message):
        return False
    if _had_successful_action(tool_traces):
        return False
    if content and (_CLI_LISTING_PATTERN.search(content) or _ACTION_CLAIM_PATTERN.search(content)):
        return True
    exec_tools = {trace.name for trace in tool_traces} & WRITE_EXEC_TOOL_NAMES
    if not exec_tools and tool_traces:
        # Searched memory but never executed — common failure mode.
        return True
    if not tool_traces:
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

SYSTEM_PROMPT = """You are NetScaler Copilot, an intelligent assistant for Citrix NetScaler ADC appliances.

Mandatory rules:
1. Answer only what the user asked. Do not add troubleshooting steps, verification checklists, or follow-up offers unless explicitly requested.
2. The user already selected and authenticated to the active appliance — use it for every NetScaler tool call.
3. Use only official documentation domains: developer-docs.netscaler.com, docs.netscaler.com, docs.citrix.com. Never cite or rely on other websites.
4. **Before any Next-Gen API tool call**, you MUST call search_netscaler_nextgen_api and read memoryExcerpts + suggestedGetPaths from netscaler_nextgen_api_memory.md.
5. **Before any SSH CLI command**, you MUST call search_netscaler_cli_reference and read memoryExcerpts + recommendedCommands from netscaler_adc_cli_memory.md. **Exception:** connectivity diagnostics (ping, ping6, traceroute, traceroute6) use netscaler_run_diagnostic directly and require NO search.
6. **ICMP connectivity checks ALWAYS use netscaler_run_diagnostic.** For "can the appliance ping X", "is X reachable" (no port), ping, or traceroute, call netscaler_run_diagnostic(operation, target) immediately. This tool is always available — never claim ping/traceroute is unavailable, never say the CLI reference lacks ping, and never tell the user to run it from the shell. A failed/unreachable result is a valid answer to report.
6b. **TCP port checks use netscaler_telnet or netscaler_run_diagnostic(operation=tcp_port, target, port).** For "is port N open on X", "can the appliance reach X:PORT", call immediately — do NOT use ping. Uses `shell sh -c '/usr/bin/telnet HOST PORT </dev/null'` on NetScaler (no GNU timeout, no netcat). NEVER claim port-check tools are broken without calling them. Report verdict open/refused/no_response. Ignore "ERROR: Export failed" CLI noise when telnet shows Connected to.
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
- Connectivity troubleshooting / "can the appliance reach X" / "is X reachable" / ping / traceroute / network path: netscaler_run_diagnostic (operation=ping|ping6|traceroute|traceroute6, target=<host>) — runs immediately, no memory search or confirmation needed. A failed ping just means the host is unreachable; report that, don't retry.
- TCP port reachability / "is port N open on X" / "can the appliance reach X on port N" / verify a backend service port: netscaler_telnet (target=<host>, port=<n>) — runs immediately, no memory search or confirmation needed. Reports verdict open/refused/no_response.
- Deeper network diagnostics (ARP table, interface/link status, packet capture): search_netscaler_cli_reference, then netscaler_ssh_run_command (show arp, show interface, stat interface, show nstrace)
- Performance statistics / counters / CPU or memory usage / event logs / newnslog analysis: netscaler_collect_nsconmsg (operation=current|stats|statswt0|event|memstats|consmsg|settime|oldconmsg, optional counter/vserver/selectors) — read-only nsconmsg, runs immediately, no memory search or confirmation needed
- Unknown Next-Gen resource: search_netscaler_nextgen_api (memory file), then netscaler_nextgen_get or netscaler_nextgen_request

Report tool results directly. State the command/request that was run and summarize its output.

When the user attaches files or images, analyze them in NetScaler context only if relevant to the question.
"""


def build_system_prompt(appliance_name: str) -> str:
    nextgen_rules = get_behavioral_rules()
    cli_rules = get_cli_behavioral_rules()
    blocks: list[str] = [SYSTEM_PROMPT]
    if nextgen_rules:
        blocks.append(f"\nNetScaler Next-Gen API behavioral rules (memory file):\n{nextgen_rules}")
    if cli_rules:
        blocks.append(f"\nNetScaler ADC CLI behavioral rules (memory file):\n{cli_rules}")
    return (
        f"{''.join(blocks)}\n"
        f"Active appliance: {appliance_name}\n"
        f"Next-Gen API login is confirmed. Always pass appliance_name \"{appliance_name}\" to NetScaler tools."
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


async def run_copilot_chat(
    db: AsyncIOMotorDatabase,
    user_message: str,
    history: list[dict],
    attachments: list[ChatAttachment] | None = None,
    settings: CopilotSettings | None = None,
    appliance_name: str = "",
) -> ChatResponse:
    provider = await get_default_provider(db)
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
            return ChatResponse(
                content=auto_response,
                providerName=provider_name,
                providerType=provider_type,
                model=model,
                toolCalls=tool_traces,
            )
        system_prompt += auto_response

    if provider_type == "Anthropic":
        content = await _run_anthropic_loop(
            db, api_key, model, user_message, history, tool_traces, attachment_list, enabled_tools, system_prompt, appliance_name
        )
    elif provider_type == "Gemini":
        content = await _run_gemini_loop(
            db, api_key, model, user_message, history, tool_traces, attachment_list, enabled_tools, system_prompt, appliance_name
        )
    elif provider_type in {"OpenAI", "Grok", "LM Studio", "OpenAI-Compatible"}:
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

    return ChatResponse(
        content=content,
        providerName=provider["providerName"],
        providerType=provider_type,
        model=model,
        toolCalls=tool_traces,
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

        for tool_call in tool_calls:
            fn = tool_call["function"]
            name = fn["name"]
            arguments = json.loads(fn.get("arguments") or "{}")
            result, nextgen_memory_reviewed, cli_memory_reviewed = await _execute_tool_with_memory_gate(
                db, name, arguments, appliance_name, nextgen_memory_reviewed, cli_memory_reviewed
            )
            tool_traces.append(ToolCallTrace(name=name, arguments=arguments, result=result))
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "content": result,
                }
            )
            retry_hint = build_tool_retry_hint(name, result, user_message)
            if retry_hint:
                messages.append({"role": "system", "content": retry_hint})

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
