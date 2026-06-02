import httpx
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.config import settings
from app.schemas.mcp_config import MCPSettingsResponse


async def _resolve_server_url(db: AsyncIOMotorDatabase | None, server_url: str | None = None) -> str:
    if server_url:
        return server_url.rstrip("/")
    if db is not None:
        from app.services.mcp_config_service import get_active_server_url

        return await get_active_server_url(db)
    return settings.mcp_server_url.rstrip("/")


async def push_config_to_mcp_server(config: MCPSettingsResponse) -> None:
    url = f"{config.serverUrl.rstrip('/')}/config"
    payload = {
        "serverName": config.serverName,
        "nitroTimeoutSeconds": config.nitroTimeoutSeconds,
        "verifySsl": config.verifySsl,
        "enabledTools": config.enabledTools,
        "sseEnabled": config.sseEnabled,
        "sshFallbackEnabled": config.sshFallbackEnabled,
        "sshPort": config.sshPort,
        "sshTimeoutSeconds": config.sshTimeoutSeconds,
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.put(url, json=payload)
        response.raise_for_status()


async def get_mcp_health(db: AsyncIOMotorDatabase | None = None, server_url: str | None = None) -> dict:
    base_url = await _resolve_server_url(db, server_url)
    async with httpx.AsyncClient(timeout=10.0) as client:
        health = await client.get(f"{base_url}/health")
        health.raise_for_status()
        tools = await client.get(f"{base_url}/tools")
        tools.raise_for_status()
    tools_payload = tools.json()
    tool_items = tools_payload.get("tools", [])
    return {
        "online": True,
        "health": health.json(),
        "tools": tool_items,
        "toolCount": len(tool_items),
    }


async def _post_mcp(
    path: str,
    payload: dict,
    db: AsyncIOMotorDatabase | None = None,
    server_url: str | None = None,
) -> dict:
    base_url = await _resolve_server_url(db, server_url)
    url = f"{base_url}{path}"
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(url, json=payload)
        try:
            body = response.json()
        except ValueError:
            body = {"success": False, "message": response.text or f"HTTP {response.status_code}"}

        if response.status_code >= 400:
            if isinstance(body, dict):
                return {
                    "success": False,
                    "message": body.get("message") or body.get("detail") or response.text,
                }
            response.raise_for_status()

        return body


async def test_appliance_via_mcp(
    host: str,
    username: str,
    password: str,
    db: AsyncIOMotorDatabase | None = None,
) -> dict:
    return await _post_mcp(
        "/test/appliance",
        {"host": host, "username": username, "password": password},
        db=db,
    )


async def get_system_info_via_mcp(
    host: str,
    username: str,
    password: str,
    db: AsyncIOMotorDatabase | None = None,
) -> dict:
    return await _post_mcp(
        "/netscaler/system-info",
        {"host": host, "username": username, "password": password},
        db=db,
    )


async def list_lb_vservers_via_mcp(
    host: str,
    username: str,
    password: str,
    db: AsyncIOMotorDatabase | None = None,
) -> dict:
    return await _post_mcp(
        "/netscaler/lb-vservers",
        {"host": host, "username": username, "password": password},
        db=db,
    )


async def generate_csr_via_mcp(
    host: str,
    username: str,
    password: str,
    params: dict,
    db: AsyncIOMotorDatabase | None = None,
) -> dict:
    payload = {
        "host": host,
        "username": username,
        "password": password,
        **params,
    }
    return await _post_mcp("/netscaler/ssl/generate-csr", payload, db=db)


async def generate_self_signed_via_mcp(
    host: str,
    username: str,
    password: str,
    params: dict,
    db: AsyncIOMotorDatabase | None = None,
) -> dict:
    payload = {
        "host": host,
        "username": username,
        "password": password,
        **params,
    }
    return await _post_mcp("/netscaler/ssl/generate-self-signed", payload, db=db)


async def list_mcp_tools(db: AsyncIOMotorDatabase | None = None) -> dict:
    base_url = await _resolve_server_url(db)
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(f"{base_url}/tools")
        response.raise_for_status()
        return response.json()


async def call_mcp_tool(
    name: str,
    arguments: dict,
    db: AsyncIOMotorDatabase | None = None,
) -> str:
    import json

    result = await _post_mcp("/tools/call", {"name": name, "arguments": arguments}, db=db)
    if not result.get("success"):
        return json.dumps(
            {"success": False, "message": result.get("message", "Tool call failed")},
            indent=2,
        )
    return result.get("result", "")
