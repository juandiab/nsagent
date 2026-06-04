"""Cisco IOS/XE SSH command validation and execution."""

from __future__ import annotations

import re
from typing import Any

from app.services.ssh_service import _execute_ssh, normalize_cli_command

READONLY_PREFIXES = ("show ", "display ", "ping ", "ping6 ", "traceroute ", "traceroute6 ")
_SHELL_METACHARS = re.compile(r"[;&|`$><\\\n]")
_SHELL_BREAKOUT = frozenset(
    {
        "bash",
        "guestshell",
        "tclsh",
        "python",
        "exec",
        "/bin/sh",
        "/bin/bash",
    }
)
READONLY_BLOCKED = (
    " configure ",
    " conf t",
    " copy ",
    " delete ",
    " erase ",
    " reload",
    " write erase",
    " format ",
)


def validate_readonly_command(command: str) -> str:
    normalized = normalize_cli_command(command)
    if not normalized:
        raise ValueError("command is required")
    lowered = normalized.lower()
    if _SHELL_METACHARS.search(normalized):
        raise ValueError("Commands must not contain shell metacharacters")
    if not lowered.startswith(READONLY_PREFIXES):
        raise ValueError("Only show, display, ping, or traceroute commands are allowed via read-only SSH")
    padded = f" {lowered} "
    for token in READONLY_BLOCKED:
        if token in padded:
            raise ValueError(f"Blocked token in read-only command: {token.strip()}")
    first = lowered.split()[0]
    if first in _SHELL_BREAKOUT:
        raise ValueError("Shell escape commands are not permitted")
    return normalized


def validate_writable_command(command: str) -> str:
    normalized = normalize_cli_command(command)
    if not normalized:
        raise ValueError("command is required")
    if _SHELL_METACHARS.search(normalized):
        raise ValueError("Commands must not contain shell metacharacters")
    tokens = normalized.lower().split()
    if tokens and tokens[0] in _SHELL_BREAKOUT:
        raise ValueError("Shell escape commands are not permitted")
    return normalized


async def _run_command(
    host: str,
    username: str,
    password: str,
    command: str,
    *,
    allow_writes: bool,
    port: int,
    timeout: float,
) -> dict[str, Any]:
    from app.services.config_service import get_runtime_config

    config = get_runtime_config()
    if not config.ssh_fallback_enabled:
        raise ValueError("SSH is disabled in MCP server configuration")

    safe = validate_writable_command(command) if allow_writes else validate_readonly_command(command)
    return await _execute_ssh(
        safe,
        host,
        username,
        password,
        port=port or config.ssh_port,
        timeout=timeout or float(config.ssh_timeout_seconds),
    )


async def test_connection(host: str, username: str, password: str) -> tuple[bool, str]:
    try:
        result = await _run_command(
            host,
            username,
            password,
            "show version",
            allow_writes=False,
            port=22,
            timeout=30.0,
        )
    except ValueError as exc:
        return False, str(exc)
    if result.get("success"):
        version_line = (result.get("output") or "").splitlines()[0:3]
        snippet = " ".join(line.strip() for line in version_line if line.strip())
        return True, snippet or "SSH login successful"
    message = result.get("errorMessage") or result.get("stderr") or "show version failed"
    return False, message


async def ssh_run_command(host: str, username: str, password: str, command: str) -> dict[str, Any]:
    return await _run_command(host, username, password, command, allow_writes=False, port=22, timeout=30.0)


async def run_cli_command(host: str, username: str, password: str, command: str) -> dict[str, Any]:
    return await _run_command(host, username, password, command, allow_writes=True, port=22, timeout=30.0)


async def run_cli_commands(host: str, username: str, password: str, commands: list[str]) -> dict[str, Any]:
    if not commands:
        raise ValueError("commands is required")
    results: list[dict[str, Any]] = []
    for command in commands:
        result = await run_cli_command(host, username, password, command)
        results.append(result)
        if not result.get("success"):
            break
    return {
        "success": all(item.get("success") for item in results),
        "commandCount": len(results),
        "results": results,
    }
