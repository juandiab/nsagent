from mcp.server import Server
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.routing import Mount, Route
from starlette.responses import JSONResponse

from app.services.config_service import serialize_runtime_config, update_runtime_config
from app.services.netscaler_service import (
    generate_ssl_csr,
    generate_ssl_self_signed,
    get_system_info,
    list_lb_vservers,
    test_appliance_connection,
)
from app.tools.netscaler_tools import NETSCALER_TOOLS, call_netscaler_tool, get_enabled_tools

mcp_app = Server("netscaler-copilot")
sse = SseServerTransport("/messages")


@mcp_app.list_tools()
async def handle_list_tools():
    return get_enabled_tools()


@mcp_app.call_tool()
async def handle_call_tool(name: str, arguments: dict):
    return await call_netscaler_tool(name, arguments)


async def handle_sse(request):
    async with sse.connect_sse(
        request.scope, request.receive, request._send
    ) as streams:
        await mcp_app.run(
            streams[0], streams[1], mcp_app.create_initialization_options()
        )


async def health(request):
    config = serialize_runtime_config()
    return JSONResponse(
        {
            "status": "ok",
            "serverName": config["serverName"],
            "enabledTools": config["enabledTools"],
        }
    )


async def get_config(request):
    return JSONResponse(serialize_runtime_config())


async def put_config(request: Request):
    payload = await request.json()
    config = update_runtime_config(payload)
    return JSONResponse(
        {
            "serverName": config.server_name,
            "nitroTimeoutSeconds": config.nitro_timeout_seconds,
            "verifySsl": config.verify_ssl,
            "enabledTools": config.enabled_tools,
            "sseEnabled": config.sse_enabled,
            "sshFallbackEnabled": config.ssh_fallback_enabled,
            "sshPort": config.ssh_port,
            "sshTimeoutSeconds": config.ssh_timeout_seconds,
        }
    )


async def list_tools(request):
    tools = [
        {
            "name": tool.name,
            "description": tool.description,
            "inputSchema": tool.inputSchema,
        }
        for tool in get_enabled_tools()
    ]
    return JSONResponse({"tools": tools})


async def invoke_tool(request: Request):
    payload = await request.json()
    name = payload.get("name", "")
    arguments = payload.get("arguments", {})
    try:
        result = await call_netscaler_tool(name, arguments)
        return JSONResponse({"success": True, "result": result[0].text if result else ""})
    except Exception as exc:
        return JSONResponse({"success": False, "message": str(exc)})


async def test_appliance(request: Request):
    payload = await request.json()
    success, message = await test_appliance_connection(
        payload.get("host", ""),
        payload.get("username", ""),
        payload.get("password", ""),
    )
    return JSONResponse({"success": success, "message": message})


async def appliance_system_info(request: Request):
    payload = await request.json()
    try:
        info = await get_system_info(
            payload.get("host", ""),
            payload.get("username", ""),
            payload.get("password", ""),
        )
        return JSONResponse({"success": True, "data": info})
    except Exception as exc:
        return JSONResponse({"success": False, "message": str(exc)})


async def appliance_lb_vservers(request: Request):
    payload = await request.json()
    try:
        vservers = await list_lb_vservers(
            payload.get("host", ""),
            payload.get("username", ""),
            payload.get("password", ""),
        )
        return JSONResponse({"success": True, "data": vservers})
    except Exception as exc:
        return JSONResponse({"success": False, "message": str(exc)})


async def appliance_generate_csr(request: Request):
    payload = await request.json()
    try:
        params = _ssl_params_from_payload(payload)
        result = await generate_ssl_csr(
            payload.get("host", ""),
            payload.get("username", ""),
            payload.get("password", ""),
            params,
        )
        return JSONResponse({"success": True, "data": result})
    except Exception as exc:
        return JSONResponse({"success": False, "message": str(exc)})


def _ssl_params_from_payload(payload: dict) -> dict:
    return {
        "key_name": payload.get("key_name", ""),
        "cert_type": payload.get("cert_type", ""),
        "key_type": payload.get("key_type", "rsa"),
        "key_size": payload.get("key_size", 2048),
        "key_password": payload.get("key_password"),
        "common_name": payload.get("common_name", ""),
        "country": payload.get("country", "US"),
        "state": payload.get("state", ""),
        "locality": payload.get("locality", ""),
        "organization": payload.get("organization", ""),
        "organizational_unit": payload.get("organizational_unit", ""),
        "email": payload.get("email"),
        "subject_alt_names": payload.get("subject_alt_names") or [],
        "validity_days": payload.get("validity_days", 365),
    }


async def appliance_generate_self_signed(request: Request):
    payload = await request.json()
    try:
        params = _ssl_params_from_payload(payload)
        result = await generate_ssl_self_signed(
            payload.get("host", ""),
            payload.get("username", ""),
            payload.get("password", ""),
            params,
        )
        return JSONResponse({"success": True, "data": result})
    except Exception as exc:
        return JSONResponse({"success": False, "message": str(exc)})


app = Starlette(
    routes=[
        Route("/health", endpoint=health),
        Route("/config", endpoint=get_config),
        Route("/config", endpoint=put_config, methods=["PUT"]),
        Route("/tools", endpoint=list_tools),
        Route("/tools/call", endpoint=invoke_tool, methods=["POST"]),
        Route("/test/appliance", endpoint=test_appliance, methods=["POST"]),
        Route("/netscaler/system-info", endpoint=appliance_system_info, methods=["POST"]),
        Route("/netscaler/lb-vservers", endpoint=appliance_lb_vservers, methods=["POST"]),
        Route("/netscaler/ssl/generate-csr", endpoint=appliance_generate_csr, methods=["POST"]),
        Route("/netscaler/ssl/generate-self-signed", endpoint=appliance_generate_self_signed, methods=["POST"]),
        Route("/sse", endpoint=handle_sse),
        Mount("/messages", app=sse.handle_post_message),
    ]
)
