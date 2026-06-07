import pytest

from app.services.copilot_progress import QueueChatProgressReporter


@pytest.mark.asyncio
async def test_progress_reporter_emits_llm_stats():
    queue = __import__("asyncio").Queue()
    reporter = QueueChatProgressReporter(queue)

    await reporter.llm_started()
    status = await queue.get()
    assert status["type"] == "status"
    assert status["phase"] == "thinking"
    assert status["round"] == 1

    await reporter.llm_finished(
        duration_ms=2000,
        provider_type="OpenAI",
        data={"usage": {"prompt_tokens": 10, "completion_tokens": 40, "total_tokens": 50}},
    )
    stats = await queue.get()
    assert stats["type"] == "llm_stats"
    assert stats["outputTokens"] == 40
    assert stats["tokensPerSec"] == 20.0
