"""Agent orchestration: tool limits, deployment subtasks, and long-task consent."""

from __future__ import annotations

from dataclasses import dataclass

from app.schemas.copilot import DeploymentContinuation, DeploymentSubtask, ToolCallTrace
from app.services.copilot_architect_discovery import extract_planning_intent
from app.services.copilot_form import (
    is_design_implementation_form_submission,
    user_requests_design_implementation,
)
from app.services.copilot_roles import JPilotRole, normalize_role

DEFAULT_MAX_TOOL_ITERATIONS = 20
DEFAULT_MAX_TOOL_CONTINUATION_PHASES = 3
DEFAULT_LONG_TASK_TOOL_THRESHOLD = 8

READ_ONLY_OPERATOR_TOOLS = frozenset(
    {
        "netscaler_get_system_info",
        "netscaler_test_connection",
        "netscaler_list_applications",
        "netscaler_list_virtual_servers",
        "netscaler_list_virtual_ips",
        "netscaler_list_ip_addresses",
        "netscaler_nextgen_get",
        "netscaler_run_diagnostic",
        "netscaler_telnet",
        "netscaler_collect_nsconmsg",
        "jpilot_check_doc_connectivity",
    }
)

_READ_ONLY_CLI_PREFIXES = ("show ", "stat ", "get ", "display ")

MEMORY_SEARCH_TOOLS = frozenset(
    {
        "search_netscaler_cli_reference",
        "search_netscaler_nextgen_api",
        "search_cisco_cli_reference",
        "search_sdx_cli_reference",
        "search_f5_tmsh_reference",
    }
)

ARCHITECT_REFERENCE_TOOLS = MEMORY_SEARCH_TOOLS | frozenset(
    {
        "search_jpilot_architect_resources",
        "search_f5_documentation",
        "jpilot_check_doc_connectivity",
        "netscaler_list_inventory",
    }
)

WRITE_EXEC_TOOL_NAMES = frozenset(
    {
        "netscaler_create_application",
        "netscaler_add_ip_address",
        "netscaler_run_cli_command",
        "netscaler_run_cli_commands",
        "netscaler_nextgen_request",
        "cisco_run_cli_command",
        "cisco_run_cli_commands",
        "sdx_run_cli_command",
        "sdx_run_cli_commands",
        "f5_run_tmsh_command",
        "f5_run_tmsh_commands",
    }
)


def cli_commands_are_read_only(commands: str | list[str]) -> bool:
    items = [commands] if isinstance(commands, str) else list(commands)
    normalized = [str(command).strip().lower() for command in items if str(command).strip()]
    if not normalized:
        return True
    return all(command.startswith(_READ_ONLY_CLI_PREFIXES) for command in normalized)


def trace_is_state_changing(trace: ToolCallTrace) -> bool:
    name = trace.name
    arguments = trace.arguments or {}
    if name in READ_ONLY_OPERATOR_TOOLS:
        return False
    if name == "netscaler_run_cli_command":
        return not cli_commands_are_read_only(str(arguments.get("command", "")))
    if name == "netscaler_run_cli_commands":
        return not cli_commands_are_read_only(arguments.get("commands") or [])
    if name == "netscaler_nextgen_request":
        return str(arguments.get("method", "GET")).upper() != "GET"
    return name in WRITE_EXEC_TOOL_NAMES


def trace_executed_successfully(trace: ToolCallTrace) -> bool:
    import json

    if trace.name not in WRITE_EXEC_TOOL_NAMES and trace.name not in READ_ONLY_OPERATOR_TOOLS:
        if trace.name not in {"netscaler_run_cli_command", "netscaler_run_cli_commands"}:
            return False
    try:
        payload = json.loads(trace.result)
    except (json.JSONDecodeError, TypeError):
        return True
    if not isinstance(payload, dict):
        return True
    if payload.get("blocked") or payload.get("needsConfirmation") or payload.get("success") is False:
        return False
    if trace.name in {"netscaler_run_cli_command", "netscaler_ssh_run_command"}:
        if payload.get("commandFailed"):
            return False
    return True


def had_successful_state_change(tool_traces: list[ToolCallTrace]) -> bool:
    return any(
        trace_is_state_changing(trace) and trace_executed_successfully(trace)
        for trace in tool_traces
    )


_RESUME_WORDS = frozenset(
    {
        "continue",
        "continuar",
        "continua",
        "continúa",
        "resume",
        "go on",
        "keep going",
        "proceed",
        "procede",
    }
)

LONG_TASK_CONSENT_MESSAGE = (
    "This deployment may take longer than usual (multiple tool rounds). "
    "Progress so far is shown below. **Would you like me to continue?**"
)

ARCHITECT_PROGRESS_PROFILES: dict[str, dict[str, object]] = {
    "new_deployment": {
        "title": "Solution design in progress",
        "steps": (
            ("reference", "Review reference architecture & standards"),
            ("discover", "Confirm requirements & constraints"),
            ("deliver", "Prepare design deliverable"),
        ),
    },
    "new_functionality": {
        "title": "Functional change design in progress",
        "steps": (
            ("reference", "Assess existing environment"),
            ("discover", "Define change scope & impact"),
            ("deliver", "Prepare change design deliverable"),
        ),
    },
    "change_control": {
        "title": "Change control preparation in progress",
        "steps": (
            ("reference", "Document change scope & justification"),
            ("discover", "Assess risk & maintenance window"),
            ("deliver", "Prepare change control record"),
        ),
    },
    "default": {
        "title": "Planning in progress",
        "steps": (
            ("reference", "Clarify planning scope"),
            ("discover", "Gather requirements & inputs"),
            ("deliver", "Prepare planning deliverable"),
        ),
    },
}

_DESIGN_DELIVERABLE_MARKERS = (
    "<!-- jpilot-design-document -->",
    "<!-- jpilot-change-control-document -->",
)


@dataclass(frozen=True)
class ProgressSubtasksBundle:
    title: str
    subtasks: list[DeploymentSubtask]


@dataclass
class OrchestrationSettings:
    max_tool_iterations: int = DEFAULT_MAX_TOOL_ITERATIONS
    max_continuation_phases: int = DEFAULT_MAX_TOOL_CONTINUATION_PHASES
    long_task_threshold: int = DEFAULT_LONG_TASK_TOOL_THRESHOLD
    prompt_before_long_tasks: bool = True


@dataclass
class OrchestrationRuntime:
    settings: OrchestrationSettings
    long_task_approved: bool = False
    deployment_continuation: bool = False
    tool_rounds: int = 0
    pause: DeploymentContinuation | None = None

    @property
    def max_tool_iterations(self) -> int:
        return self.settings.max_tool_iterations

    @property
    def max_continuation_phases(self) -> int:
        return self.settings.max_continuation_phases

    def approve_long_task(self) -> None:
        self.long_task_approved = True
        self.pause = None

    def request_pause(self, *, reason: str, subtasks: list[DeploymentSubtask]) -> None:
        self.pause = DeploymentContinuation(
            required=True,
            reason=reason,
            message=LONG_TASK_CONSENT_MESSAGE,
            subtasks=subtasks,
        )


def orchestration_settings_from_document(document: dict | None) -> OrchestrationSettings:
    document = document or {}
    return OrchestrationSettings(
        max_tool_iterations=int(document.get("maxToolIterations", DEFAULT_MAX_TOOL_ITERATIONS)),
        max_continuation_phases=int(
            document.get("maxToolContinuationPhases", DEFAULT_MAX_TOOL_CONTINUATION_PHASES)
        ),
        long_task_threshold=int(document.get("longTaskToolThreshold", DEFAULT_LONG_TASK_TOOL_THRESHOLD)),
        prompt_before_long_tasks=bool(document.get("promptBeforeLongTasks", True)),
    )


def is_deployment_resume_message(message: str) -> bool:
    normalized = " ".join((message or "").strip().lower().split())
    if not normalized:
        return False
    if normalized in _RESUME_WORDS:
        return True
    return normalized.startswith("continue ") or normalized.startswith("continuar ")


def build_orchestration_runtime(
    *,
    settings: OrchestrationSettings,
    user_message: str,
    deployment_continuation: bool = False,
    long_task_approved: bool = False,
) -> OrchestrationRuntime:
    runtime = OrchestrationRuntime(
        settings=settings,
        deployment_continuation=deployment_continuation,
        long_task_approved=long_task_approved,
    )
    if deployment_continuation or is_deployment_resume_message(user_message):
        runtime.approve_long_task()
    return runtime


def operator_requires_documentation_review(
    user_message: str,
    *,
    conversation_text: str = "",
    attachment_names: list[str] | None = None,
) -> bool:
    """True when Operator progress should include a documentation review step."""
    names = attachment_names or []
    if user_requests_design_implementation(user_message, names):
        return True
    if is_design_implementation_form_submission(user_message):
        return True
    text = conversation_text or ""
    if "<!-- jpilot-design-document -->" in text:
        return True
    return False


def build_deployment_subtasks(
    tool_traces: list[ToolCallTrace],
    *,
    role: str | None = None,
    user_message: str = "",
    conversation_text: str = "",
    attachment_names: list[str] | None = None,
    deliverable_ready: bool = False,
) -> list[DeploymentSubtask]:
    return build_progress_subtasks(
        tool_traces,
        role=role,
        user_message=user_message,
        conversation_text=conversation_text,
        attachment_names=attachment_names,
        deliverable_ready=deliverable_ready,
    ).subtasks


def build_progress_subtasks(
    tool_traces: list[ToolCallTrace],
    *,
    role: str | None = None,
    user_message: str = "",
    conversation_text: str = "",
    attachment_names: list[str] | None = None,
    deliverable_ready: bool = False,
) -> ProgressSubtasksBundle:
    if normalize_role(role) == JPilotRole.ARCHITECT:
        return _build_architect_progress_subtasks(
            tool_traces,
            conversation_text=conversation_text,
            deliverable_ready=deliverable_ready,
        )
    return _build_operator_progress_subtasks(
        tool_traces,
        user_message=user_message,
        conversation_text=conversation_text,
        attachment_names=attachment_names,
    )


def _architect_profile(conversation_text: str) -> dict[str, object]:
    intent = extract_planning_intent(conversation_text) or "default"
    return ARCHITECT_PROGRESS_PROFILES.get(intent, ARCHITECT_PROGRESS_PROFILES["default"])


def _build_architect_progress_subtasks(
    tool_traces: list[ToolCallTrace],
    *,
    conversation_text: str = "",
    deliverable_ready: bool = False,
) -> ProgressSubtasksBundle:
    profile = _architect_profile(conversation_text)
    steps: tuple[tuple[str, str], ...] = profile["steps"]  # type: ignore[assignment]
    title = str(profile["title"])

    reference_count = sum(1 for trace in tool_traces if trace.name in ARCHITECT_REFERENCE_TOOLS)
    research_done = reference_count > 0

    if deliverable_ready:
        statuses = ["completed", "completed", "completed"]
    elif research_done:
        statuses = [
            "completed",
            "completed" if reference_count >= 2 else "in_progress",
            "in_progress" if reference_count >= 2 else "pending",
        ]
    else:
        statuses = ["pending", "pending", "pending"]

    subtasks = [
        DeploymentSubtask(id=step_id, label=label, status=statuses[index])  # type: ignore[arg-type]
        for index, (step_id, label) in enumerate(steps)
    ]
    return ProgressSubtasksBundle(title=title, subtasks=subtasks)


def _build_operator_progress_subtasks(
    tool_traces: list[ToolCallTrace],
    *,
    user_message: str = "",
    conversation_text: str = "",
    attachment_names: list[str] | None = None,
) -> ProgressSubtasksBundle:
    review_docs = operator_requires_documentation_review(
        user_message,
        conversation_text=conversation_text,
        attachment_names=attachment_names,
    )
    memory_reviewed = any(trace.name in MEMORY_SEARCH_TOOLS for trace in tool_traces)
    write_started = any(trace_is_state_changing(trace) for trace in tool_traces)
    saved = _classic_config_saved(tool_traces)

    if review_docs:
        reference_done = memory_reviewed
        reference_label = "Review documentation"
        title = "Deployment progress"
    else:
        reference_done = bool(tool_traces)
        reference_label = "Review request"
        title = "Operation progress"

    reference_status = "completed" if reference_done else "pending"
    execute_status = "pending"
    if saved:
        execute_status = "completed"
    elif write_started:
        execute_status = "in_progress"

    save_status = "completed" if saved else ("in_progress" if write_started else "pending")

    read_only = not review_docs and not write_started and not saved
    if tool_traces:
        read_only = read_only and not any(trace_is_state_changing(trace) for trace in tool_traces)

    if read_only:
        return ProgressSubtasksBundle(
            title="Operation progress",
            subtasks=[
                DeploymentSubtask(
                    id="reference",
                    label="Review request",
                    status="completed" if tool_traces else "pending",
                ),
            ],
        )

    return ProgressSubtasksBundle(
        title=title,
        subtasks=[
            DeploymentSubtask(id="reference", label=reference_label, status=reference_status),
            DeploymentSubtask(id="execute", label="Apply configuration", status=execute_status),
            DeploymentSubtask(id="save", label="Save configuration", status=save_status),
        ],
    )


def deliverable_ready_from_content(content: str) -> bool:
    text = content or ""
    return any(marker in text for marker in _DESIGN_DELIVERABLE_MARKERS)


def _trace_includes_save_ns_config(trace: ToolCallTrace) -> bool:
    arguments = trace.arguments or {}
    if trace.name == "netscaler_run_cli_command":
        return "save ns config" in str(arguments.get("command", "")).lower()
    if trace.name == "netscaler_run_cli_commands":
        commands = arguments.get("commands") or []
        return any("save ns config" in str(command).lower() for command in commands)
    return False


def _classic_config_saved(tool_traces: list[ToolCallTrace]) -> bool:
    import json

    for trace in tool_traces:
        if trace.name not in {"netscaler_run_cli_command", "netscaler_run_cli_commands"}:
            continue
        if not _trace_includes_save_ns_config(trace):
            continue
        try:
            payload = json.loads(trace.result)
        except (json.JSONDecodeError, TypeError):
            return True
        if isinstance(payload, dict) and payload.get("success") is False:
            continue
        return True
    return False


def should_offer_long_task_consent(
    runtime: OrchestrationRuntime,
    *,
    role: str | None,
    user_message: str,
    tool_traces: list[ToolCallTrace],
    deployment_incomplete: bool,
    continuation_phase: int,
) -> bool:
    if runtime.pause is not None:
        return False
    if runtime.long_task_approved:
        return False
    if not runtime.settings.prompt_before_long_tasks:
        return False
    if normalize_role(role) != JPilotRole.OPERATOR:
        return False
    if not deployment_incomplete:
        return False

    threshold_hit = runtime.tool_rounds >= runtime.settings.long_task_threshold
    continuation_pending = continuation_phase > 0
    return threshold_hit or continuation_pending


def continuation_for_tool_limit(
    tool_traces: list[ToolCallTrace],
    *,
    deployment_incomplete: bool,
    role: str | None = None,
    user_message: str = "",
    conversation_text: str = "",
    attachment_names: list[str] | None = None,
) -> DeploymentContinuation | None:
    if not deployment_incomplete:
        return None
    return DeploymentContinuation(
        required=True,
        reason="tool_limit",
        message=(
            "I reached the maximum number of tool calls before the deployment finished. "
            "Reply **continue** or use the button below to resume from where it stopped."
        ),
        subtasks=build_deployment_subtasks(
            tool_traces,
            role=role,
            user_message=user_message,
            conversation_text=conversation_text,
            attachment_names=attachment_names,
        ),
    )
