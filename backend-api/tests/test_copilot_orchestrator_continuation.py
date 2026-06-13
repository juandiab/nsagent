import json

from app.schemas.copilot import ToolCallTrace
from app.services.copilot_orchestration import (
    LONG_TASK_CONSENT_MESSAGE,
    OrchestrationRuntime,
    OrchestrationSettings,
    build_deployment_subtasks,
    build_progress_subtasks,
    build_orchestration_runtime,
    cli_commands_are_read_only,
    continuation_for_tool_limit,
    is_deployment_resume_message,
    should_offer_long_task_consent,
    trace_is_state_changing,
)
from app.services.copilot_orchestrator import _deployment_may_be_incomplete


def test_user_confirmed_execution_detects_spanish_and_english():
    assert is_deployment_resume_message("Si, procede")
    assert is_deployment_resume_message("yes, go ahead") is False
    assert is_deployment_resume_message("continue")


def test_deployment_subtasks_reflect_progress():
    traces = [
        ToolCallTrace(name="search_netscaler_cli_reference", arguments={}, result="{}"),
    ]
    subtasks = build_deployment_subtasks(
        traces,
        user_message="implement this design",
        attachment_names=["jpilot-design-2026-06-04.md"],
    )
    assert subtasks[0].label == "Review documentation"
    assert subtasks[0].status == "completed"
    assert subtasks[1].status == "pending"


def test_operation_subtasks_use_review_request():
    traces = [
        ToolCallTrace(name="netscaler_nextgen_request", arguments={}, result="{}"),
    ]
    bundle = build_progress_subtasks(
        traces,
        role="operator",
        user_message="remove all VIPs",
    )
    assert bundle.title == "Operation progress"
    assert bundle.subtasks[0].label == "Review request"
    assert bundle.subtasks[0].status == "completed"


def test_design_handoff_uses_documentation_review():
    traces = []
    conversation = "<!-- jpilot-design-document -->\n# Design\nHandoff for Operator"
    bundle = build_progress_subtasks(
        traces,
        role="operator",
        user_message="yes",
        conversation_text=conversation,
    )
    assert bundle.title == "Deployment progress"
    assert bundle.subtasks[0].label == "Review documentation"


def test_architect_change_control_progress_labels():
    traces = [
        ToolCallTrace(name="search_jpilot_architect_resources", arguments={}, result="{}"),
    ]
    conversation = "Planning inputs for: What are you planning?\n- Planning intent: change_control"
    bundle = build_progress_subtasks(
        traces,
        role="architect",
        conversation_text=conversation,
    )
    assert bundle.title == "Change control preparation in progress"
    assert bundle.subtasks[0].label == "Document change scope & justification"
    assert bundle.subtasks[2].label == "Prepare change control record"


def test_architect_deliverable_marks_all_steps_complete():
    traces = [
        ToolCallTrace(name="search_jpilot_architect_resources", arguments={}, result="{}"),
    ]
    bundle = build_progress_subtasks(
        traces,
        role="architect",
        conversation_text="- Planning intent: new_deployment",
        deliverable_ready=True,
    )
    assert bundle.title == "Solution design in progress"
    assert all(task.status == "completed" for task in bundle.subtasks)


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
    continuation = continuation_for_tool_limit(
        traces,
        deployment_incomplete=True,
        role="operator",
        user_message="remove all VIPs",
    )
    assert continuation is not None
    assert continuation.required is True
    assert "continue" in continuation.message.lower()
    assert continuation.subtasks[0].label == "Review request"
    assert LONG_TASK_CONSENT_MESSAGE not in continuation.message


def test_show_route_is_read_only_cli():
    assert cli_commands_are_read_only("show route")
    assert not cli_commands_are_read_only("rm vserver web")


def test_show_route_trace_is_not_state_changing():
    trace = ToolCallTrace(
        name="netscaler_run_cli_command",
        arguments={"command": "show route", "purpose": "routes"},
        result=json.dumps({"success": True, "output": "0.0.0.0/0"}),
    )
    assert not trace_is_state_changing(trace)


def test_bare_yes_after_read_only_does_not_continue_deployment():
    traces = [
        ToolCallTrace(
            name="netscaler_run_cli_command",
            arguments={"command": "show route", "purpose": "routes"},
            result=json.dumps({"success": True, "output": "0.0.0.0/0"}),
        )
    ]
    assert _deployment_may_be_incomplete(traces, "yes", "operator") is False


def test_read_only_operation_progress_single_step():
    traces = [
        ToolCallTrace(name="netscaler_run_diagnostic", arguments={}, result="{}"),
    ]
    bundle = build_progress_subtasks(
        traces,
        role="operator",
        user_message="does the netscaler have internet access?",
    )
    assert bundle.title == "Operation progress"
    assert len(bundle.subtasks) == 1
    assert bundle.subtasks[0].label == "Review request"


def test_nextgen_create_marks_all_deployment_steps_complete():
    traces = [
        ToolCallTrace(
            name="netscaler_create_application",
            arguments={"name": "iis_lb_app"},
            result=json.dumps({"success": True, "application": {"name": "iis_lb_app"}}),
        )
    ]
    bundle = build_progress_subtasks(
        traces,
        role="operator",
        user_message="Configuration inputs for: Create IIS Load Balancer\n- Application Name: iis",
    )
    assert bundle.subtasks[1].status == "completed"
    assert bundle.subtasks[2].status == "completed"
