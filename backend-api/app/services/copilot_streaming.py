from __future__ import annotations

import asyncio
import json
from typing import Any, AsyncIterator

import httpx
from motor.motor_asyncio import AsyncIOMotorDatabase
from starlette.requests import Request

from app.schemas.copilot import ChatRequest, ChatResponse, CopilotSettings
from app.services.ai_provider_errors import (
    AiProviderError,
    build_gateway_timeout_detail,
    enrich_ai_provider_error,
    maybe_parse_ai_provider_error,
)
from app.services.copilot_orchestrator import ChatCancelledError, resolve_chat_provider, run_copilot_chat
from app.services.copilot_progress import PROGRESS_SENTINEL, QueueChatProgressReporter
from app.services.copilot_roles import normalize_role, role_requires_appliance

DEFAULT_SETTINGS = CopilotSettings()


def _sse_payload(event: dict[str, Any]) -> str:
    return f"data: {json.dumps(event, default=str)}\n\n"


async def stream_copilot_chat_events(
    *,
    db: AsyncIOMotorDatabase,
    payload: ChatRequest,
    request: Request,
) -> AsyncIterator[str]:
    settings = payload.settings or DEFAULT_SETTINGS
    chat_role = normalize_role(payload.role)
    appliance_name = (payload.applianceName or "").strip()
    provider = await resolve_chat_provider(db, payload.providerId, role=chat_role.value)
    queue: asyncio.Queue[Any | object] = asyncio.Queue()
    reporter = QueueChatProgressReporter(queue)
    result_holder: dict[str, ChatResponse] = {}
    error_holder: dict[str, Exception] = {}

    async def run_chat() -> None:
        try:
            history = [item.model_dump() for item in payload.history]
            result_holder["response"] = await run_copilot_chat(
                db,
                payload.message.strip(),
                history,
                attachments=payload.attachments,
                settings=settings,
                appliance_name=appliance_name,
                provider_id=payload.providerId,
                web_search=payload.webSearch,
                role=chat_role.value,
                request=request,
                progress=reporter,
            )
        except Exception as exc:
            error_holder["error"] = exc
        finally:
            await queue.put(PROGRESS_SENTINEL)

    task = asyncio.create_task(run_chat())
    await reporter.status(phase="starting", label="Starting…")

    try:
        while True:
            item = await queue.get()
            if item is PROGRESS_SENTINEL:
                break
            yield _sse_payload(item)

        await task

        if "error" in error_holder:
            exc = error_holder["error"]
            if isinstance(exc, ChatCancelledError):
                yield _sse_payload({"type": "error", "status": 499, "detail": "Chat request cancelled"})
                return
            if isinstance(exc, AiProviderError):
                if provider and not exc.provider_name:
                    exc.provider_name = provider.get("providerName", "")
                detail = await enrich_ai_provider_error(db, exc, payload.providerId)
                yield _sse_payload({"type": "error", "status": 429, "detail": detail})
                return
            if isinstance(exc, ValueError):
                yield _sse_payload({"type": "error", "status": 400, "detail": str(exc)})
                return
            if isinstance(exc, httpx.TimeoutException):
                yield _sse_payload({"type": "error", "status": 504, "detail": build_gateway_timeout_detail()})
                return
            provider_type = provider.get("providerType", "") if provider else ""
            model = provider.get("model", "") if provider else ""
            provider_name = provider.get("providerName", "") if provider else ""
            parsed = maybe_parse_ai_provider_error(
                str(exc),
                provider_type=provider_type,
                model=model,
                provider_name=provider_name,
            )
            if parsed is not None:
                detail = await enrich_ai_provider_error(db, parsed, payload.providerId)
                yield _sse_payload({"type": "error", "status": 429, "detail": detail})
                return
            yield _sse_payload({"type": "error", "status": 502, "detail": f"Copilot request failed: {exc}"})
            return

        response = result_holder["response"]
        yield _sse_payload({"type": "done", "response": response.model_dump(mode="json")})
    finally:
        if not task.done():
            task.cancel()
