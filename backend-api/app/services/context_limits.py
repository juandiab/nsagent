"""Model-aware context budgeting — keep in sync with frontend modelContextWindows.js."""

from __future__ import annotations

from dataclasses import dataclass

MODEL_CONTEXT_PATTERNS: list[tuple[str, int]] = [
    (r"gpt-4\.1", 1_047_576),
    (r"gpt-4o-mini", 128_000),
    (r"gpt-4o", 128_000),
    (r"gpt-4-turbo", 128_000),
    (r"gpt-4", 8192),
    (r"gpt-3\.5", 16_385),
    (r"o1-mini", 128_000),
    (r"o1-preview|o1\b", 128_000),
    (r"o3-mini", 200_000),
    (r"claude-opus-4|claude-sonnet-4|claude-3-7", 200_000),
    (r"claude-3-5-sonnet|claude-3-5-haiku", 200_000),
    (r"claude-3-opus|claude-3-sonnet|claude-3-haiku", 200_000),
    (r"claude", 200_000),
    (r"gemini-2\.5|gemini-2\.0|gemini-1\.5-pro|gemini-1\.5-flash", 1_048_576),
    (r"gemini", 128_000),
    (r"grok-3|grok-2", 131_072),
    (r"grok", 131_072),
    (r"deepseek-reasoner|deepseek-r1", 64_000),
    (r"deepseek", 64_000),
    (r"llama-3\.3|llama-3\.2|llama-3\.1|llama3", 128_000),
    (r"qwen2\.5|qwen", 128_000),
    (r"mistral-large|mixtral|mistral", 128_000),
    (r"phi-3|phi-4", 128_000),
]

PROVIDER_DEFAULT_CONTEXT: dict[str, int] = {
    "OpenAI": 128_000,
    "Anthropic": 200_000,
    "Gemini": 1_048_576,
    "Grok": 131_072,
    "DeepSeek": 64_000,
    "OpenRouter": 128_000,
    "Azure OpenAI": 128_000,
    "AWS Bedrock": 200_000,
    "LM Studio": 32_768,
    "OpenAI-Compatible": 32_768,
}


@dataclass(frozen=True)
class ContextLimits:
    token_limit: int
    max_history_messages: int
    max_tool_result_chars: int
    system_prompt_overhead: int


def _normalize_model_name(name: str) -> str:
    return (name or "").strip().replace("models/", "", 1)


def resolve_context_token_limit(model: str, provider_type: str = "") -> int:
    import re

    normalized = _normalize_model_name(model)
    if normalized:
        for pattern, tokens in MODEL_CONTEXT_PATTERNS:
            if re.search(pattern, normalized, re.IGNORECASE):
                return tokens
    return PROVIDER_DEFAULT_CONTEXT.get(provider_type, 128_000)


def resolve_max_history_messages(context_token_limit: int) -> int:
    if context_token_limit >= 1_000_000:
        return 48
    if context_token_limit >= 512_000:
        return 36
    if context_token_limit >= 200_000:
        return 28
    if context_token_limit >= 128_000:
        return 20
    if context_token_limit >= 64_000:
        return 14
    if context_token_limit >= 32_768:
        return 10
    if context_token_limit >= 16_000:
        return 8
    return 6


def resolve_max_tool_result_chars(context_token_limit: int) -> int:
    if context_token_limit >= 512_000:
        return 16_000
    if context_token_limit >= 128_000:
        return 12_000
    if context_token_limit >= 64_000:
        return 8_000
    if context_token_limit >= 32_768:
        return 5_000
    return 3_000


def resolve_system_prompt_token_overhead(context_token_limit: int) -> int:
    if context_token_limit >= 128_000:
        return 4000
    if context_token_limit >= 32_768:
        return 3500
    return 3000


def resolve_context_limits(model: str, provider_type: str = "") -> ContextLimits:
    token_limit = resolve_context_token_limit(model, provider_type)
    return ContextLimits(
        token_limit=token_limit,
        max_history_messages=resolve_max_history_messages(token_limit),
        max_tool_result_chars=resolve_max_tool_result_chars(token_limit),
        system_prompt_overhead=resolve_system_prompt_token_overhead(token_limit),
    )
