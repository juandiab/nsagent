import json
from typing import Any

import httpx

from app.services.ai_provider_service import build_openai_compatible_headers, resolve_base_url
from app.services.mcp_client import call_mcp_tool as invoke_mcp_tool


COPILOT_TOOLS = [
    {
        "name": "netscaler_list_inventory",
        "description": "List NetScaler appliances in the platform inventory (name, environment, enabled status).",
        "parameters": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "netscaler_test_connection",
        "description": "Test Next-Gen API connectivity to a NetScaler appliance by inventory name.",
        "parameters": {
            "type": "object",
            "properties": {
                "appliance_name": {
                    "type": "string",
                    "description": "Inventory name of the NetScaler appliance",
                }
            },
            "required": ["appliance_name"],
        },
    },
    {
        "name": "netscaler_get_system_info",
        "description": (
            "Get appliance management IP, firmware version, hostname, serial, and Next-Gen application count "
            "by inventory name. Use for firmware, version, IP address, or appliance identity."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "appliance_name": {
                    "type": "string",
                    "description": "Inventory name of the NetScaler appliance",
                }
            },
            "required": ["appliance_name"],
        },
    },
    {
        "name": "netscaler_list_applications",
        "description": "List Next-Gen API applications only (application-centric configs).",
        "parameters": {
            "type": "object",
            "properties": {
                "appliance_name": {
                    "type": "string",
                    "description": "Inventory name of the NetScaler appliance",
                }
            },
            "required": ["appliance_name"],
        },
    },
    {
        "name": "netscaler_list_virtual_servers",
        "description": (
            "List all load-balancing virtual servers: Next-Gen applications plus classic NITRO lbvserver. "
            "Use for 'show virtual servers', 'show lb vserver', or listing VIPs/vservers on the appliance."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "appliance_name": {
                    "type": "string",
                    "description": "Inventory name of the NetScaler appliance",
                }
            },
            "required": ["appliance_name"],
        },
    },
    {
        "name": "netscaler_list_virtual_ips",
        "description": (
            "List load-balancing virtual IPs from Next-Gen API applications. "
            "Use netscaler_list_ip_addresses when the user asks for all IPs (NSIP, SNIP, VIP)."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "appliance_name": {
                    "type": "string",
                    "description": "Inventory name of the NetScaler appliance",
                }
            },
            "required": ["appliance_name"],
        },
    },
    {
        "name": "netscaler_list_ip_addresses",
        "description": (
            "List all IP addresses on the appliance: NSIP (management), SNIP, VIP, servers, "
            "and application IPs. Uses Next-Gen API first (applications, config_sets), "
            "then read-only NITRO for classic configuration. "
            "Use for 'list all IPs', 'show ns ip', or any request covering every address on the box."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "appliance_name": {
                    "type": "string",
                    "description": "Inventory name of the NetScaler appliance",
                }
            },
            "required": ["appliance_name"],
        },
    },
    {
        "name": "netscaler_nextgen_get",
        "description": (
            "Read-only GET against a NetScaler Next-Gen API path on an appliance "
            "(e.g. applications, applications/{name}). Use after searching the official guide."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "appliance_name": {
                    "type": "string",
                    "description": "Inventory name of the NetScaler appliance",
                },
                "path": {
                    "type": "string",
                    "description": "Resource path relative to /mgmt/api/nextgen/v1/ (no leading slash)",
                },
            },
            "required": ["appliance_name", "path"],
        },
    },
    {
        "name": "netscaler_create_application",
        "description": (
            "Create a NetScaler Next-Gen application via POST /applications. "
            "Use after search_netscaler_nextgen_api confirms AddApplication payload from memory file. "
            "Not for classic add lb vserver — this is the Next-Gen application-centric API."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "appliance_name": {
                    "type": "string",
                    "description": "Inventory name of the NetScaler appliance",
                },
                "name": {"type": "string", "description": "Application name"},
                "virtual_ip": {"type": "string", "description": "Frontend VIP"},
                "port": {"type": "integer", "description": "Frontend port (default 80)"},
                "protocol": {
                    "type": "string",
                    "description": "Frontend protocol: HTTP, HTTPS, TCP, etc.",
                },
                "servers": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Backend server IP addresses",
                },
                "servers_port": {"type": "integer", "description": "Backend port"},
                "servers_protocol": {"type": "string", "description": "Backend protocol"},
            },
            "required": ["appliance_name", "name", "virtual_ip", "servers"],
        },
    },
    {
        "name": "netscaler_add_ip_address",
        "description": (
            "Add a classic NetScaler IP (VIP, SNIP, or NSIP) on the appliance. "
            "Equivalent to: add ns ip <ip> <netmask> -type VIP. "
            "Use after search_netscaler_cli_reference confirms syntax from netscaler_adc_cli_memory.md."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "appliance_name": {
                    "type": "string",
                    "description": "Inventory name of the NetScaler appliance",
                },
                "ip_address": {
                    "type": "string",
                    "description": "IPv4 address to add, e.g. 192.168.20.224",
                },
                "ip_type": {
                    "type": "string",
                    "description": "VIP, SNIP, NSIP, MIP, or GSLBsiteIP",
                    "enum": ["VIP", "SNIP", "NSIP", "MIP", "GSLBsiteIP"],
                },
                "netmask": {
                    "type": "string",
                    "description": "Subnet mask (default 255.255.255.0)",
                },
                "save_config": {
                    "type": "boolean",
                    "description": "Persist with save ns config after add (default true)",
                },
            },
            "required": ["appliance_name", "ip_address", "ip_type"],
        },
    },
    {
        "name": "netscaler_ssh_run_command",
        "description": (
            "Run a read-only NetScaler CLI command via SSH (show/stat/get only). "
            "Use only after search_netscaler_cli_reference returns a recommendedCommands entry "
            "and only run that exact command (or documented alias). "
            "If success is false, read retryHint/suggestedCommand and retry — do not answer the user yet."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "appliance_name": {
                    "type": "string",
                    "description": "Inventory name of the NetScaler appliance",
                },
                "command": {
                    "type": "string",
                    "description": "Read-only CLI command, e.g. show ns version",
                },
                "purpose": {
                    "type": "string",
                    "description": "Why this command is needed to answer the user's question",
                },
            },
            "required": ["appliance_name", "command", "purpose"],
        },
    },
    {
        "name": "netscaler_run_cli_command",
        "description": (
            "Run ANY NetScaler classic CLI command via SSH — including configuration writes "
            "(add, set, bind, unbind, enable, disable, rm, clear, save, ...) plus show/stat/get. "
            "Use ONLY after search_netscaler_cli_reference confirms the exact syntax from "
            "netscaler_adc_cli_memory.md — never invent CLI syntax. "
            "Run 'save ns config' afterwards to persist classic configuration. "
            "Destructive commands (rm, clear, delete, reboot, shutdown, disable, unbind, flush, reset, "
            "unset, kill, force) are blocked until the user has agreed and you pass confirmed=true. "
            "If success is false, read retryHint/suggestedCommand and fix before answering."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "appliance_name": {
                    "type": "string",
                    "description": "Inventory name of the NetScaler appliance",
                },
                "command": {
                    "type": "string",
                    "description": "CLI command, e.g. add lb vserver web_vs HTTP 10.0.0.10 80",
                },
                "purpose": {
                    "type": "string",
                    "description": "Why this command is needed to fulfill the user's request",
                },
                "confirmed": {
                    "type": "boolean",
                    "description": "Set true ONLY after the user explicitly confirmed a destructive command",
                },
            },
            "required": ["appliance_name", "command", "purpose"],
        },
    },
    {
        "name": "netscaler_run_cli_commands",
        "description": (
            "Run a sequence of NetScaler classic CLI commands via SSH in order — preferred for multi-step "
            "LB setup (add lb vserver, add serviceGroup, bind serviceGroup, bind lb vserver, save ns config). "
            "Use ONLY after search_netscaler_cli_reference confirms exact syntax. "
            "Stops on first failure; read results[] for each command output. "
            "Destructive commands in the list require confirmed=true."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "appliance_name": {
                    "type": "string",
                    "description": "Inventory name of the NetScaler appliance",
                },
                "commands": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "CLI commands in execution order",
                },
                "purpose": {
                    "type": "string",
                    "description": "Why this sequence fulfills the user's request",
                },
                "confirmed": {
                    "type": "boolean",
                    "description": "Set true ONLY after the user explicitly confirmed a destructive command in the list",
                },
            },
            "required": ["appliance_name", "commands", "purpose"],
        },
    },
    {
        "name": "netscaler_nextgen_request",
        "description": (
            "Perform any NetScaler Next-Gen API request (GET, POST, PUT, DELETE) against a path "
            "relative to /mgmt/api/nextgen/v1/, with an optional JSON body. "
            "Use for creating/updating/deleting applications, certificates, routes, config_sets, etc. "
            "Use ONLY after search_netscaler_nextgen_api confirms the endpoint and payload from "
            "netscaler_nextgen_api_memory.md. "
            "DELETE requests and disable/uninstall actions are blocked until the user has agreed and "
            "you pass confirmed=true."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "appliance_name": {
                    "type": "string",
                    "description": "Inventory name of the NetScaler appliance",
                },
                "method": {
                    "type": "string",
                    "description": "HTTP method",
                    "enum": ["GET", "POST", "PUT", "DELETE"],
                },
                "path": {
                    "type": "string",
                    "description": "Path without the /mgmt/api/nextgen/v1 prefix, e.g. applications/app1",
                },
                "body": {
                    "type": "object",
                    "description": "JSON body for POST/PUT (omit for GET/DELETE)",
                },
                "confirmed": {
                    "type": "boolean",
                    "description": "Set true ONLY after the user explicitly confirmed a destructive request",
                },
            },
            "required": ["appliance_name", "method", "path"],
        },
    },
]

SEARCH_TOOL = {
    "name": "search_netscaler_nextgen_api",
    "description": (
        "REQUIRED before any Next-Gen API tool call. Searches the authoritative "
        "netscaler_nextgen_api_memory.md file plus official API reference. "
        "Read memoryExcerpts and suggestedGetPaths and follow them exactly."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Focused search query about NetScaler Next-Gen API usage or endpoints",
            }
        },
        "required": ["query"],
    },
}

CLI_SEARCH_TOOL = {
    "name": "search_netscaler_cli_reference",
    "description": (
        "REQUIRED before netscaler_run_cli_command or netscaler_run_cli_commands. "
        "Searches netscaler_adc_cli_memory.md plus the official ADC CLI reference. "
        "Read memoryExcerpts and recommendedCommands and run the exact command(s) — never invent CLI syntax."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "CLI command or topic to look up, e.g. show ns version or virtual server",
            }
        },
        "required": ["query"],
    },
}

MCP_TOOL_MAP = {
    "netscaler_test_connection": "netscaler_test_connection",
    "netscaler_get_system_info": "netscaler_get_system_info",
    "netscaler_list_applications": "netscaler_list_applications",
    "netscaler_list_virtual_servers": "netscaler_list_virtual_servers",
    "netscaler_list_virtual_ips": "netscaler_list_virtual_ips",
    "netscaler_list_ip_addresses": "netscaler_list_ip_addresses",
    "netscaler_nextgen_get": "netscaler_nextgen_get",
    "netscaler_create_application": "netscaler_create_application",
    "netscaler_add_ip_address": "netscaler_add_ip_address",
    "netscaler_ssh_run_command": "netscaler_ssh_run_command",
    "netscaler_run_cli_command": "netscaler_run_cli_command",
    "netscaler_run_cli_commands": "netscaler_run_cli_commands",
    "netscaler_nextgen_request": "netscaler_nextgen_request",
    "netscaler_list_lb_vservers": "netscaler_list_virtual_servers",
}


async def resolve_appliance_credentials(db, appliance_name: str) -> tuple[str, str, str]:
    appliance = await db.appliances.find_one({"name": appliance_name})
    if appliance is None:
        raise ValueError(f"Appliance '{appliance_name}' not found in inventory")

    from app.services.encryption_service import decrypt_value

    return (
        decrypt_value(appliance["encryptedHost"]),
        decrypt_value(appliance["encryptedUsername"]),
        decrypt_value(appliance["encryptedPassword"]),
    )


async def execute_copilot_tool(
    db,
    name: str,
    arguments: dict[str, Any],
    default_appliance_name: str | None = None,
) -> str:
    if name == "search_netscaler_nextgen_api":
        from app.services.nextgen_docs_service import search_nextgen_guide

        query = arguments.get("query", "").strip()
        if not query:
            raise ValueError("query is required")

        guide_matches = await search_nextgen_guide(query)
        return json.dumps(
            {
                "guideMatches": guide_matches,
                "officialDocsOnly": True,
                "allowedDomains": [
                    "developer-docs.netscaler.com",
                    "docs.citrix.com",
                    "docs.netscaler.com",
                ],
            },
            indent=2,
        )

    if name == "search_netscaler_cli_reference":
        from app.services.cli_reference_service import search_cli_reference

        query = arguments.get("query", "").strip()
        if not query:
            raise ValueError("query is required")
        return json.dumps(await search_cli_reference(query), indent=2)

    if name == "netscaler_list_inventory":
        appliances = await db.appliances.find().sort("name", 1).to_list(length=None)
        items = [
            {
                "name": item["name"],
                "environment": item["environment"],
                "enabled": item.get("enabled", True),
            }
            for item in appliances
        ]
        return json.dumps(items, indent=2)

    appliance_name = arguments.get("appliance_name", "") or (default_appliance_name or "")
    if name in MCP_TOOL_MAP:
        if not appliance_name:
            raise ValueError("appliance_name is required")
        arguments = {**arguments, "appliance_name": appliance_name}

    host, username, password = await resolve_appliance_credentials(db, appliance_name)
    mcp_tool = MCP_TOOL_MAP.get(name)
    if not mcp_tool:
        raise ValueError(f"Unknown tool: {name}")

    mcp_args: dict[str, Any] = {"host": host, "username": username, "password": password}
    if name == "netscaler_nextgen_get":
        path = arguments.get("path", "").strip().lstrip("/")
        if not path:
            raise ValueError("path is required")
        mcp_args["path"] = path

        from app.services.nextgen_memory_service import suggest_path_for_nextgen_get

        path_hint = suggest_path_for_nextgen_get(path)
        result = await invoke_mcp_tool(mcp_tool, mcp_args, db=db)
        if path_hint:
            payload = json.loads(result) if result.strip().startswith("{") else {"data": result}
            if isinstance(payload, dict):
                payload["memoryPathGuidance"] = path_hint
                return json.dumps(payload, indent=2, default=str)
        return result

    if name in ("netscaler_ssh_run_command", "netscaler_run_cli_command"):
        command = arguments.get("command", "").strip()
        purpose = arguments.get("purpose", "").strip()
        if not command:
            raise ValueError("command is required")
        if not purpose:
            raise ValueError("purpose is required")
        mcp_args["command"] = command
        mcp_args["purpose"] = purpose

    if name == "netscaler_run_cli_commands":
        commands = arguments.get("commands") or []
        purpose = arguments.get("purpose", "").strip()
        if not commands:
            raise ValueError("commands is required")
        if not purpose:
            raise ValueError("purpose is required")
        mcp_args["commands"] = commands
        mcp_args["purpose"] = purpose

    if name == "netscaler_nextgen_request":
        method = arguments.get("method", "GET").strip().upper()
        path = arguments.get("path", "").strip().lstrip("/")
        if not path:
            raise ValueError("path is required")
        mcp_args["method"] = method
        mcp_args["path"] = path
        body = arguments.get("body")
        if body is not None:
            mcp_args["body"] = body

    if name == "netscaler_add_ip_address":
        ip_address = arguments.get("ip_address", "").strip()
        ip_type = arguments.get("ip_type", "VIP").strip()
        if not ip_address:
            raise ValueError("ip_address is required")
        if not ip_type:
            raise ValueError("ip_type is required")
        mcp_args["ip_address"] = ip_address
        mcp_args["ip_type"] = ip_type
        if arguments.get("netmask"):
            mcp_args["netmask"] = arguments["netmask"].strip()
        if "save_config" in arguments:
            mcp_args["save_config"] = arguments["save_config"]

    if name == "netscaler_create_application":
        app_name = arguments.get("name", "").strip()
        virtual_ip = arguments.get("virtual_ip", "").strip()
        servers = arguments.get("servers") or []
        if not app_name:
            raise ValueError("name is required")
        if not virtual_ip:
            raise ValueError("virtual_ip is required")
        if not servers:
            raise ValueError("servers is required")
        mcp_args["name"] = app_name
        mcp_args["virtual_ip"] = virtual_ip
        mcp_args["port"] = int(arguments.get("port", 80))
        mcp_args["protocol"] = arguments.get("protocol", "HTTP").strip()
        mcp_args["servers"] = servers
        if arguments.get("servers_port") is not None:
            mcp_args["servers_port"] = int(arguments["servers_port"])
        if arguments.get("servers_protocol"):
            mcp_args["servers_protocol"] = arguments["servers_protocol"].strip()

    return await invoke_mcp_tool(mcp_tool, mcp_args, db=db)


async def get_enabled_copilot_tools(db) -> list[dict[str, Any]]:
    from app.services.mcp_config_service import get_mcp_settings

    settings = await get_mcp_settings(db)
    enabled = set(settings.enabledTools)
    tools = [
        tool
        for tool in COPILOT_TOOLS
        if tool["name"] == "netscaler_list_inventory" or tool["name"] in enabled
    ]
    tools.append(SEARCH_TOOL)
    tools.append(CLI_SEARCH_TOOL)
    return tools


def to_openai_tools(tools: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    source = tools or COPILOT_TOOLS
    return [
        {
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool["description"],
                "parameters": tool["parameters"],
            },
        }
        for tool in source
    ]


def to_anthropic_tools(tools: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    source = tools or COPILOT_TOOLS
    return [
        {
            "name": tool["name"],
            "description": tool["description"],
            "input_schema": tool["parameters"],
        }
        for tool in source
    ]


async def _chat_openai_at_base(
    *,
    base_url: str,
    api_key: str,
    model: str,
    messages: list[dict[str, Any]],
    tools: list[dict[str, Any]],
) -> dict[str, Any]:
    url = f"{base_url.rstrip('/')}/chat/completions"
    headers = build_openai_compatible_headers(api_key)
    headers["Content-Type"] = "application/json"
    payload = {"model": model, "messages": messages, "tools": tools, "tool_choice": "auto"}

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(url, json=payload, headers=headers)
        if response.status_code >= 400:
            raise ValueError(response.text)
        return response.json()


def _should_try_next_openai_base(error_message: str) -> bool:
    lowered = error_message.lower()
    return any(
        phrase in lowered
        for phrase in (
            "unexpected endpoint",
            "not found",
            "connection refused",
            "connection timed out",
            "404",
        )
    )


def _openai_base_candidates(base_url: str, base_url_candidates: list[str] | None) -> list[str]:
    if base_url_candidates:
        ordered: list[str] = []
        for url in base_url_candidates:
            cleaned = url.rstrip("/")
            if cleaned not in ordered:
                ordered.append(cleaned)
        return ordered
    return [base_url.rstrip("/")]


async def chat_openai_compatible(
    *,
    base_url: str,
    api_key: str,
    model: str,
    messages: list[dict[str, Any]],
    tools: list[dict[str, Any]],
    base_url_candidates: list[str] | None = None,
) -> tuple[dict[str, Any], str]:
    candidates = _openai_base_candidates(base_url, base_url_candidates)

    errors: list[str] = []
    for candidate in candidates:
        try:
            data = await _chat_openai_at_base(
                base_url=candidate,
                api_key=api_key,
                model=model,
                messages=messages,
                tools=tools,
            )
            return data, candidate
        except httpx.ConnectError as exc:
            errors.append(f"{candidate}: connection failed ({exc})")
            continue
        except httpx.TimeoutException:
            errors.append(f"{candidate}: timed out")
            continue
        except ValueError as exc:
            message = str(exc)
            errors.append(f"{candidate}: {message}")
            if _should_try_next_openai_base(message):
                continue
            raise

    raise ValueError("Could not reach OpenAI-compatible API. " + " | ".join(errors))


async def chat_anthropic(
    *,
    api_key: str,
    model: str,
    system: str,
    messages: list[dict[str, Any]],
    tools: list[dict[str, Any]],
) -> dict[str, Any]:
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "max_tokens": 4096,
        "system": system,
        "messages": messages,
        "tools": tools,
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(url, json=payload, headers=headers)
        if response.status_code >= 400:
            raise ValueError(response.text)
        return response.json()


def to_gemini_tools(tools: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    source = tools or COPILOT_TOOLS
    return [
        {
            "functionDeclarations": [
                {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["parameters"],
                }
                for tool in source
            ]
        }
    ]


def _normalize_gemini_model(model: str) -> str:
    return model.replace("models/", "")


async def chat_gemini(
    *,
    api_key: str,
    model: str,
    system: str,
    contents: list[dict[str, Any]],
    tools: list[dict[str, Any]],
) -> dict[str, Any]:
    model_id = _normalize_gemini_model(model)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_id}:generateContent"
    payload: dict[str, Any] = {
        "systemInstruction": {"parts": [{"text": system}]},
        "contents": contents,
        "tools": tools,
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(url, params={"key": api_key}, json=payload)
        if response.status_code >= 400:
            raise ValueError(response.text)
        return response.json()
