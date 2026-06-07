from app.services.context_limits import (
    resolve_context_limits,
    resolve_context_token_limit,
    resolve_max_history_messages,
    resolve_max_tool_result_chars,
)


def test_resolve_context_token_limit_by_model():
    assert resolve_context_token_limit("gpt-4o", "OpenAI") == 128_000
    assert resolve_context_token_limit("gemini-2.5-pro", "Gemini") == 1_048_576
    assert resolve_context_token_limit("unknown-model", "LM Studio") == 32_768


def test_history_messages_scale_with_context():
    assert resolve_max_history_messages(32_768) == 10
    assert resolve_max_history_messages(128_000) == 20
    assert resolve_max_history_messages(200_000) == 28
    assert resolve_max_history_messages(1_048_576) == 48


def test_tool_result_chars_scale_with_context():
    assert resolve_max_tool_result_chars(16_000) == 3_000
    assert resolve_max_tool_result_chars(64_000) == 8_000
    assert resolve_max_tool_result_chars(128_000) == 12_000
    assert resolve_max_tool_result_chars(1_048_576) == 16_000


def test_resolve_context_limits_bundle():
    limits = resolve_context_limits("claude-sonnet-4-20250514", "Anthropic")
    assert limits.token_limit == 200_000
    assert limits.max_history_messages == 28
    assert limits.max_tool_result_chars == 12_000
