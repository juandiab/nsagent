from __future__ import annotations

import re
from typing import Any

_SECRET_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"(?i)(password|passwd|secret|api[_-]?key|token|license[_-]?code)\s*[:=]\s*\S+"), r"\1: [REDACTED]"),
    (re.compile(r"-----BEGIN [A-Z ]+-----[\s\S]*?-----END [A-Z ]+-----"), "[REDACTED PEM BLOCK]"),
    (re.compile(r"(?i)Bearer\s+[A-Za-z0-9\-._~+/]+=*"), "Bearer [REDACTED]"),
]

_IPV4_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")


def redact_text(text: str, *, mask_ips: bool = False) -> str:
    if not text:
        return text
    redacted = text
    for pattern, replacement in _SECRET_PATTERNS:
        redacted = pattern.sub(replacement, redacted)
    if mask_ips:
        redacted = _IPV4_RE.sub("[IP]", redacted)
    return redacted


def redact_tool_arguments(arguments: Any, *, mask_ips: bool = False) -> dict[str, Any]:
    if not isinstance(arguments, dict):
        return {}
    cleaned: dict[str, Any] = {}
    for key, value in arguments.items():
        lowered = str(key).lower()
        if any(term in lowered for term in ("password", "secret", "token", "key", "credential")):
            cleaned[key] = "[REDACTED]"
        elif isinstance(value, str):
            cleaned[key] = redact_text(value, mask_ips=mask_ips)
        else:
            cleaned[key] = value
    return cleaned


def truncate_text(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3].rstrip() + "..."


def redact_session_messages(
    messages: list[dict[str, Any]],
    *,
    max_messages: int = 40,
    max_content_chars: int = 4000,
    max_tool_result_chars: int = 800,
    mask_ips: bool = False,
) -> list[dict[str, Any]]:
    excerpt = messages[-max_messages:] if len(messages) > max_messages else messages
    cleaned: list[dict[str, Any]] = []
    for item in excerpt:
        if not isinstance(item, dict):
            continue
        content = redact_text(str(item.get("content") or ""), mask_ips=mask_ips)
        content = truncate_text(content, max_content_chars)
        entry: dict[str, Any] = {
            "role": str(item.get("role") or "user"),
            "content": content,
        }
        if item.get("createdAt"):
            entry["createdAt"] = item["createdAt"]
        if item.get("isError"):
            entry["isError"] = True
        tool_calls = item.get("toolCalls") or []
        if tool_calls:
            entry["toolCalls"] = []
            for trace in tool_calls[:12]:
                if not isinstance(trace, dict):
                    continue
                result = trace.get("result") or trace.get("resultExcerpt") or ""
                entry["toolCalls"].append(
                    {
                        "name": str(trace.get("name") or ""),
                        "arguments": redact_tool_arguments(trace.get("arguments") or {}, mask_ips=mask_ips),
                        "resultExcerpt": truncate_text(
                            redact_text(str(result), mask_ips=mask_ips),
                            max_tool_result_chars,
                        ),
                    }
                )
        cleaned.append(entry)
    return cleaned
