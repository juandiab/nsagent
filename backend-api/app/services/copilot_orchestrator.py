import json
import logging
import re
import sys
import time
from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase
from starlette.requests import Request

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
from app.services.ai_provider_service import (
    lm_studio_endpoint_candidates,
    normalize_azure_resource_endpoint,
    OPENAI_COMPAT_CHAT_PROVIDER_TYPES,
    resolve_base_url,
    resolve_bedrock_openai_base,
)
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
    user_requests_design_implementation,
)
from app.services.model_usage_service import UsageAccumulator, flush_usage_accumulator, record_provider_usage
from app.services.copilot_memory_gate import (
    CLI_MEMORY_SEARCH_TOOL,
    CISCO_CLI_MEMORY_SEARCH_TOOL,
    F5_CLI_MEMORY_SEARCH_TOOL,
    MEMORY_SEARCH_TOOL,
    SDX_CLI_MEMORY_SEARCH_TOOL,
    apply_memory_review_gates,
    block_result_for_unconfirmed_destructive,
    destructive_confirmation_required,
)
from app.services.copilot_architect_discovery import (
    architect_discovery_should_retry,
    sanitize_architect_reply,
)
from app.services.copilot_retry import build_tool_retry_hint
from app.services.copilot_roles import (
    JPilotRole,
    build_system_prompt,
    normalize_role,
    role_requires_appliance,
)
from app.services.copilot_tool_router import route_copilot_tools
from app.services.copilot_vendors import copilot_vendor_is_supported
from app.services.vendor_registry import resolve_chat_vendor
from app.services.encryption_service import decrypt_value

from app.services.context_limits import ContextLimits, resolve_context_limits
from app.services.copilot_progress import QueueChatProgressReporter

MAX_TOOL_ITERATIONS = 20


class ChatCancelledError(Exception):
    """Raised when the client closes the connection before chat completes."""


async def raise_if_chat_cancelled(request: Request | None) -> None:
    if request is not None and await request.is_disconnected():
        raise ChatCancelledError()

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


def _architect_discovery_retry_nudge(
    content: str,
    user_message: str,
    role: str | None,
    vendor: str | None,
) -> str | None:
    return architect_discovery_should_retry(content, user_message, role, vendor)


def _should_force_tool_execution(
    user_message: str,
    tool_traces: list[ToolCallTrace],
    content: str,
    role: str | None = None,
) -> bool:
    if normalize_role(role) == JPilotRole.ARCHITECT:
        return False

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


def guard_fabricated_execution(
    content: str,
    tool_traces: list[ToolCallTrace],
    role: str | None = None,
) -> str:
    """Prepend a warning when the reply claims a config change that no tool actually performed."""
    if normalize_role(role) == JPilotRole.ARCHITECT:
        return content

    if _claims_config_change(content) and not _had_successful_action(tool_traces):
        logger.warning(
            "fabricated_execution_guard fired — response claims a config change but no "
            "write/exec tool ran successfully (toolCalls=%d)",
            len(tool_traces),
        )
        return f"{UNEXECUTED_ACTION_BANNER}\n\n---\n\n{content}"
    return content

def trim_chat_history(history: list[dict], max_messages: int) -> list[dict]:
    if max_messages <= 0 or len(history) <= max_messages:
        return history
    return history[-max_messages:]


def _truncate_tool_result(result: str, max_chars: int) -> str:
    if max_chars <= 0 or len(result) <= max_chars:
        return result
    return result[:max_chars] + "\n...[truncated for context]"


def _finalize_chat_response(
    content: str,
    *,
    provider_name: str,
    provider_type: str,
    model: str,
    tool_traces: list[ToolCallTrace],
    user_message: str = "",
    role: str | None = None,
) -> ChatResponse:
    if normalize_role(role) == JPilotRole.ARCHITECT:
        content = sanitize_architect_reply(content)
    cleaned, input_form = parse_input_form(content)
    cleaned, input_form = attach_default_lb_form_if_missing(
        user_message, cleaned, input_form, role=role
    )
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
    role: str | None = None,
    vendor: str | None = None,
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

    result = await execute_copilot_tool(
        db, name, arguments, default_appliance_name=appliance_name, role=role, vendor=vendor
    )
    logger.info("tool_call name=%s executed result=%s", name, (result or "")[:600])
    if name == MEMORY_SEARCH_TOOL:
        nextgen_memory_reviewed = True
    if name in {
        CLI_MEMORY_SEARCH_TOOL,
        CISCO_CLI_MEMORY_SEARCH_TOOL,
        SDX_CLI_MEMORY_SEARCH_TOOL,
        F5_CLI_MEMORY_SEARCH_TOOL,
    }:
        cli_memory_reviewed = True
    return result, nextgen_memory_reviewed, cli_memory_reviewed


async def resolve_appliance_vendor(db: AsyncIOMotorDatabase, appliance_name: str) -> str:
    if not appliance_name:
        return "netscaler"
    appliance = await db.appliances.find_one({"name": appliance_name})
    if appliance is None:
        return "netscaler"
    return str(appliance.get("vendor") or "netscaler")


async def get_default_provider(db: AsyncIOMotorDatabase, role: str | None = None) -> dict | None:
    from app.models.ai_provider import provider_supports_role

    providers = await db.aiProviders.find({"enabled": True}).sort("providerName", 1).to_list(length=None)
    if role:
        providers = [provider for provider in providers if provider_supports_role(provider, role)]
    if not providers:
        return None
    for provider in providers:
        if provider.get("isDefault"):
            return provider
    return providers[0]


async def resolve_chat_provider(
    db: AsyncIOMotorDatabase,
    provider_id: str | None,
    role: str | None = None,
) -> dict | None:
    """Pick the provider for this chat: explicit choice, else role-matched default."""
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
    return await get_default_provider(db, role=role)


async def run_copilot_chat(
    db: AsyncIOMotorDatabase,
    user_message: str,
    history: list[dict],
    attachments: list[ChatAttachment] | None = None,
    settings: CopilotSettings | None = None,
    appliance_name: str = "",
    provider_id: str | None = None,
    web_search: bool = True,
    role: str | None = None,
    request: Request | None = None,
    progress: QueueChatProgressReporter | None = None,
) -> ChatResponse:
    from app.services.copilot_service import set_web_search_allowed

    set_web_search_allowed(web_search)
    await raise_if_chat_cancelled(request)
    provider = await resolve_chat_provider(db, provider_id, role=role)
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

    chat_role = normalize_role(role)
    appliance_vendor = await resolve_appliance_vendor(db, appliance_name)
    chat_vendor = resolve_chat_vendor(
        appliance_vendor=appliance_vendor,
        role=chat_role.value,
        appliance_name=appliance_name,
    )
    tool_traces: list[ToolCallTrace] = []
    enabled_tools = await get_enabled_copilot_tools(
        db,
        role=chat_role.value,
        vendor=chat_vendor,
    )
    enabled_tools = route_copilot_tools(
        enabled_tools,
        role=chat_role.value,
        user_message=user_message,
        attachment_names=[a.name for a in attachment_list],
        vendor=chat_vendor,
    )
    enabled_tool_names = {tool["name"] for tool in enabled_tools}
    logger.info(
        "copilot_tools role=%s vendor=%s appliance_vendor=%s routed=%d names=%s",
        chat_role.value,
        chat_vendor,
        appliance_vendor,
        len(enabled_tools),
        sorted(enabled_tool_names),
    )
    if appliance_name and not copilot_vendor_is_supported(appliance_vendor) and chat_role != JPilotRole.ARCHITECT:
        raise ValueError(
            f"JPilot chat for Operator/Analyst is not yet available for vendor '{appliance_vendor}'. "
            "Connect a supported appliance or use Architect role for planning."
        )
    system_prompt = build_system_prompt(chat_role, appliance_name, vendor=chat_vendor)
    attachment_names = [a.name for a in attachment_list]
    if (
        chat_role == JPilotRole.OPERATOR
        and appliance_name
        and user_requests_design_implementation(user_message, attachment_names)
    ):
        from app.services.copilot_roles import operator_design_implementation_suffix

        system_prompt += "\n" + operator_design_implementation_suffix(appliance_name, vendor=chat_vendor)
    ctx_limits = resolve_context_limits(model, provider_type)
    history = trim_chat_history(history, ctx_limits.max_history_messages)

    if progress is not None:
        await progress.status(phase="preparing", label="Preparing request…")

    from app.services.copilot_port_check import try_auto_tcp_port_check

    auto_traces: list[ToolCallTrace] = []
    auto_response = None
    if appliance_name and role_requires_appliance(chat_role):
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
    provider_id_str = str(provider["_id"])
    usage_accumulator = UsageAccumulator()

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
            provider_type,
            provider_name,
            usage_accumulator,
            jpilot_role=chat_role.value,
            chat_vendor=chat_vendor,
            request=request,
            context_limits=ctx_limits,
            progress=progress,
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
            provider_type,
            provider_name,
            usage_accumulator,
            jpilot_role=chat_role.value,
            chat_vendor=chat_vendor,
            request=request,
            context_limits=ctx_limits,
            progress=progress,
        )
    elif provider_type in OPENAI_COMPAT_CHAT_PROVIDER_TYPES:
        if provider_type == "LM Studio":
            lm_base_urls = lm_studio_endpoint_candidates(endpoint.strip())
            base_url = lm_base_urls[0]
            base_url_candidates = lm_base_urls
        elif provider_type == "AWS Bedrock":
            base_url = resolve_bedrock_openai_base(endpoint.strip())
            base_url_candidates = None
        elif provider_type == "Azure OpenAI":
            base_url = normalize_azure_resource_endpoint(endpoint.strip())
            base_url_candidates = None
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
            usage_accumulator,
            jpilot_role=chat_role.value,
            chat_vendor=chat_vendor,
            request=request,
            endpoint=endpoint,
            context_limits=ctx_limits,
            progress=progress,
        )
    else:
        raise ValueError(f"Unsupported provider type: {provider_type}")

    await flush_usage_accumulator(db, provider_id_str, usage_accumulator)
    if usage_accumulator.requests == 0 and (content or "").strip():
        await record_provider_usage(db, provider_id=provider_id_str, tokens=0, requests=1)

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

    content = guard_fabricated_execution(content, tool_traces, role=chat_role.value)

    return _finalize_chat_response(
        content,
        provider_name=provider["providerName"],
        provider_type=provider_type,
        model=model,
        tool_traces=tool_traces,
        user_message=user_message,
        role=chat_role.value,
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
    usage_accumulator: UsageAccumulator | None = None,
    jpilot_role: str | None = None,
    chat_vendor: str | None = None,
    request: Request | None = None,
    endpoint: str = "",
    context_limits: ContextLimits | None = None,
    progress: QueueChatProgressReporter | None = None,
) -> str:
    limits = context_limits or resolve_context_limits(model, provider_type)
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
        await raise_if_chat_cancelled(request)
        if progress is not None:
            await progress.llm_started()
        llm_started_at = time.perf_counter()
        data, active_base_url = await chat_openai_compatible(
            base_url=active_base_url,
            api_key=api_key,
            model=model,
            messages=messages,
            tools=tools,
            base_url_candidates=fallback_candidates,
            provider_type=provider_type,
            provider_name=provider_name,
            endpoint=endpoint,
        )
        if progress is not None:
            await progress.llm_finished(
                duration_ms=int((time.perf_counter() - llm_started_at) * 1000),
                provider_type=provider_type,
                data=data,
            )
        fallback_candidates = None
        if usage_accumulator is not None:
            usage_accumulator.add_llm_response(provider_type, data)
        choice = data["choices"][0]["message"]
        tool_calls = choice.get("tool_calls") or []

        if not tool_calls:
            content = sanitize_architect_reply(choice.get("content") or "")
            architect_nudge = _architect_discovery_retry_nudge(
                content, user_message, jpilot_role, chat_vendor
            )
            if architect_nudge:
                logger.warning("architect_discovery_nudge — checklist or missing jpilot-form")
                if content.strip():
                    messages.append({"role": "assistant", "content": content})
                messages.append({"role": "system", "content": architect_nudge})
                continue
            if _should_force_tool_execution(user_message, tool_traces, content, role=jpilot_role):
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
                if progress is not None:
                    await progress.tool_started(name)
                result, nextgen_memory_reviewed, cli_memory_reviewed = await _execute_tool_with_memory_gate(
                    db,
                    name,
                    arguments,
                    appliance_name,
                    nextgen_memory_reviewed,
                    cli_memory_reviewed,
                    role=jpilot_role,
                    vendor=chat_vendor,
                )
                if progress is not None:
                    await progress.tool_finished(name)
            except Exception as exc:
                logger.exception("tool_call name=%s failed", name)
                result = json.dumps({"success": False, "errorMessage": str(exc)})

            tool_traces.append(ToolCallTrace(name=name, arguments=arguments, result=result))
            tool_call_id = tool_call.get("id") or f"call_{len(tool_traces)}"
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call_id,
                    "content": _truncate_tool_result(result, limits.max_tool_result_chars),
                }
            )
            retry_hint = build_tool_retry_hint(
                name, result, user_message, [a.name for a in attachments]
            )
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
    provider_type: str = "Gemini",
    provider_name: str = "",
    usage_accumulator: UsageAccumulator | None = None,
    jpilot_role: str | None = None,
    chat_vendor: str | None = None,
    request: Request | None = None,
    context_limits: ContextLimits | None = None,
    progress: QueueChatProgressReporter | None = None,
) -> str:
    limits = context_limits or resolve_context_limits(model, provider_type)
    contents: list[dict[str, Any]] = []
    for item in history:
        gemini_role = "model" if item["role"] == "assistant" else "user"
        contents.append({"role": gemini_role, "parts": [{"text": item["content"]}]})
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
        await raise_if_chat_cancelled(request)
        if progress is not None:
            await progress.llm_started()
        llm_started_at = time.perf_counter()
        data = await chat_gemini(
            api_key=api_key,
            model=model,
            system=system_prompt,
            contents=contents,
            tools=tools,
            provider_name=provider_name,
        )
        if progress is not None:
            await progress.llm_finished(
                duration_ms=int((time.perf_counter() - llm_started_at) * 1000),
                provider_type=provider_type,
                data=data,
            )
        if usage_accumulator is not None:
            usage_accumulator.add_llm_response(provider_type, data)

        candidate = (data.get("candidates") or [{}])[0]
        content = candidate.get("content", {})
        parts = content.get("parts", [])

        function_calls = [part["functionCall"] for part in parts if part.get("functionCall")]
        text_parts = [part.get("text", "") for part in parts if part.get("text")]

        if not function_calls:
            content = sanitize_architect_reply("\n".join(text_parts).strip())
            architect_nudge = _architect_discovery_retry_nudge(
                content, user_message, jpilot_role, chat_vendor
            )
            if architect_nudge:
                logger.warning("architect_discovery_nudge — checklist or missing jpilot-form")
                if content:
                    contents.append({"role": "model", "parts": [{"text": content}]})
                contents.append({"role": "user", "parts": [{"text": architect_nudge}]})
                continue
            if _should_force_tool_execution(user_message, tool_traces, content, role=jpilot_role):
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
            if progress is not None:
                await progress.tool_started(name)
            result, nextgen_memory_reviewed, cli_memory_reviewed = await _execute_tool_with_memory_gate(
                db,
                name,
                arguments,
                appliance_name,
                nextgen_memory_reviewed,
                cli_memory_reviewed,
                role=jpilot_role,
                vendor=chat_vendor,
            )
            if progress is not None:
                await progress.tool_finished(name)
            tool_traces.append(ToolCallTrace(name=name, arguments=arguments, result=result))
            truncated = _truncate_tool_result(result, limits.max_tool_result_chars)
            response_parts.append(
                {
                    "functionResponse": {
                        "name": name,
                        "response": {"result": truncated},
                    }
                }
            )
            retry_hint = build_tool_retry_hint(
                name, result, user_message, [a.name for a in attachments]
            )
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
    provider_type: str = "Anthropic",
    provider_name: str = "",
    usage_accumulator: UsageAccumulator | None = None,
    jpilot_role: str | None = None,
    chat_vendor: str | None = None,
    request: Request | None = None,
    context_limits: ContextLimits | None = None,
    progress: QueueChatProgressReporter | None = None,
) -> str:
    limits = context_limits or resolve_context_limits(model, provider_type)
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
        await raise_if_chat_cancelled(request)
        if progress is not None:
            await progress.llm_started()
        llm_started_at = time.perf_counter()
        data = await chat_anthropic(
            api_key=api_key,
            model=model,
            system=system_prompt,
            messages=messages,
            tools=tools,
            provider_name=provider_name,
        )
        if progress is not None:
            await progress.llm_finished(
                duration_ms=int((time.perf_counter() - llm_started_at) * 1000),
                provider_type=provider_type,
                data=data,
            )
        if usage_accumulator is not None:
            usage_accumulator.add_llm_response(provider_type, data)

        content_blocks = data.get("content", [])
        tool_uses = [block for block in content_blocks if block.get("type") == "tool_use"]
        text_blocks = [block.get("text", "") for block in content_blocks if block.get("type") == "text"]
        stop_reason = data.get("stop_reason")

        if stop_reason != "tool_use" and not tool_uses:
            content = sanitize_architect_reply("\n".join(text_blocks).strip())
            architect_nudge = _architect_discovery_retry_nudge(
                content, user_message, jpilot_role, chat_vendor
            )
            if architect_nudge:
                logger.warning("architect_discovery_nudge — checklist or missing jpilot-form")
                if content:
                    messages.append({"role": "assistant", "content": content})
                messages.append({"role": "user", "content": [{"type": "text", "text": architect_nudge}]})
                continue
            if _should_force_tool_execution(user_message, tool_traces, content, role=jpilot_role):
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
            if progress is not None:
                await progress.tool_started(name)
            result, nextgen_memory_reviewed, cli_memory_reviewed = await _execute_tool_with_memory_gate(
                db,
                name,
                arguments,
                appliance_name,
                nextgen_memory_reviewed,
                cli_memory_reviewed,
                role=jpilot_role,
                vendor=chat_vendor,
            )
            if progress is not None:
                await progress.tool_finished(name)
            tool_traces.append(ToolCallTrace(name=name, arguments=arguments, result=result))
            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": tool_use["id"],
                    "content": _truncate_tool_result(result, limits.max_tool_result_chars),
                }
            )
            retry_hint = build_tool_retry_hint(
                name, result, user_message, [a.name for a in attachments]
            )
            if retry_hint:
                tool_results.append({"type": "text", "text": retry_hint})

        messages.append({"role": "user", "content": tool_results})

    return "I reached the maximum number of tool calls. Please try a simpler request."
