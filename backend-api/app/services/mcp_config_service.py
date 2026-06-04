from datetime import datetime, timezone

from urllib.parse import urlparse

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.config import settings as app_settings
from app.schemas.mcp_config import MCPSettingsResponse, MCPSettingsUpdate

SETTINGS_ID = "default"

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

LEGACY_TOOL_ALIASES = {
    "netscaler_list_lb_vservers": "netscaler_list_virtual_servers",
}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _is_local_mcp_url(url: str) -> bool:
    host = (urlparse(url.strip()).hostname or "").lower()
    return host in {"localhost", "127.0.0.1", "0.0.0.0"}


def default_settings() -> dict:
    return {
        "_id": SETTINGS_ID,
        "serverUrl": app_settings.mcp_server_url,
        "serverName": "netscaler-copilot",
        "nitroTimeoutSeconds": 30,
        "verifySsl": False,
        "enabledTools": list(ALL_TOOL_NAMES),
        "sseEnabled": True,
        "sshFallbackEnabled": True,
        "sshPort": 22,
        "sshTimeoutSeconds": 30,
        "updatedAt": utc_now(),
    }


async def ensure_default_settings(db: AsyncIOMotorDatabase) -> None:
    existing = await db.mcpSettings.find_one({"_id": SETTINGS_ID})
    if existing is None:
        await db.mcpSettings.insert_one(default_settings())
        return

    stored_url = str(existing.get("serverUrl") or "").strip()
    if stored_url and _is_local_mcp_url(stored_url):
        await db.mcpSettings.update_one(
            {"_id": SETTINGS_ID},
            {"$set": {"serverUrl": app_settings.mcp_server_url, "updatedAt": utc_now()}},
        )

    enabled_tools = existing.get("enabledTools", [])
    migrated = False
    normalized_tools: list[str] = []
    for name in enabled_tools:
        mapped = LEGACY_TOOL_ALIASES.get(name, name)
        if mapped not in normalized_tools:
            normalized_tools.append(mapped)
        if mapped != name:
            migrated = True

    for name in ALL_TOOL_NAMES:
        if name not in normalized_tools:
            normalized_tools.append(name)
            migrated = True

    if migrated:
        await db.mcpSettings.update_one(
            {"_id": SETTINGS_ID},
            {"$set": {"enabledTools": normalized_tools, "updatedAt": utc_now()}},
        )

    ssh_defaults = {
        "sshFallbackEnabled": True,
        "sshPort": 22,
        "sshTimeoutSeconds": 30,
    }
    missing_ssh = {key: value for key, value in ssh_defaults.items() if key not in existing}
    if missing_ssh:
        await db.mcpSettings.update_one(
            {"_id": SETTINGS_ID},
            {"$set": {**missing_ssh, "updatedAt": utc_now()}},
        )


async def get_mcp_settings(db: AsyncIOMotorDatabase) -> MCPSettingsResponse:
    await ensure_default_settings(db)
    document = await db.mcpSettings.find_one({"_id": SETTINGS_ID})
    return serialize_settings(document)


async def update_mcp_settings(
    db: AsyncIOMotorDatabase,
    payload: MCPSettingsUpdate,
) -> MCPSettingsResponse:
    await ensure_default_settings(db)

    enabled_tools = payload.enabledTools or list(ALL_TOOL_NAMES)
    enabled_tools = [LEGACY_TOOL_ALIASES.get(name, name) for name in enabled_tools]
    invalid = [name for name in enabled_tools if name not in ALL_TOOL_NAMES]
    if invalid:
        raise ValueError(f"Unknown tools: {', '.join(invalid)}")

    update_data = {
        **payload.model_dump(),
        "enabledTools": enabled_tools,
        "updatedAt": utc_now(),
    }

    await db.mcpSettings.update_one({"_id": SETTINGS_ID}, {"$set": update_data}, upsert=True)
    document = await db.mcpSettings.find_one({"_id": SETTINGS_ID})
    return serialize_settings(document)


def serialize_settings(document: dict) -> MCPSettingsResponse:
    return MCPSettingsResponse(
        id=str(document["_id"]),
        serverUrl=document["serverUrl"],
        serverName=document.get("serverName", "netscaler-copilot"),
        nitroTimeoutSeconds=document.get("nitroTimeoutSeconds", 30),
        verifySsl=document.get("verifySsl", False),
        enabledTools=document.get("enabledTools", list(ALL_TOOL_NAMES)),
        sseEnabled=document.get("sseEnabled", True),
        sshFallbackEnabled=document.get("sshFallbackEnabled", True),
        sshPort=document.get("sshPort", 22),
        sshTimeoutSeconds=document.get("sshTimeoutSeconds", 30),
        updatedAt=document["updatedAt"],
    )


async def get_active_server_url(db: AsyncIOMotorDatabase) -> str:
    settings = await get_mcp_settings(db)
    return settings.serverUrl.rstrip("/")
