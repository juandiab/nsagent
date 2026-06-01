import re
from typing import Any

import asyncssh

READONLY_PREFIXES = ("show ", "stat ", "get ")
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


def validate_cli_command(command: str) -> str:
    normalized = normalize_cli_command(command).lower()
    if not normalized:
        raise ValueError("command is required")

    if not normalized.startswith(READONLY_PREFIXES):
        raise ValueError("Only read-only show, stat, or get commands are allowed via SSH")

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
    from app.services.netscaler_service import normalize_host

    safe_command = (
        validate_writable_cli_command(command) if allow_writes else validate_cli_command(command)
    )
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
