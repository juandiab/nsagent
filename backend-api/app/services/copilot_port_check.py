"""Detect connectivity questions and run NetScaler diagnostics without relying on the LLM."""

from __future__ import annotations

import json
import re
from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.schemas.copilot import ToolCallTrace

_DEFAULT_INTERNET_PROBE = "8.8.8.8"
_APPLIANCE_CONTEXT = re.compile(
    r"\b(netscaler|adc|appliance|nsip|the box|this box|vpx)\b",
    re.IGNORECASE,
)
_INTERNET_QUESTION = re.compile(
    r"\b("
    r"internet access|internet connectivity|reach the internet|"
    r"outbound internet|has internet|access the internet|"
    r"connect to the internet|external connectivity"
    r")\b",
    re.IGNORECASE,
)
_JPILOT_INTERNET = re.compile(
    r"\b(can you reach|can jpilot|jpilot reach|your server|the backend|documentation site)\b",
    re.IGNORECASE,
)

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


def detect_appliance_internet_check(message: str) -> bool:
    """Return True when the user asks whether the connected appliance has internet access."""
    text = (message or "").strip()
    if not text or not _INTERNET_QUESTION.search(text):
        return False
    if _JPILOT_INTERNET.search(text) and not _APPLIANCE_CONTEXT.search(text):
        return False
    return True


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


def _ping_summary(data: dict[str, Any]) -> str:
    summary = (data.get("summary") or data.get("verdict") or "").strip()
    if summary:
        return summary
    output = (data.get("output") or "").strip()
    if "received" in output.lower():
        return output.splitlines()[0][:160]
    return "completed"


def _default_route_summary(output: str) -> str:
    for line in (output or "").splitlines():
        normalized = line.strip()
        if normalized.startswith("0.0.0.0/0") or normalized.startswith("0.0.0.0 "):
            return normalized[:160]
    for line in (output or "").splitlines():
        if "0.0.0.0" in line:
            return line.strip()[:160]
    return "not found in route table"


def format_internet_check_response(
    appliance_name: str,
    *,
    route_summary: str,
    ping_summary: str,
    has_default_route: bool,
    ping_ok: bool,
) -> str:
    verdict = "Yes" if has_default_route and ping_ok else "No or inconclusive"
    lines = [
        f"**{appliance_name} — Internet access**",
        "",
        "| Check | Result |",
        "| --- | --- |",
        f"| Default route | {route_summary or 'not found'} |",
        f"| Ping to {_DEFAULT_INTERNET_PROBE} | {ping_summary or 'not completed'} |",
        "",
        f"**Internet access:** {verdict}",
    ]
    return "\n".join(lines)


async def try_auto_appliance_internet_check(
    db: AsyncIOMotorDatabase,
    *,
    user_message: str,
    appliance_name: str,
    enabled_tool_names: set[str],
) -> tuple[list[ToolCallTrace], str | None]:
    """Run show route + ping when the user asks whether the appliance has internet access."""
    if not appliance_name:
        return [], None
    if not detect_appliance_internet_check(user_message):
        return [], None
    if "netscaler_run_diagnostic" not in enabled_tool_names:
        return [], None

    from app.services.copilot_service import execute_copilot_tool

    traces: list[ToolCallTrace] = []
    route_summary = ""
    has_default_route = False
    ping_summary = ""
    ping_ok = False

    if "netscaler_run_cli_command" in enabled_tool_names:
        route_args = {
            "appliance_name": appliance_name,
            "command": "show route",
            "purpose": "Check default route for internet access",
        }
        try:
            route_result = await execute_copilot_tool(
                db,
                "netscaler_run_cli_command",
                route_args,
                default_appliance_name=appliance_name,
            )
        except Exception as exc:
            route_result = json.dumps({"success": False, "message": str(exc)}, indent=2)
        traces.append(ToolCallTrace(name="netscaler_run_cli_command", arguments=route_args, result=route_result))
        route_data = _parse_tool_result(route_result) or {}
        route_output = str(route_data.get("output") or "")
        route_summary = _default_route_summary(route_output)
        has_default_route = "0.0.0.0" in route_output

    ping_args = {
        "appliance_name": appliance_name,
        "operation": "ping",
        "target": _DEFAULT_INTERNET_PROBE,
        "count": 4,
    }
    try:
        ping_result = await execute_copilot_tool(
            db,
            "netscaler_run_diagnostic",
            ping_args,
            default_appliance_name=appliance_name,
        )
    except Exception as exc:
        ping_result = json.dumps({"success": False, "message": str(exc)}, indent=2)
    traces.append(ToolCallTrace(name="netscaler_run_diagnostic", arguments=ping_args, result=ping_result))
    ping_data = _parse_tool_result(ping_result) or {}
    ping_summary = _ping_summary(ping_data)
    ping_output = str(ping_data.get("output") or ping_data.get("summary") or "").lower()
    ping_ok = ping_data.get("success") is not False and (
        "0% loss" in ping_output
        or "0.0% loss" in ping_output
        or "4 received" in ping_output
        or ping_data.get("verdict") in {"success", "reachable", "up"}
    )

    if traces and (has_default_route or ping_ok):
        return [
            *traces
        ], format_internet_check_response(
            appliance_name,
            route_summary=route_summary,
            ping_summary=ping_summary,
            has_default_route=has_default_route,
            ping_ok=ping_ok,
        )

    context = (
        "\n\n[Auto-executed appliance internet checks]\n"
        f"show route summary: {route_summary or 'unavailable'}\n"
        f"ping {_DEFAULT_INTERNET_PROBE}: {ping_summary or ping_result}\n"
        "Report these results directly. Do not tell the user manual CLI is required.\n"
    )
    return traces, context


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
