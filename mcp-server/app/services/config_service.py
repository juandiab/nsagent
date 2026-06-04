from dataclasses import dataclass, field


ALL_TOOL_NAMES = [
    "netscaler_test_connection",
    "netscaler_get_system_info",
    "netscaler_list_applications",
    "netscaler_list_virtual_servers",
    "netscaler_list_virtual_ips",
    "netscaler_list_ip_addresses",
    "netscaler_nextgen_get",
    "netscaler_create_application",
    "netscaler_add_ip_address",
    "netscaler_ssh_run_command",
    "netscaler_run_cli_command",
    "netscaler_run_cli_commands",
    "netscaler_run_diagnostic",
    "netscaler_telnet",
    "netscaler_collect_nsconmsg",
    "netscaler_nextgen_request",
    "netscaler_generate_csr",
    "cisco_test_connection",
    "cisco_ssh_run_command",
    "cisco_run_cli_command",
    "cisco_run_cli_commands",
]


@dataclass
class MCPRuntimeConfig:
    server_name: str = "netscaler-copilot"
    nitro_timeout_seconds: int = 30
    verify_ssl: bool = False
    enabled_tools: list[str] = field(default_factory=lambda: list(ALL_TOOL_NAMES))
    sse_enabled: bool = True
    ssh_fallback_enabled: bool = True
    ssh_port: int = 22
    ssh_timeout_seconds: int = 30


_runtime_config = MCPRuntimeConfig()


def get_runtime_config() -> MCPRuntimeConfig:
    return _runtime_config


def update_runtime_config(payload: dict) -> MCPRuntimeConfig:
    global _runtime_config
    enabled_tools = payload.get("enabledTools") or list(ALL_TOOL_NAMES)
    _runtime_config = MCPRuntimeConfig(
        server_name=payload.get("serverName", "netscaler-copilot"),
        nitro_timeout_seconds=int(payload.get("nitroTimeoutSeconds", 30)),
        verify_ssl=bool(payload.get("verifySsl", False)),
        enabled_tools=[name for name in enabled_tools if name in ALL_TOOL_NAMES],
        sse_enabled=bool(payload.get("sseEnabled", True)),
        ssh_fallback_enabled=bool(payload.get("sshFallbackEnabled", True)),
        ssh_port=int(payload.get("sshPort", 22)),
        ssh_timeout_seconds=int(payload.get("sshTimeoutSeconds", 30)),
    )
    return _runtime_config


def serialize_runtime_config() -> dict:
    config = get_runtime_config()
    return {
        "serverName": config.server_name,
        "nitroTimeoutSeconds": config.nitro_timeout_seconds,
        "verifySsl": config.verify_ssl,
        "enabledTools": config.enabled_tools,
        "sseEnabled": config.sse_enabled,
        "sshFallbackEnabled": config.ssh_fallback_enabled,
        "sshPort": config.ssh_port,
        "sshTimeoutSeconds": config.ssh_timeout_seconds,
    }


def is_tool_enabled(name: str) -> bool:
    return name in get_runtime_config().enabled_tools
