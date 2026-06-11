import json

from app.schemas.copilot import ToolCallTrace
from app.services.copilot_orchestration import (
    LONG_TASK_CONSENT_MESSAGE,
    OrchestrationRuntime,
    OrchestrationSettings,
    build_deployment_subtasks,
    build_orchestration_runtime,
    continuation_for_tool_limit,
    is_deployment_resume_message,
    should_offer_long_task_consent,
)


def test_user_confirmed_execution_detects_spanish_and_english():
    assert is_deployment_resume_message("Si, procede")
    assert is_deployment_resume_message("yes, go ahead") is False
    assert is_deployment_resume_message("continue")


def test_deployment_subtasks_reflect_progress():
    traces = [
        ToolCallTrace(name="search_netscaler_cli_reference", arguments={}, result="{}"),
    ]
    subtasks = build_deployment_subtasks(traces)
    assert subtasks[0].status == "completed"
    assert subtasks[1].status == "pending"


def test_long_task_consent_when_threshold_hit():
    runtime = OrchestrationRuntime(
        settings=OrchestrationSettings(long_task_threshold=3, prompt_before_long_tasks=True),
        tool_rounds=3,
    )
    assert should_offer_long_task_consent(
        runtime,
        role="operator",
        user_message="configure dns lb",
        tool_traces=[],
        deployment_incomplete=True,
        continuation_phase=0,
    )


def test_resume_message_auto_approves_runtime():
    runtime = build_orchestration_runtime(
        settings=OrchestrationSettings(),
        user_message="continue",
    )
    assert runtime.long_task_approved is True


def test_tool_limit_continuation_payload():
    traces = [
        ToolCallTrace(
            name="netscaler_run_cli_command",
            arguments={"command": "add service s1 1.1.1.1 DNS 53"},
            result=json.dumps({"success": True}),
        )
    ]
    continuation = continuation_for_tool_limit(traces, deployment_incomplete=True)
    assert continuation is not None
    assert continuation.required is True
    assert "continue" in continuation.message.lower()
    assert LONG_TASK_CONSENT_MESSAGE not in continuation.message
