from __future__ import annotations

import asyncio
import time
from typing import Any

from app.services.model_usage_service import extract_llm_usage_details

PROGRESS_SENTINEL = object()


class QueueChatProgressReporter:
    """Emits chat progress events into an asyncio queue for SSE streaming."""

    def __init__(self, queue: asyncio.Queue[Any | object]) -> None:
        self._queue = queue
        self._started_at = time.perf_counter()
        self._llm_round = 0
        self._last_tokens_per_sec: float | None = None

    def _elapsed_ms(self) -> int:
        return int((time.perf_counter() - self._started_at) * 1000)

    async def emit(self, event: dict[str, Any]) -> None:
        await self._queue.put(event)

    async def status(self, *, phase: str, label: str) -> None:
        await self.emit(
            {
                "type": "status",
                "phase": phase,
                "label": label,
                "elapsedMs": self._elapsed_ms(),
                "tokensPerSec": self._last_tokens_per_sec,
            }
        )

    async def llm_started(self) -> None:
        self._llm_round += 1
        await self.emit(
            {
                "type": "status",
                "phase": "thinking",
                "label": "Waiting for model…",
                "elapsedMs": self._elapsed_ms(),
                "round": self._llm_round,
                "tokensPerSec": self._last_tokens_per_sec,
            }
        )

    async def llm_finished(
        self,
        *,
        duration_ms: int,
        provider_type: str,
        data: dict[str, Any],
    ) -> None:
        details = extract_llm_usage_details(provider_type, data)
        output_tokens = int(details.get("output_tokens") or 0)
        total_tokens = details.get("total_tokens")
        tokens_per_sec: float | None = None
        if duration_ms > 0 and output_tokens > 0:
            tokens_per_sec = round(output_tokens / (duration_ms / 1000.0), 1)
            self._last_tokens_per_sec = tokens_per_sec

        label = f"{tokens_per_sec} tok/s" if tokens_per_sec is not None else "Model responded"
        await self.emit(
            {
                "type": "llm_stats",
                "phase": "thinking",
                "label": label,
                "elapsedMs": self._elapsed_ms(),
                "round": self._llm_round,
                "durationMs": duration_ms,
                "outputTokens": output_tokens,
                "totalTokens": total_tokens,
                "tokensPerSec": tokens_per_sec,
            }
        )

    async def tool_started(self, name: str) -> None:
        await self.emit(
            {
                "type": "status",
                "phase": "tools",
                "label": f"Running {name}…",
                "elapsedMs": self._elapsed_ms(),
                "tool": name,
                "tokensPerSec": self._last_tokens_per_sec,
            }
        )

    async def tool_finished(self, name: str) -> None:
        await self.emit(
            {
                "type": "status",
                "phase": "tools",
                "label": f"Finished {name}",
                "elapsedMs": self._elapsed_ms(),
                "tool": name,
                "tokensPerSec": self._last_tokens_per_sec,
            }
        )

    async def subtasks_updated(self, subtasks: list[dict[str, str]]) -> None:
        await self.emit(
            {
                "type": "subtasks",
                "subtasks": subtasks,
                "elapsedMs": self._elapsed_ms(),
            }
        )
