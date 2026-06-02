import json

import httpx
import mcp.types as types

from app.services.netscaler_service import (
    add_ip_address,
    create_application,
    format_tool_result,
    get_system_info,
    list_applications,
    list_ip_addresses,
    list_virtual_ips,
    list_virtual_servers,
    nextgen_get,
    nextgen_request,
    run_cli_command,
    run_cli_commands,
    run_diagnostic,
    generate_ssl_csr,
    generate_ssl_self_signed,
    run_nsconmsg,
    run_telnet,
    ssh_run_command,
    test_appliance_connection,
)

NETSCALER_TOOLS = [
    types.Tool(
        name="netscaler_test_connection",
        description="Test connectivity and authentication to a NetScaler appliance via the Next-Gen API.",
        inputSchema={
            "type": "object",
            "properties": {
                "host": {"type": "string", "description": "NetScaler hostname or IP (HTTPS port 443)"},
                "username": {"type": "string", "description": "NetScaler API username"},
                "password": {"type": "string", "description": "NetScaler API password"},
            },
            "required": ["host", "username", "password"],
        },
    ),
    types.Tool(
        name="netscaler_get_system_info",
        description=(
            "Retrieve appliance summary via NetScaler Next-Gen API: management IP, firmware version, "
            "hostname, serial, and application count."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "host": {"type": "string", "description": "NetScaler hostname or IP"},
                "username": {"type": "string", "description": "NetScaler API username"},
                "password": {"type": "string", "description": "NetScaler API password"},
            },
            "required": ["host", "username", "password"],
        },
    ),
    types.Tool(
        name="netscaler_list_applications",
        description="List NetScaler Next-Gen API applications (application-centric load balancing configs).",
        inputSchema={
            "type": "object",
            "properties": {
                "host": {"type": "string", "description": "NetScaler hostname or IP"},
                "username": {"type": "string", "description": "NetScaler API username"},
                "password": {"type": "string", "description": "NetScaler API password"},
            },
            "required": ["host", "username", "password"],
        },
    ),
    types.Tool(
        name="netscaler_list_virtual_ips",
        description=(
            "List load-balancing virtual IPs from Next-Gen API applications. "
            "Not for appliance management IP — use netscaler_list_ip_addresses for all IPs."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "host": {"type": "string", "description": "NetScaler hostname or IP"},
                "username": {"type": "string", "description": "NetScaler API username"},
                "password": {"type": "string", "description": "NetScaler API password"},
            },
            "required": ["host", "username", "password"],
        },
    ),
    types.Tool(
        name="netscaler_list_ip_addresses",
        description=(
            "List all IP addresses on the appliance: NSIP, SNIP, VIP, servers, and application IPs. "
            "Uses Next-Gen API (applications, config_sets) plus read-only NITRO for classic config."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "host": {"type": "string", "description": "NetScaler hostname or IP"},
                "username": {"type": "string", "description": "NetScaler API username"},
                "password": {"type": "string", "description": "NetScaler API password"},
            },
            "required": ["host", "username", "password"],
        },
    ),
    types.Tool(
        name="netscaler_nextgen_get",
        description=(
            "Perform a read-only GET against a NetScaler Next-Gen API path "
            "(e.g. applications, applications/{name}). Path is relative to /mgmt/api/nextgen/v1/."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "host": {"type": "string", "description": "NetScaler hostname or IP"},
                "username": {"type": "string", "description": "NetScaler API username"},
                "password": {"type": "string", "description": "NetScaler API password"},
                "path": {
                    "type": "string",
                    "description": "Next-Gen API resource path without the /mgmt/api/nextgen/v1 prefix",
                },
            },
            "required": ["host", "username", "password", "path"],
        },
    ),
    types.Tool(
        name="netscaler_list_virtual_servers",
        description=(
            "List load-balancing virtual servers from Next-Gen applications plus classic NITRO lbvserver. "
            "Use for 'show virtual servers', 'show lb vserver', or any VIP/vserver listing request."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "host": {"type": "string", "description": "NetScaler hostname or IP"},
                "username": {"type": "string", "description": "NetScaler API username"},
                "password": {"type": "string", "description": "NetScaler API password"},
            },
            "required": ["host", "username", "password"],
        },
    ),
    types.Tool(
        name="netscaler_create_application",
        description=(
            "Create a NetScaler Next-Gen application (POST /applications). "
            "Defines VIP, frontend protocol/port, and backend server pool."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "host": {"type": "string", "description": "NetScaler hostname or IP"},
                "username": {"type": "string", "description": "NetScaler API username"},
                "password": {"type": "string", "description": "NetScaler API password"},
                "name": {"type": "string", "description": "Application name, e.g. app_2"},
                "virtual_ip": {"type": "string", "description": "Frontend VIP address"},
                "port": {"type": "integer", "description": "Frontend port (default 80)"},
                "protocol": {
                    "type": "string",
                    "description": "Frontend protocol: HTTP, HTTPS, TCP, etc. (default HTTP)",
                },
                "servers": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Backend server IP addresses",
                },
                "servers_port": {
                    "type": "integer",
                    "description": "Backend port (defaults to frontend port)",
                },
                "servers_protocol": {
                    "type": "string",
                    "description": "Backend protocol (defaults to frontend protocol)",
                },
            },
            "required": ["host", "username", "password", "name", "virtual_ip", "servers"],
        },
    ),
    types.Tool(
        name="netscaler_add_ip_address",
        description=(
            "Add a classic NetScaler IP address (NSIP, SNIP, or VIP) via NITRO — "
            "equivalent to: add ns ip <ip> <netmask> -type VIP|SNIP|NSIP. "
            "Persists running config with save ns config when save_config is true."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "host": {"type": "string", "description": "NetScaler hostname or IP"},
                "username": {"type": "string", "description": "NetScaler API username"},
                "password": {"type": "string", "description": "NetScaler API password"},
                "ip_address": {"type": "string", "description": "IPv4 address to add"},
                "ip_type": {
                    "type": "string",
                    "description": "Address type: VIP, SNIP, NSIP, MIP, or GSLBsiteIP",
                    "enum": ["VIP", "SNIP", "NSIP", "MIP", "GSLBsiteIP"],
                },
                "netmask": {
                    "type": "string",
                    "description": "Subnet mask (default 255.255.255.0)",
                },
                "save_config": {
                    "type": "boolean",
                    "description": "Run save ns config after add (default true)",
                },
            },
            "required": ["host", "username", "password", "ip_address", "ip_type"],
        },
    ),
    types.Tool(
        name="netscaler_ssh_run_command",
        description=(
            "Run a read-only NetScaler CLI command via SSH (show/stat/get) or a connectivity "
            "troubleshooting command (ping, ping6, traceroute, traceroute6). ping is automatically "
            "bounded with a packet count so it cannot run indefinitely. "
            "Use after confirming the command in the ADC CLI reference."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "host": {"type": "string", "description": "NetScaler hostname or IP"},
                "username": {"type": "string", "description": "NetScaler SSH username"},
                "password": {"type": "string", "description": "NetScaler SSH password"},
                "command": {
                    "type": "string",
                    "description": "Read-only or diagnostic command, e.g. show ns version, ping -c 4 10.0.0.5, traceroute 10.0.0.5",
                },
                "purpose": {
                    "type": "string",
                    "description": "Why this command answers the user's question",
                },
            },
            "required": ["host", "username", "password", "command", "purpose"],
        },
    ),
    types.Tool(
        name="netscaler_run_cli_command",
        description=(
            "Run ANY NetScaler classic CLI command via SSH, including configuration writes "
            "(add, set, bind, unbind, enable, disable, rm, clear, save, ...) as well as show/stat/get. "
            "Use after confirming exact syntax in the ADC CLI reference. "
            "Run 'save ns config' afterwards to persist classic config. Dropping to the BSD shell is blocked."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "host": {"type": "string", "description": "NetScaler hostname or IP"},
                "username": {"type": "string", "description": "NetScaler SSH username"},
                "password": {"type": "string", "description": "NetScaler SSH password"},
                "command": {
                    "type": "string",
                    "description": "Any CLI command, e.g. add lb vserver web_vs HTTP 10.0.0.10 80",
                },
                "purpose": {
                    "type": "string",
                    "description": "Why this command is needed to fulfill the user's request",
                },
            },
            "required": ["host", "username", "password", "command", "purpose"],
        },
    ),
    types.Tool(
        name="netscaler_run_cli_commands",
        description=(
            "Run a sequence of NetScaler classic CLI commands via SSH in order — ideal for multi-step "
            "setup (add lb vserver, add serviceGroup, bind, save ns config). Stops on first failure. "
            "Use after confirming syntax in the ADC CLI reference."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "host": {"type": "string", "description": "NetScaler hostname or IP"},
                "username": {"type": "string", "description": "NetScaler SSH username"},
                "password": {"type": "string", "description": "NetScaler SSH password"},
                "commands": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "CLI commands to run in order, e.g. add lb vserver ..., bind ..., save ns config",
                },
                "purpose": {
                    "type": "string",
                    "description": "Why this command sequence fulfills the user's request",
                },
            },
            "required": ["host", "username", "password", "commands", "purpose"],
        },
    ),
    types.Tool(
        name="netscaler_run_diagnostic",
        description=(
            "Run a bounded network diagnostic from the appliance for connectivity troubleshooting: "
            "ping, ping6, traceroute, traceroute6 (ICMP/path), or tcp_port (TCP port via telnet). "
            "Use tcp_port for 'is port N open' or host:PORT reachability. Read-only and safe."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "host": {"type": "string", "description": "NetScaler hostname or IP"},
                "username": {"type": "string", "description": "NetScaler SSH username"},
                "password": {"type": "string", "description": "NetScaler SSH password"},
                "operation": {
                    "type": "string",
                    "description": "Diagnostic to run",
                    "enum": ["ping", "ping6", "traceroute", "traceroute6", "tcp_port"],
                },
                "target": {
                    "type": "string",
                    "description": "Destination host or IP to test, e.g. 8.8.8.8 or server.example.com",
                },
                "count": {
                    "type": "integer",
                    "description": "ping only: number of echo requests (default 4, max 10)",
                },
                "max_hops": {
                    "type": "integer",
                    "description": "traceroute only: maximum hops/TTL (default 15, max 20)",
                },
                "port": {
                    "type": "integer",
                    "description": "tcp_port only: TCP port to test (1-65535)",
                },
            },
            "required": ["host", "username", "password", "operation", "target"],
        },
    ),
    types.Tool(
        name="netscaler_telnet",
        description=(
            "Test TCP port connectivity from the NetScaler appliance using telnet via "
            "`shell sh -c '/usr/bin/telnet HOST PORT </dev/null'`. NetScaler ADC has telnet "
            "but not netcat/nc or GNU timeout. Returns verdict open/refused/no_response. "
            "Ignore 'ERROR: Export failed' CLI noise when telnet shows Connected to."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "host": {"type": "string", "description": "NetScaler hostname or IP"},
                "username": {"type": "string", "description": "NetScaler SSH username"},
                "password": {"type": "string", "description": "NetScaler SSH password"},
                "target": {"type": "string", "description": "Destination host or IP to test"},
                "port": {"type": "integer", "description": "TCP port to test (1-65535)"},
                "timeout_seconds": {
                    "type": "integer",
                    "description": "Connect timeout in seconds (default 8, max 20)",
                },
            },
            "required": ["host", "username", "password", "target", "port"],
        },
    ),
    types.Tool(
        name="netscaler_collect_nsconmsg",
        description=(
            "Collect performance statistics and event logs using nsconmsg (read-only). "
            "Runs /netscaler/nsconmsg -K /var/nslog/<newnslog> -d <operation> from the shell — "
            "always read-only (uppercase -K, never -k). Use for performance counters, CPU/memory "
            "stats, event logs, and historical newnslog analysis."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "host": {"type": "string", "description": "NetScaler hostname or IP"},
                "username": {"type": "string", "description": "NetScaler SSH username"},
                "password": {"type": "string", "description": "NetScaler SSH password"},
                "operation": {
                    "type": "string",
                    "description": "nsconmsg -d operation",
                    "enum": [
                        "current",
                        "stats",
                        "statswt0",
                        "event",
                        "consmsg",
                        "memstats",
                        "settime",
                        "oldconmsg",
                    ],
                },
                "logfile": {
                    "type": "string",
                    "description": "newnslog file name under /var/nslog (default newnslog, e.g. newnslog.100)",
                },
                "counter": {
                    "type": "string",
                    "description": "Optional -g pattern, e.g. cpu_use, mem_err, vsvr_tot_hits",
                },
                "vserver": {
                    "type": "string",
                    "description": "Optional -j LB vserver name (use with oldconmsg)",
                },
                "selectors": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional -s selectors: ConLB=1..3, ConMEM=1..3, disptime=1, time=ddmmmyyyy",
                },
                "interval": {
                    "type": "integer",
                    "description": "Optional -T interval in seconds",
                },
            },
            "required": ["host", "username", "password", "operation"],
        },
    ),
    types.Tool(
        name="netscaler_generate_csr",
        description=(
            "Generate an SSL private key and either a CSR (OpenSSL) or a self-signed certificate "
            "(NetScaler classic CLI) under /nsconfig/ssl. Returns PEM output for copy/paste or local use."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "host": {"type": "string", "description": "NetScaler hostname or IP"},
                "username": {"type": "string", "description": "NetScaler SSH username"},
                "password": {"type": "string", "description": "NetScaler SSH password"},
                "key_name": {"type": "string", "description": "Base name for key/CSR files (no path)"},
                "generation_mode": {
                    "type": "string",
                    "enum": ["csr", "self_signed"],
                    "description": "csr = signing request for a CA; self_signed = NetScaler ROOT_CERT",
                },
                "validity_days": {
                    "type": "integer",
                    "description": "Self-signed certificate validity in days (default 365)",
                },
                "cert_type": {
                    "type": "string",
                    "enum": ["standard", "wildcard", "san"],
                    "description": "Certificate type",
                },
                "key_type": {
                    "type": "string",
                    "enum": ["rsa", "ecdsa"],
                    "description": "Private key algorithm",
                },
                "key_size": {
                    "type": "integer",
                    "description": "RSA key size (2048, 3072, or 4096)",
                },
                "key_password": {
                    "type": "string",
                    "description": "Optional password to encrypt the private key",
                },
                "common_name": {"type": "string", "description": "Certificate common name (CN)"},
                "country": {"type": "string", "description": "Country code (C), e.g. US"},
                "state": {"type": "string", "description": "State or province (ST)"},
                "locality": {"type": "string", "description": "City or locality (L)"},
                "organization": {"type": "string", "description": "Organization (O)"},
                "organizational_unit": {"type": "string", "description": "Organizational unit (OU)"},
                "email": {"type": "string", "description": "Email address"},
                "subject_alt_names": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "DNS names or IPs for SAN certificates",
                },
            },
            "required": ["host", "username", "password", "key_name", "cert_type", "common_name"],
        },
    ),
    types.Tool(
        name="netscaler_nextgen_request",
        description=(
            "Perform any NetScaler Next-Gen API request (GET, POST, PUT, or DELETE) against a path "
            "relative to /mgmt/api/nextgen/v1/, with an optional JSON body. "
            "Use for creating, updating, or deleting applications, certificates, routes, config_sets, etc. "
            "Confirm the endpoint and payload against the Next-Gen API reference first."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "host": {"type": "string", "description": "NetScaler hostname or IP"},
                "username": {"type": "string", "description": "NetScaler API username"},
                "password": {"type": "string", "description": "NetScaler API password"},
                "method": {
                    "type": "string",
                    "description": "HTTP method",
                    "enum": ["GET", "POST", "PUT", "DELETE"],
                },
                "path": {
                    "type": "string",
                    "description": "Resource path without the /mgmt/api/nextgen/v1 prefix, e.g. applications/app1",
                },
                "body": {
                    "type": "object",
                    "description": "JSON request body for POST/PUT (omit for GET/DELETE)",
                },
            },
            "required": ["host", "username", "password", "method", "path"],
        },
    ),
]


def get_enabled_tools() -> list[types.Tool]:
    from app.services.config_service import is_tool_enabled

    return [tool for tool in NETSCALER_TOOLS if is_tool_enabled(tool.name)]


def _tool_error(message: str) -> list[types.TextContent]:
    return [types.TextContent(type="text", text=format_tool_result({"success": False, "message": message}))]


async def _run_nextgen_tool(action):
    try:
        data = await action()
        return [types.TextContent(type="text", text=format_tool_result(data))]
    except httpx.ConnectError:
        return _tool_error(
            "Could not connect to the appliance — check hostname/IP, HTTPS (port 443), "
            "and that Next-Gen API is enabled (`enable ns nextgenapi`)"
        )
    except httpx.TimeoutException:
        return _tool_error("Connection timed out reaching the appliance")
    except ValueError as exc:
        message = str(exc)
        if "invalid" in message.lower() or "password" in message.lower() or "authentication" in message.lower():
            return _tool_error("Authentication failed — invalid username or password")
        return _tool_error(message)
    except Exception as exc:
        return _tool_error(str(exc))


async def call_netscaler_tool(name: str, arguments: dict) -> list[types.TextContent]:
    from app.services.config_service import is_tool_enabled

    if not is_tool_enabled(name):
        raise ValueError(f"Tool '{name}' is disabled in MCP server configuration")

    host = arguments.get("host", "")
    username = arguments.get("username", "")
    password = arguments.get("password", "")

    if name == "netscaler_test_connection":
        success, message = await test_appliance_connection(host, username, password)
        payload = {"success": success, "message": message}
        return [types.TextContent(type="text", text=format_tool_result(payload))]

    if name == "netscaler_get_system_info":
        return await _run_nextgen_tool(lambda: get_system_info(host, username, password))

    if name == "netscaler_list_applications":
        return await _run_nextgen_tool(lambda: list_applications(host, username, password))

    if name == "netscaler_list_virtual_servers":
        return await _run_nextgen_tool(lambda: list_virtual_servers(host, username, password))

    if name == "netscaler_create_application":
        app_name = arguments.get("name", "").strip()
        virtual_ip = arguments.get("virtual_ip", "").strip()
        port = int(arguments.get("port", 80))
        protocol = arguments.get("protocol", "HTTP").strip()
        servers = arguments.get("servers") or []
        if not app_name:
            return _tool_error("name is required")
        if not virtual_ip:
            return _tool_error("virtual_ip is required")
        if not servers:
            return _tool_error("servers is required — at least one backend IP")
        servers_port = arguments.get("servers_port")
        servers_protocol = arguments.get("servers_protocol")
        return await _run_nextgen_tool(
            lambda: create_application(
                host,
                username,
                password,
                app_name,
                virtual_ip,
                port,
                protocol,
                servers,
                servers_port=int(servers_port) if servers_port is not None else None,
                servers_protocol=str(servers_protocol).strip() if servers_protocol else None,
            )
        )

    if name == "netscaler_list_virtual_ips":
        return await _run_nextgen_tool(lambda: list_virtual_ips(host, username, password))

    if name == "netscaler_list_ip_addresses":
        return await _run_nextgen_tool(lambda: list_ip_addresses(host, username, password))

    if name == "netscaler_nextgen_get":
        path = arguments.get("path", "").strip().lstrip("/")
        if not path:
            return _tool_error("path is required")
        return await _run_nextgen_tool(lambda: nextgen_get(host, username, password, path))

    if name == "netscaler_add_ip_address":
        ip_address = arguments.get("ip_address", "").strip()
        ip_type = arguments.get("ip_type", "VIP").strip()
        netmask = arguments.get("netmask", "255.255.255.0").strip()
        save_config = arguments.get("save_config", True)
        if not ip_address:
            return _tool_error("ip_address is required")
        if not ip_type:
            return _tool_error("ip_type is required")
        return await _run_nextgen_tool(
            lambda: add_ip_address(
                host,
                username,
                password,
                ip_address,
                ip_type,
                netmask,
                save_config=bool(save_config),
            )
        )

    if name == "netscaler_ssh_run_command":
        command = arguments.get("command", "").strip()
        purpose = arguments.get("purpose", "").strip()
        if not command:
            return _tool_error("command is required")
        if not purpose:
            return _tool_error("purpose is required — confirm why this CLI command is needed")
        return await _run_nextgen_tool(
            lambda: ssh_run_command(host, username, password, command)
        )

    if name == "netscaler_run_cli_command":
        command = arguments.get("command", "").strip()
        purpose = arguments.get("purpose", "").strip()
        if not command:
            return _tool_error("command is required")
        if not purpose:
            return _tool_error("purpose is required — confirm why this CLI command is needed")
        return await _run_nextgen_tool(
            lambda: run_cli_command(host, username, password, command)
        )

    if name == "netscaler_run_cli_commands":
        commands = arguments.get("commands") or []
        purpose = arguments.get("purpose", "").strip()
        if not commands:
            return _tool_error("commands is required — provide at least one CLI command")
        if not purpose:
            return _tool_error("purpose is required — confirm why this command sequence is needed")
        return await _run_nextgen_tool(
            lambda: run_cli_commands(host, username, password, commands)
        )

    if name == "netscaler_run_diagnostic":
        operation = arguments.get("operation", "").strip()
        target = arguments.get("target", "").strip()
        if not operation:
            return _tool_error("operation is required (ping, ping6, traceroute, traceroute6, tcp_port)")
        if not target:
            return _tool_error("target host or IP is required")
        count = arguments.get("count")
        max_hops = arguments.get("max_hops")
        port = arguments.get("port")
        if operation == "tcp_port" and port is None:
            return _tool_error("port is required for tcp_port operation (1-65535)")
        return await _run_nextgen_tool(
            lambda: run_diagnostic(
                host,
                username,
                password,
                operation,
                target,
                count=int(count) if count is not None else None,
                max_hops=int(max_hops) if max_hops is not None else None,
                port=int(port) if port is not None else None,
            )
        )

    if name == "netscaler_telnet":
        target = arguments.get("target", "").strip()
        port = arguments.get("port")
        if not target:
            return _tool_error("target host or IP is required")
        if port is None:
            return _tool_error("port is required (1-65535)")
        timeout_seconds = arguments.get("timeout_seconds")
        return await _run_nextgen_tool(
            lambda: run_telnet(
                host,
                username,
                password,
                target,
                int(port),
                timeout_seconds=int(timeout_seconds) if timeout_seconds is not None else None,
            )
        )

    if name == "netscaler_collect_nsconmsg":
        operation = arguments.get("operation", "").strip()
        if not operation:
            return _tool_error("operation is required (current, stats, event, memstats, oldconmsg, ...)")
        interval = arguments.get("interval")
        return await _run_nextgen_tool(
            lambda: run_nsconmsg(
                host,
                username,
                password,
                operation,
                logfile=(arguments.get("logfile") or "newnslog"),
                counter=arguments.get("counter"),
                vserver=arguments.get("vserver"),
                selectors=arguments.get("selectors") or [],
                interval=int(interval) if interval is not None else None,
            )
        )

    if name == "netscaler_generate_csr":
        key_name = arguments.get("key_name", "").strip()
        cert_type = arguments.get("cert_type", "").strip()
        common_name = arguments.get("common_name", "").strip()
        if not key_name:
            return _tool_error("key_name is required")
        if not cert_type:
            return _tool_error("cert_type is required (standard, wildcard, or san)")
        if not common_name:
            return _tool_error("common_name is required")
        csr_params = {
            "key_name": key_name,
            "cert_type": cert_type,
            "generation_mode": arguments.get("generation_mode", "csr"),
            "validity_days": arguments.get("validity_days", 365),
            "key_type": arguments.get("key_type", "rsa"),
            "key_size": arguments.get("key_size", 2048),
            "key_password": arguments.get("key_password"),
            "common_name": common_name,
            "country": arguments.get("country", "US"),
            "state": arguments.get("state", ""),
            "locality": arguments.get("locality", ""),
            "organization": arguments.get("organization", ""),
            "organizational_unit": arguments.get("organizational_unit", ""),
            "email": arguments.get("email"),
            "subject_alt_names": arguments.get("subject_alt_names") or [],
        }
        mode = str(arguments.get("generation_mode", "csr")).strip().lower()
        if mode == "self_signed":
            return await _run_nextgen_tool(
                lambda: generate_ssl_self_signed(host, username, password, csr_params)
            )
        return await _run_nextgen_tool(
            lambda: generate_ssl_csr(host, username, password, csr_params)
        )

    if name == "netscaler_nextgen_request":
        method = arguments.get("method", "GET").strip().upper()
        path = arguments.get("path", "").strip().lstrip("/")
        body = arguments.get("body")
        if not path:
            return _tool_error("path is required")
        if body is not None and not isinstance(body, dict):
            return _tool_error("body must be a JSON object")
        return await _run_nextgen_tool(
            lambda: nextgen_request(host, username, password, method, path, body)
        )

    raise ValueError(f"Unknown tool: {name}")
