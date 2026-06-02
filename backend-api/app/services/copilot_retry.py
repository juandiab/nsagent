import json
from typing import Any


def _parse_tool_payload(result: str) -> Any:
    try:
        payload = json.loads(result)
    except (json.JSONDecodeError, TypeError):
        return None

    if isinstance(payload, dict) and "data" in payload:
        return payload["data"]
    return payload


def _user_asks_for_all_ips(user_message: str) -> bool:
    lowered = user_message.lower()
    if any(term in lowered for term in ("all ip", "list ip", "every ip", "show ns ip", "show ip", "ns ip")):
        return True
    if "ip" in lowered and any(term in lowered for term in ("all", "list", "every", "each")):
        return True
    return any(term in lowered for term in ("nsip", "snip"))


def _user_asks_for_management_ip_only(user_message: str) -> bool:
    lowered = user_message.lower()
    if _user_asks_for_all_ips(user_message):
        return False
    if "vip" in lowered or "virtual server" in lowered or "virtual ip" in lowered:
        return False
    return any(term in lowered for term in ("management ip", "mgmt ip", "management address"))


def build_tool_retry_hint(tool_name: str, result: str, user_message: str) -> str | None:
    data = _parse_tool_payload(result)

    if _user_asks_for_all_ips(user_message) and tool_name in {
        "netscaler_get_system_info",
        "netscaler_list_virtual_ips",
    }:
        return (
            "The user asked for all IP addresses on the appliance, not just the management IP or VIPs. "
            "Call netscaler_list_ip_addresses and report every address with its type (NSIP, SNIP, VIP, etc.). "
            "Do not add troubleshooting steps or suggestions."
        )

    if tool_name == "netscaler_list_virtual_ips" and _user_asks_for_management_ip_only(user_message):
        return (
            "Wrong tool for this request. The user asked for the appliance management IP only. "
            "Call netscaler_get_system_info and report ipAddress/managementIp. "
            "Do not add troubleshooting steps or suggestions."
        )

    lowered_message = user_message.lower()
    if tool_name == "netscaler_list_applications" and any(
        term in lowered_message for term in ("virtual server", "vserver", "lb vserver", "virtual servers")
    ):
        return (
            "The user asked for virtual servers, which may include classic lbvserver config not visible "
            "in Next-Gen applications only. Call netscaler_list_virtual_servers and report all entries "
            "(nextGenCount and classicCount). Do not add troubleshooting steps or suggestions."
        )

    empty_result = data == [] or data == {} or data is None
    missing_expected = False

    if tool_name == "netscaler_get_system_info" and isinstance(data, dict):
        msg = user_message.lower()
        asks_firmware = any(term in msg for term in ("firmware", "version", "build", "release"))
        if asks_firmware and not data.get("firmwareVersion") and not data.get("version"):
            missing_expected = True
        elif _user_asks_for_management_ip_only(user_message) and not data.get("ipAddress") and not data.get("managementIp"):
            missing_expected = True

    if tool_name == "netscaler_list_ip_addresses" and isinstance(data, dict):
        if _user_asks_for_all_ips(user_message) and not data.get("addresses"):
            missing_expected = True

    if empty_result or missing_expected:
        if _user_asks_for_all_ips(user_message):
            return (
                "IP listing via Next-Gen/NITRO did not return addresses. "
                "Follow SSH fallback: search_netscaler_cli_reference for 'show ns ip', "
                "then netscaler_ssh_run_command. Answer only what the user asked."
            )
        return (
            "The previous Next-Gen API tool did not return the information needed. "
            "Follow the SSH fallback workflow: "
            "1) decide the read-only CLI command (show/stat/get), "
            "2) call search_netscaler_cli_reference to confirm syntax, "
            "3) call netscaler_ssh_run_command with command and purpose. "
            "Answer only what the user asked — no extra instructions."
        )

    if tool_name == "search_netscaler_nextgen_api" and isinstance(data, dict):
        guide = data.get("guideMatches") or data
        has_guide = bool(guide.get("excerptCount"))
        has_memory = bool(guide.get("memoryExcerptCount") or data.get("memoryExcerptCount"))
        api_matches = guide.get("apiReferenceMatches") or data.get("apiReferenceMatches") or []
        if not has_guide and not has_memory and not api_matches:
            return (
                "Official Next-Gen memory/documentation search returned no matches. "
                "Broaden the search query. Do not use non-official web sources."
            )

    if tool_name == "search_netscaler_cli_reference" and isinstance(data, dict):
        has_memory = bool(data.get("memoryExcerptCount"))
        has_commands = bool(data.get("recommendedCommands"))
        if not has_memory and not has_commands:
            return (
                "CLI memory search returned no matches. Broaden the query using namespace/entity "
                "terms from netscaler_adc_cli_memory.md (e.g. lb vserver, show ns ip, stat lb vserver)."
            )
        lowered = user_message.lower()
        if any(v in lowered for v in ("create", "add", "bind", "configure", "setup", "set up")):
            return (
                "CLI reference loaded. Do NOT list commands in prose — EXECUTE them now with "
                "netscaler_run_cli_commands (full sequence + save ns config) or netscaler_run_cli_command "
                "once per command. Do not answer the user until every command succeeds."
            )

    if tool_name == "netscaler_telnet" and isinstance(data, dict):
        verdict = data.get("verdict")
        if verdict in ("open", "refused", "no_response"):
            return None

        payload_text = json.dumps(data).lower()
        if "timeout" in payload_text and "not found" in payload_text:
            return (
                "netscaler_telnet does not use the GNU timeout command. Call netscaler_telnet again — "
                "it runs `shell sh -c '/usr/bin/telnet HOST PORT </dev/null'` on NetScaler. "
                "Report the verdict/summary field. Do not tell the user the tool is permanently broken."
            )
        if verdict == "unknown":
            return (
                "Port check verdict was unknown. Call netscaler_telnet again. "
                "If raw output contains 'Connected to', report the port as OPEN even if "
                "'ERROR: Export failed' appears — that is normal NetScaler CLI noise."
            )

    if isinstance(data, dict) and data.get("blocked"):
        return data.get("message") or (
            "Next-Gen API tool blocked until search_netscaler_nextgen_api is called first."
        )

    if tool_name == "netscaler_nextgen_get" and isinstance(data, dict):
        guidance = data.get("memoryPathGuidance")
        if guidance:
            hints = guidance.get("hints") or []
            suggested = guidance.get("suggestedGetPaths") or []
            return (
                "The Next-Gen GET path may be incorrect. "
                f"Hints: {'; '.join(hints) if hints else 'see memory file'}. "
                f"Suggested paths: {', '.join(suggested[:5])}. "
                "Call search_netscaler_nextgen_api and retry with the correct path."
            )

    if tool_name == "netscaler_run_cli_commands" and isinstance(data, dict):
        if data.get("success") is False:
            failed = next(
                (item for item in (data.get("results") or []) if not item.get("success")),
                None,
            )
            if failed:
                suggested = failed.get("suggestedCommand") or ""
                message = failed.get("retryHint") or failed.get("errorMessage") or failed.get("output", "")[:200]
                if suggested:
                    message = f"{message} Retry with: {suggested}"
                return (
                    f"Command sequence failed at '{failed.get('command', '')}': {message} "
                    "Fix the failing command and retry netscaler_run_cli_commands. "
                    "Do not answer the user until the full sequence succeeds."
                )

    if tool_name in ("netscaler_ssh_run_command", "netscaler_run_cli_command") and isinstance(data, dict):
        # A failed ping/traceroute is a legitimate diagnostic result (host unreachable),
        # not a syntax error to fix — don't push the model to retry it.
        ran_command = str(data.get("command") or "").strip().lower()
        is_diagnostic = ran_command.startswith(("ping ", "ping6 ", "traceroute ", "traceroute6 "))
        failed = data.get("commandFailed") or data.get("success") is False or data.get("exitStatus") not in (0, None)
        if failed and not is_diagnostic:
            suggested = data.get("suggestedCommand") or ""
            retry_hint = data.get("retryHint") or ""
            usage = data.get("usage") or ""
            message = retry_hint or (
                f"SSH command failed: {data.get('errorMessage') or data.get('output', '')[:200]}"
            )
            if suggested:
                message = f"{message} Retry with: {suggested}"
            elif usage:
                message = f"{message} Official usage: {usage[:240]}"
            return (
                f"{message} "
                "Re-run search_netscaler_cli_reference if needed, then retry SSH with the exact official syntax. "
                "Do not answer the user until the command succeeds or API tools provide the data."
            )

    return None
