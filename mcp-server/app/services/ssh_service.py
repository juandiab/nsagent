import re
from typing import Any

import asyncssh

READONLY_PREFIXES = ("show ", "stat ", "get ")
# Read-only diagnostic/troubleshooting commands (ICMP reachability, path tracing).
DIAGNOSTIC_PREFIXES = ("ping ", "ping6 ", "traceroute ", "traceroute6 ")
DEFAULT_PING_COUNT = 4
MAX_PING_COUNT = 10
# traceroute defaults of 64 hops x 3 queries x 5s would far exceed the SSH timeout.
# Bound it so it completes (max ~ MAX_HOPS x WAIT x 1 query) within the timeout.
DEFAULT_TRACEROUTE_MAX_HOPS = 15
MAX_TRACEROUTE_MAX_HOPS = 20
TRACEROUTE_WAIT_SECONDS = 2
# Shell metacharacters are never valid in a NetScaler diagnostic argument; block
# them to prevent any command chaining/injection via the host argument.
_SHELL_METACHARS = re.compile(r"[;&|`$><\\\n]")
_PING_COUNT_RE = re.compile(r"(^|\s)-c\s+(\d+)")
_TRACE_MAXHOPS_RE = re.compile(r"(^|\s)-m\s+(\d+)")
BLOCKED_TOKENS = (
    " set ",
    " rm ",
    " add ",
    " bind ",
    " unbind ",
    " clear ",
    " delete ",
    " install ",
    " reboot",
    " shutdown",
    " configure ",
    " enable ",
    " disable ",
    " shell ",
    " bash",
    " sh ",
)

INVALID_SHOW_PATTERNS = (
    re.compile(r"^show\s+.+\s+statistics\b", re.IGNORECASE),
)

# Commands that would break out of the NetScaler CLI into the underlying BSD
# shell are never permitted, even when configuration writes are allowed.
SHELL_BREAKOUT_TOKENS = (
    "shell",
    "bash",
    "/bin/sh",
    "/bin/bash",
    "csh",
    "tcsh",
    "zsh",
    "ksh",
    "scp",
)


def normalize_cli_command(command: str) -> str:
    return " ".join(command.strip().split())


def is_diagnostic_command(command: str) -> bool:
    return normalize_cli_command(command).lower().startswith(DIAGNOSTIC_PREFIXES)


def sanitize_diagnostic_command(command: str) -> str:
    """Validate ping/traceroute and bound ping so it cannot run indefinitely over SSH."""
    normalized = normalize_cli_command(command)
    if not normalized:
        raise ValueError("command is required")

    if _SHELL_METACHARS.search(normalized):
        raise ValueError("Diagnostic commands must not contain shell metacharacters")

    verb = normalized.lower().split()[0]
    if verb in ("ping", "ping6"):
        if _PING_COUNT_RE.search(normalized):
            normalized = _PING_COUNT_RE.sub(
                lambda m: f"{m.group(1)}-c {min(int(m.group(2)), MAX_PING_COUNT)}",
                normalized,
            )
        else:
            parts = normalized.split(maxsplit=1)
            rest = parts[1] if len(parts) > 1 else ""
            if not rest:
                raise ValueError("ping requires a target host or IP")
            normalized = f"{parts[0]} -c {DEFAULT_PING_COUNT} {rest}".strip()
    elif verb in ("traceroute", "traceroute6"):
        if _TRACE_MAXHOPS_RE.search(normalized):
            normalized = _TRACE_MAXHOPS_RE.sub(
                lambda m: f"{m.group(1)}-m {min(int(m.group(2)), MAX_TRACEROUTE_MAX_HOPS)}",
                normalized,
            )
        else:
            parts = normalized.split(maxsplit=1)
            rest = parts[1] if len(parts) > 1 else ""
            if not rest:
                raise ValueError("traceroute requires a target host or IP")
            # Bound hops, one query per hop, short wait — so it finishes within the SSH timeout.
            normalized = (
                f"{parts[0]} -q 1 -w {TRACEROUTE_WAIT_SECONDS} "
                f"-m {DEFAULT_TRACEROUTE_MAX_HOPS} {rest}".strip()
            )

    return normalized


def validate_cli_command(command: str) -> str:
    normalized = normalize_cli_command(command).lower()
    if not normalized:
        raise ValueError("command is required")

    if normalized.startswith(DIAGNOSTIC_PREFIXES):
        return sanitize_diagnostic_command(command)

    if not normalized.startswith(READONLY_PREFIXES):
        raise ValueError(
            "Only read-only show, stat, get, ping, or traceroute commands are allowed via SSH"
        )

    padded = f" {normalized} "
    for token in BLOCKED_TOKENS:
        if token in padded:
            raise ValueError(f"Command contains blocked token: {token.strip()}")

    for pattern in INVALID_SHOW_PATTERNS:
        if pattern.match(normalized):
            raise ValueError(
                "Invalid syntax: statistics require 'stat', not 'show ... statistics'. "
                "Search the CLI reference and use the recommended command."
            )

    return normalize_cli_command(command)


def validate_writable_cli_command(command: str) -> str:
    """Validate a CLI command that may modify configuration.

    Any documented NetScaler CLI verb is allowed (add, set, bind, unbind,
    enable, disable, rm, clear, save, ...). The only hard block is escaping
    the NetScaler CLI into the underlying BSD shell.
    """
    normalized = normalize_cli_command(command)
    if not normalized:
        raise ValueError("command is required")

    if is_diagnostic_command(normalized):
        return sanitize_diagnostic_command(normalized)

    tokens = normalized.lower().split()
    if tokens and tokens[0] in SHELL_BREAKOUT_TOKENS:
        raise ValueError("Dropping to the BSD shell is not permitted via this tool")

    for pattern in INVALID_SHOW_PATTERNS:
        if pattern.match(normalized.lower()):
            raise ValueError(
                "Invalid syntax: statistics require 'stat', not 'show ... statistics'. "
                "Search the CLI reference and use the recommended command."
            )

    return normalized


def _parse_cli_failure_output(stdout: str, stderr: str) -> dict[str, Any]:
    combined = f"{stdout}\n{stderr}".strip()
    details: dict[str, Any] = {}

    error_match = re.search(r"ERROR:\s*(.+)", combined, flags=re.IGNORECASE)
    if error_match:
        details["errorMessage"] = error_match.group(1).strip()

    usage_match = re.search(r"Usage:\s*(.+)", combined, flags=re.IGNORECASE | re.DOTALL)
    if usage_match:
        details["usage"] = " ".join(usage_match.group(1).split())

    alias_match = re.search(r"alias for '([^']+)'", combined, flags=re.IGNORECASE)
    if alias_match:
        details["suggestedCommand"] = alias_match.group(1).strip()

    return details


def _command_succeeded(exit_status: int | None, stdout: str, stderr: str) -> bool:
    combined = f"{stdout}\n{stderr}"
    if exit_status not in (0, None):
        return False
    if re.search(r"\bERROR:\b", combined, flags=re.IGNORECASE):
        return False
    if re.search(r"\bUsage:\b", combined, flags=re.IGNORECASE) and not stdout.strip().endswith("Done"):
        return False
    return True


async def _execute_ssh(
    safe_command: str,
    host: str,
    username: str,
    password: str,
    *,
    port: int,
    timeout: float,
) -> dict[str, Any]:
    """Connect, run an ALREADY-VALIDATED command, and return a parsed result payload.

    Callers are responsible for validating/sanitizing safe_command before calling this.
    """
    from app.services.netscaler_service import normalize_host

    target = normalize_host(host)

    try:
        async with asyncssh.connect(
            target,
            port=port,
            username=username,
            password=password,
            known_hosts=None,
            login_timeout=timeout,
        ) as conn:
            result = await conn.run(safe_command, check=False, timeout=timeout)
    except asyncssh.Error as exc:
        raise ValueError(f"SSH connection failed: {exc}") from exc
    except OSError as exc:
        raise ValueError(f"SSH connection failed: {exc}") from exc

    stdout = (result.stdout or "").strip()
    stderr = (result.stderr or "").strip()
    exit_status = result.exit_status
    success = _command_succeeded(exit_status, stdout, stderr)
    failure_details = {} if success else _parse_cli_failure_output(stdout, stderr)

    payload: dict[str, Any] = {
        "host": target,
        "transport": "SSH",
        "port": port,
        "command": safe_command,
        "exitStatus": exit_status,
        "success": success,
        "output": stdout,
        "stderr": stderr,
    }

    if not success:
        payload["commandFailed"] = True
        payload.update(failure_details)
        if failure_details.get("suggestedCommand"):
            payload["retryHint"] = (
                f"Command failed. Use '{failure_details['suggestedCommand']}' instead and do not answer the user until it succeeds."
            )

    return payload


async def run_ssh_command(
    host: str,
    username: str,
    password: str,
    command: str,
    *,
    port: int = 22,
    timeout: float = 30.0,
    allow_writes: bool = False,
) -> dict[str, Any]:
    safe_command = (
        validate_writable_cli_command(command) if allow_writes else validate_cli_command(command)
    )
    return await _execute_ssh(
        safe_command, host, username, password, port=port, timeout=timeout
    )


async def run_prevalidated_command(
    command: str,
    host: str,
    username: str,
    password: str,
    *,
    port: int = 22,
    timeout: float = 30.0,
) -> dict[str, Any]:
    """Run a command that the caller has already built and validated as safe.

    Used only for internally-constructed commands (e.g. the scoped nsconmsg builder),
    NOT for arbitrary model-supplied input.
    """
    return await _execute_ssh(
        normalize_cli_command(command), host, username, password, port=port, timeout=timeout
    )
