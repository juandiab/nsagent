"""Translate AI provider HTTP/API failures into actionable user messages."""

from __future__ import annotations

import json
import re
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from motor.motor_asyncio import AsyncIOMotorDatabase


class AiProviderError(ValueError):
    """Raised when an AI provider rejects a request due to quota, billing, auth, or limits."""

    def __init__(
        self,
        message: str,
        *,
        kind: str,
        provider_type: str,
        model: str,
        provider_name: str = "",
        status_code: int | None = None,
        raw_error: str = "",
    ) -> None:
        super().__init__(message)
        self.kind = kind
        self.provider_type = provider_type
        self.model = model
        self.provider_name = provider_name
        self.status_code = status_code
        self.raw_error = raw_error


_QUOTA_HINTS = (
    "quota exceeded",
    "exceeded your current quota",
    "insufficient_quota",
    "resource_exhausted",
    "billing hard limit",
    "billing_hard_limit",
    "credit balance is too low",
    "you exceeded your current quota",
    "spending limit",
    "payment required",
    "purchase credits",
    "free_tier",
    "free tier",
    "generativelanguage.googleapis.com/generate_content",
)

_RATE_LIMIT_HINTS = (
    "rate limit",
    "rate_limit",
    "too many requests",
    "requests per day",
    "retry in",
    "retry-after",
)

_BILLING_HINTS = (
    "billing",
    "payment",
    "subscription",
    "purchase",
    "add credits",
    "top up",
)

_AUTH_HINTS = (
    "invalid api key",
    "incorrect api key",
    "authentication failed",
    "authentication_error",
    "invalid_api_key",
    "unauthorized",
    "permission denied",
    "access denied",
    "invalid x-api-key",
)


def _extract_error_payload(body: str) -> tuple[dict[str, Any] | None, str]:
    text = (body or "").strip()
    if not text:
        return None, ""

    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return None, text.lower()

    if isinstance(payload, dict):
        nested = payload.get("error")
        if isinstance(nested, dict):
            message = str(nested.get("message") or nested.get("msg") or "").strip()
            code = str(nested.get("code") or nested.get("type") or nested.get("status") or "").strip()
            combined = " ".join(part for part in (message, code, json.dumps(nested)) if part).lower()
            return nested, combined
        message = str(payload.get("message") or payload.get("detail") or "").strip()
        return payload, message.lower()

    return None, text.lower()


def _classify_error_text(status_code: int | None, combined: str) -> str | None:
    if status_code in {401, 403} or any(hint in combined for hint in _AUTH_HINTS):
        return "auth"

    if status_code == 402 or any(hint in combined for hint in _BILLING_HINTS):
        if any(hint in combined for hint in _QUOTA_HINTS + _RATE_LIMIT_HINTS):
            return "quota"
        return "billing"

    if status_code == 429 or any(hint in combined for hint in _QUOTA_HINTS):
        return "quota"

    if any(hint in combined for hint in _RATE_LIMIT_HINTS):
        return "rate_limit"

    return None


def _provider_label(provider_type: str, provider_name: str, model: str) -> str:
    name = provider_name.strip() or provider_type.strip() or "AI provider"
    model_part = f" (`{model}`)" if model else ""
    return f"**{name}**{model_part}"


def build_gateway_timeout_detail() -> str:
    """User-facing message when nginx, the backend, or the provider times out."""
    lines = [
        "JPilot did not finish in time (gateway or upstream timeout).",
        "",
        "The proxy or AI provider stopped waiting while your request was running. "
        "Architect discovery with tools can take several minutes.",
        "",
        "**What you can do:**",
        "1. **Retry** — your message is already in the chat thread.",
        "2. Start a **new chat** if the thread is long (shorter context is faster).",
        "3. Use a faster **Model**, or turn off **Web** search for this turn.",
    ]
    return "\n".join(lines)


def build_context_limit_detail() -> str:
    """User-facing message when the model rejects an oversized prompt."""
    lines = [
        "The selected model ran out of context or token budget for this request.",
        "",
        "**What you can do:**",
        "1. Start a **new chat** and paste your latest planning inputs to continue discovery.",
        "2. Switch to a model with a larger context window under **AI Providers**.",
        "3. Open **Settings → Usage** to review monthly token limits and remaining quota.",
    ]
    return "\n".join(lines)


def _build_user_message(
    *,
    kind: str,
    provider_type: str,
    model: str,
    provider_name: str,
    alternate_providers: list[str] | None = None,
) -> str:
    label = _provider_label(provider_type, provider_name, model)

    if kind == "auth":
        lead = f"{label} rejected the API key or credentials."
        actions = [
            "Verify the API key under **AI Providers** and save the provider again.",
            "Switch to another provider using the **Model** dropdown in JPilot if one is configured.",
        ]
    elif kind == "billing":
        lead = f"{label} cannot run because billing or credits are unavailable for this account."
        actions = [
            "Add credits, fix billing, or upgrade the plan with your provider, then retry.",
            "Switch to another provider using the **Model** dropdown, or configure one under **AI Providers**.",
        ]
    elif kind == "rate_limit":
        lead = f"{label} hit a temporary rate limit."
        actions = [
            "Wait a minute and try again, or switch to another provider in the **Model** dropdown.",
            "If this keeps happening, reduce chat frequency or upgrade the provider plan.",
        ]
    else:
        lead = f"{label} cannot complete this request because the API quota or credits are exhausted."
        actions = [
            "Switch to another provider using the **Model** dropdown in JPilot.",
            "Open **AI Providers** to configure another model, or add credits / billing with the current provider.",
            "On free tiers, limits often reset daily — wait and retry, or use a paid key.",
        ]

    lines = [lead, "", "**What you can do:**"]
    for index, action in enumerate(actions, start=1):
        lines.append(f"{index}. {action}")

    alternates = [name for name in (alternate_providers or []) if name.strip()]
    if alternates:
        lines.extend(["", f"Other enabled providers: {', '.join(alternates)}."])
    else:
        lines.extend(["", "No other enabled providers were found — add one under **AI Providers**."])

    return "\n".join(lines)


def parse_ai_provider_error(
    body: str,
    *,
    status_code: int | None = None,
    provider_type: str = "",
    model: str = "",
    provider_name: str = "",
) -> AiProviderError | None:
    """Return AiProviderError when the response looks like quota/billing/auth/rate-limit failure."""
    _payload, combined = _extract_error_payload(body)
    kind = _classify_error_text(status_code, combined)
    if kind is None and status_code not in {401, 402, 403, 429}:
        return None
    if kind is None:
        kind = "quota" if status_code == 429 else "auth" if status_code in {401, 403} else "billing"

    message = _build_user_message(
        kind=kind,
        provider_type=provider_type,
        model=model,
        provider_name=provider_name,
    )
    return AiProviderError(
        message,
        kind=kind,
        provider_type=provider_type,
        model=model,
        provider_name=provider_name,
        status_code=status_code,
        raw_error=body,
    )


_CONTEXT_LIMIT_HINTS = (
    "context length",
    "context window",
    "maximum context",
    "max_tokens",
    "token limit",
    "too many tokens",
    "prompt is too long",
    "input is too long",
    "request too large",
)


def maybe_parse_context_limit_error(
    error_text: str,
    *,
    provider_type: str = "",
    model: str = "",
    provider_name: str = "",
) -> AiProviderError | None:
    combined = (error_text or "").strip().lower()
    if not combined or not any(hint in combined for hint in _CONTEXT_LIMIT_HINTS):
        return None
    return AiProviderError(
        build_context_limit_detail(),
        kind="quota",
        provider_type=provider_type,
        model=model,
        provider_name=provider_name,
        raw_error=error_text,
    )


def maybe_parse_ai_provider_error(
    error_text: str,
    *,
    provider_type: str = "",
    model: str = "",
    provider_name: str = "",
) -> AiProviderError | None:
    """Best-effort parse for errors that were wrapped as plain strings."""
    text = (error_text or "").strip()
    if not text:
        return None

    context_limit = maybe_parse_context_limit_error(
        text,
        provider_type=provider_type,
        model=model,
        provider_name=provider_name,
    )
    if context_limit is not None:
        return context_limit

    status_code = None
    status_match = re.search(r"\bHTTP\s+(\d{3})\b", text, flags=re.IGNORECASE)
    if status_match:
        status_code = int(status_match.group(1))
    elif '"code": 429' in text or '"status": "RESOURCE_EXHAUSTED"' in text:
        status_code = 429

    return parse_ai_provider_error(
        text,
        status_code=status_code,
        provider_type=provider_type,
        model=model,
        provider_name=provider_name,
    )


def raise_for_ai_provider_response(
    response,
    *,
    provider_type: str,
    model: str,
    provider_name: str = "",
) -> None:
    """Raise AiProviderError for known provider failures, otherwise ValueError with body text."""
    body = response.text or ""
    parsed = parse_ai_provider_error(
        body,
        status_code=response.status_code,
        provider_type=provider_type,
        model=model,
        provider_name=provider_name,
    )
    if parsed is not None:
        raise parsed
    if response.status_code >= 400:
        raise ValueError(body or f"HTTP {response.status_code}")


async def enrich_ai_provider_error(
    db: "AsyncIOMotorDatabase",
    exc: AiProviderError,
    current_provider_id: str | None = None,
) -> str:
    """Attach alternate enabled providers to the user-facing message."""
    query: dict[str, Any] = {"enabled": True}
    providers = await db.aiProviders.find(query).sort("providerName", 1).to_list(length=None)

    current_name = exc.provider_name.strip()
    alternates: list[str] = []
    for doc in providers:
        name = str(doc.get("providerName") or doc.get("providerType") or "").strip()
        if not name:
            continue
        doc_id = str(doc.get("_id", ""))
        if current_provider_id and doc_id == current_provider_id:
            current_name = current_name or name
            continue
        if current_name and name == current_name:
            continue
        model = str(doc.get("model") or "").strip()
        alternates.append(f"{name} ({model})" if model else name)

    return _build_user_message(
        kind=exc.kind,
        provider_type=exc.provider_type,
        model=exc.model,
        provider_name=current_name or exc.provider_name,
        alternate_providers=alternates,
    )
