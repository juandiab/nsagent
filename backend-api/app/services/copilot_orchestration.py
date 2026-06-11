"""Agent orchestration: tool limits, deployment subtasks, and long-task consent."""

from __future__ import annotations

from dataclasses import dataclass

from app.schemas.copilot import DeploymentContinuation, DeploymentSubtask, ToolCallTrace
from app.services.copilot_roles import JPilotRole, normalize_role

DEFAULT_MAX_TOOL_ITERATIONS = 20
DEFAULT_MAX_TOOL_CONTINUATION_PHASES = 3
DEFAULT_LONG_TASK_TOOL_THRESHOLD = 8

MEMORY_SEARCH_TOOLS = frozenset(
    {
        "search_netscaler_cli_reference",
        "search_netscaler_nextgen_api",
        "search_cisco_cli_reference",
        "search_sdx_cli_reference",
        "search_f5_tmsh_reference",
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


def build_deployment_subtasks(tool_traces: list[ToolCallTrace]) -> list[DeploymentSubtask]:
    reference_done = any(trace.name in MEMORY_SEARCH_TOOLS for trace in tool_traces)
    write_started = any(trace.name in WRITE_EXEC_TOOL_NAMES for trace in tool_traces)
    saved = _classic_config_saved(tool_traces)

    reference_status = "completed" if reference_done else "pending"
    execute_status = "pending"
    if saved:
        execute_status = "completed"
    elif write_started:
        execute_status = "in_progress"

    save_status = "completed" if saved else ("in_progress" if write_started else "pending")

    return [
        DeploymentSubtask(id="reference", label="Review documentation", status=reference_status),
        DeploymentSubtask(id="execute", label="Apply configuration", status=execute_status),
        DeploymentSubtask(id="save", label="Save configuration", status=save_status),
    ]


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
        subtasks=build_deployment_subtasks(tool_traces),
    )
