"""Detect TCP port-check questions and run netscaler_telnet without relying on the LLM."""

from __future__ import annotations

import json
import re
from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.schemas.copilot import ToolCallTrace

_TCP_PORT_IN_MESSAGE = re.compile(
    r"(\d{1,3}(?:\.\d{1,3}){3})\s*:\s*(\d{1,5})\b"
)
_IP_THEN_PORT = re.compile(
    r"(\d{1,3}(?:\.\d{1,3}){3}).*?\bport\s+(\d{1,5})\b",
    re.IGNORECASE,
)
_PORT_THEN_IP = re.compile(
    r"\bport\s+(\d{1,5})\b.*?(\d{1,3}(?:\.\d{1,3}){3})",
    re.IGNORECASE,
)
_PORT_CHECK_HINT = re.compile(
    r"\b(reach|reachable|open|connect|connectivity|telnet|port\s+check|port\s+\d)\b",
    re.IGNORECASE,
)


def detect_tcp_port_check(message: str) -> tuple[str, int] | None:
    """Return (host_or_ip, port) when the user is asking about TCP port reachability."""
    text = (message or "").strip()
    if not text:
        return None

    for pattern in (_TCP_PORT_IN_MESSAGE, _IP_THEN_PORT, _PORT_THEN_IP):
        match = pattern.search(text)
        if match:
            if pattern is _PORT_THEN_IP:
                port = int(match.group(1))
                host = match.group(2)
            else:
                host = match.group(1)
                port = int(match.group(2))
            if 1 <= port <= 65535:
                return host, port

    if not _PORT_CHECK_HINT.search(text):
        return None
    return None


def _parse_tool_result(result: str) -> dict[str, Any] | None:
    try:
        payload = json.loads(result)
    except (json.JSONDecodeError, TypeError):
        return None
    if isinstance(payload, dict) and isinstance(payload.get("data"), dict):
        return payload["data"]
    return payload if isinstance(payload, dict) else None


def format_port_check_response(appliance_name: str, target: str, port: int, data: dict[str, Any]) -> str:
    verdict = data.get("verdict", "unknown")
    summary = data.get("summary") or data.get("verdictMeaning") or verdict
    command = data.get("command", "")
    lines = [
        f"**{appliance_name}** — TCP port **{target}:{port}**",
        "",
        f"**Verdict:** {summary}",
    ]
    if command:
        lines.extend(["", f"Command run on appliance: `{command}`"])
    output = (data.get("output") or "").strip()
    if output:
        snippet = "\n".join(output.splitlines()[:6])
        lines.extend(["", "**Telnet output (excerpt):**", f"```\n{snippet}\n```"])
    return "\n".join(lines)


async def try_auto_tcp_port_check(
    db: AsyncIOMotorDatabase,
    *,
    user_message: str,
    appliance_name: str,
    enabled_tool_names: set[str],
) -> tuple[list[ToolCallTrace], str | None]:
    """Run netscaler_telnet when the user message contains host:port reachability intent."""
    if not appliance_name:
        return [], None
    if "netscaler_telnet" not in enabled_tool_names:
        return [], None

    parsed = detect_tcp_port_check(user_message)
    if not parsed:
        return [], None

    target, port = parsed
    from app.services.copilot_service import execute_copilot_tool

    arguments = {
        "appliance_name": appliance_name,
        "target": target,
        "port": port,
    }
    try:
        result = await execute_copilot_tool(
            db,
            "netscaler_telnet",
            arguments,
            default_appliance_name=appliance_name,
        )
    except Exception as exc:
        result = json.dumps({"success": False, "message": str(exc)}, indent=2)

    trace = ToolCallTrace(name="netscaler_telnet", arguments=arguments, result=result)
    data = _parse_tool_result(result)
    if data and data.get("verdict") in {"open", "refused", "no_response"}:
        return [trace], format_port_check_response(appliance_name, target, port, data)

    context = (
        f"\n\n[Auto-executed netscaler_telnet for {target}:{port}]\n{result}\n"
        "Report the summary/verdict to the user. Do not claim port-check tools are broken.\n"
    )
    return [trace], context
