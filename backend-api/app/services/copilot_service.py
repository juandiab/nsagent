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
            "Run a read-only NetScaler CLI command via SSH (show/stat/get) or a connectivity "
            "troubleshooting command (ping, ping6, traceroute, traceroute6). "
            "Use only after search_netscaler_cli_reference returns a recommendedCommands entry "
            "and only run that exact command (or documented alias). ping is automatically bounded "
            "with a packet count. If success is false, read retryHint/suggestedCommand and retry — "
            "do not answer the user yet."
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
                    "description": "Read-only or diagnostic command, e.g. show ns version, ping -c 4 10.0.0.5, traceroute 10.0.0.5",
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
    {
        "name": "netscaler_run_diagnostic",
        "description": (
            "Run a bounded network diagnostic from the appliance for connectivity troubleshooting: "
            "ping, ping6, traceroute, traceroute6 (ICMP/path), or tcp_port (TCP port open/closed via telnet). "
            "Use ping/traceroute for 'can the appliance reach X' with no port. "
            "Use tcp_port for 'is port N open on X' or 'can the appliance reach X:PORT'. "
            "Read-only and safe — runs immediately, no confirmation and no memory search required."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "appliance_name": {
                    "type": "string",
                    "description": "Inventory name of the NetScaler appliance",
                },
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
                    "description": "traceroute only: maximum hops (default 15, max 20)",
                },
                "port": {
                    "type": "integer",
                    "description": "tcp_port only: TCP port to test (1-65535)",
                },
            },
            "required": ["appliance_name", "operation", "target"],
        },
    },
    {
        "name": "netscaler_telnet",
        "description": (
            "Test TCP port connectivity from the NetScaler appliance (telnet via shell sh -c). "
            "Use for 'is port N open on host X', 'can the appliance reach X:PORT', or verifying "
            "a backend service/port is reachable. Does NOT use GNU timeout or netcat — uses "
            "/usr/bin/telnet on NetScaler ADC. Complements netscaler_run_diagnostic (ping = ICMP only). "
            "Runs immediately — no memory search or confirmation needed. Returns verdict: "
            "open, refused (port closed), or no_response (filtered/unreachable). "
            "Report the summary/verdict field; ignore NetScaler 'ERROR: Export failed' CLI noise."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "appliance_name": {
                    "type": "string",
                    "description": "Inventory name of the NetScaler appliance",
                },
                "target": {
                    "type": "string",
                    "description": "Destination host or IP to test, e.g. 10.0.0.5 or server.example.com",
                },
                "port": {
                    "type": "integer",
                    "description": "TCP port to test (1-65535), e.g. 443",
                },
                "timeout_seconds": {
                    "type": "integer",
                    "description": "Connect timeout in seconds (default 8, max 20)",
                },
            },
            "required": ["appliance_name", "target", "port"],
        },
    },
    {
        "name": "netscaler_collect_nsconmsg",
        "description": (
            "Collect performance statistics and event logs via nsconmsg (read-only). "
            "Use for 'performance stats', 'counters', 'CPU/memory usage over time', 'event logs', "
            "or historical newnslog analysis. Always read-only (/netscaler/nsconmsg -K /var/nslog/<file> "
            "-d <operation>). Runs immediately — no memory search or confirmation needed. "
            "operation: current (perf data), stats/statswt0 (counters), event (event log), memstats "
            "(memory), consmsg (console), settime (file time span), oldconmsg (historical, with vserver/selectors)."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "appliance_name": {
                    "type": "string",
                    "description": "Inventory name of the NetScaler appliance",
                },
                "operation": {
                    "type": "string",
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
                    "description": "nsconmsg -d operation",
                },
                "logfile": {
                    "type": "string",
                    "description": "newnslog file under /var/nslog (default newnslog; e.g. newnslog.100)",
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
            "required": ["appliance_name", "operation"],
        },
    },
]

SELF_CONNECTIVITY_TOOL = {
    "name": "jpilot_check_doc_connectivity",
    "description": (
        "Check whether JPilot's OWN backend server can reach the official NetScaler/Citrix "
        "documentation sites over HTTPS (and the web-search provider, if enabled). "
        "Use this for 'can you reach the documentation', 'can you reach the internet', "
        "'do you have internet access'. This tests the JPilot backend's connectivity — "
        "NOT a NetScaler appliance, and not via ICMP ping. Requires no appliance."
    ),
    "parameters": {"type": "object", "properties": {}},
}

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
        "Read recommendedCommands for exact syntax; read memoryExcerpts only when retrievalMode is section. Never invent CLI syntax."
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

ARCHITECT_SEARCH_TOOL = {
    "name": "search_jpilot_architect_resources",
    "description": (
        "Search Architect design outline and Citrix integration reference markdown. "
        "Use before producing a design document or when discovery needs AWS, Gateway, AAA, or integration option lists."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Topic to look up, e.g. AWS deployment, Gateway authentication, design outline",
            }
        },
        "required": ["query"],
    },
}

F5_SEARCH_TOOL = {
    "name": "search_f5_tmsh_reference",
    "description": (
        "REQUIRED before f5_run_tmsh_command or f5_run_tmsh_commands. "
        "Searches f5_bigip_tmsh_memory.md for TMSH syntax and recommendedCommands."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "TMSH topic or command, e.g. virtual server or pool members",
            }
        },
        "required": ["query"],
    },
}

F5_DOC_SEARCH_TOOL = {
    "name": "search_f5_documentation",
    "description": (
        "Search official F5 documentation (clouddocs.f5.com, techdocs.f5.com, devcentral.f5.com). "
        "Use for architecture, HA, sizing, and design questions — cite only returned official URLs."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "F5 architecture topic, e.g. active-standby HA or iApp deployment",
            }
        },
        "required": ["query"],
    },
}

CISCO_SEARCH_TOOL = {
    "name": "search_cisco_cli_reference",
    "description": (
        "REQUIRED before cisco_run_cli_command or cisco_run_cli_commands. "
        "Searches cisco_ios_switch_memory.md for IOS/XE syntax and recommendedCommands."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "IOS topic or command, e.g. show vlan brief or access port",
            }
        },
        "required": ["query"],
    },
}

SDX_SEARCH_TOOL = {
    "name": "search_sdx_cli_reference",
    "description": (
        "REQUIRED before sdx_run_cli_command or sdx_run_cli_commands. "
        "Searches netscaler_sdx_cli_memory.md for SDX SVM syntax and recommendedCommands."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "SDX topic or command, e.g. show virtualserver or start VPX",
            }
        },
        "required": ["query"],
    },
}

CISCO_COPILOT_TOOLS = [
    {
        "name": "cisco_test_connection",
        "description": "Test SSH connectivity to a Cisco IOS/XE switch using show version.",
        "parameters": {
            "type": "object",
            "properties": {
                "appliance_name": {"type": "string", "description": "Inventory name of the switch"},
            },
            "required": ["appliance_name"],
        },
    },
    {
        "name": "cisco_ssh_run_command",
        "description": (
            "Run a read-only Cisco IOS/XE command over SSH (show, display, ping, traceroute). "
            "Use search_cisco_cli_reference first when syntax is uncertain."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "appliance_name": {"type": "string"},
                "command": {"type": "string"},
                "purpose": {"type": "string", "description": "Why this command is needed"},
            },
            "required": ["appliance_name", "command", "purpose"],
        },
    },
    {
        "name": "cisco_run_cli_command",
        "description": (
            "Run a single Cisco IOS/XE command over SSH. "
            "Use ONLY after search_cisco_cli_reference confirms syntax from memory."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "appliance_name": {"type": "string"},
                "command": {"type": "string"},
                "purpose": {"type": "string"},
                "confirmed": {
                    "type": "boolean",
                    "description": "Required true for destructive commands on retry",
                },
            },
            "required": ["appliance_name", "command", "purpose"],
        },
    },
    {
        "name": "cisco_run_cli_commands",
        "description": (
            "Run ordered Cisco IOS/XE commands over SSH. "
            "Use ONLY after search_cisco_cli_reference confirms syntax."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "appliance_name": {"type": "string"},
                "commands": {"type": "array", "items": {"type": "string"}},
                "purpose": {"type": "string"},
                "confirmed": {"type": "boolean"},
            },
            "required": ["appliance_name", "commands", "purpose"],
        },
    },
]

F5_COPILOT_TOOLS = [
    {
        "name": "f5_test_connection",
        "description": "Test SSH connectivity to an F5 BIG-IP using tmsh show sys version.",
        "parameters": {
            "type": "object",
            "properties": {
                "appliance_name": {"type": "string", "description": "Inventory name of the BIG-IP"},
            },
            "required": ["appliance_name"],
        },
    },
    {
        "name": "f5_ssh_run_command",
        "description": (
            "Run a read-only F5 TMSH command over SSH (tmsh show/list, ping, traceroute). "
            "Use search_f5_tmsh_reference first when syntax is uncertain."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "appliance_name": {"type": "string"},
                "command": {"type": "string"},
                "purpose": {"type": "string", "description": "Why this command is needed"},
            },
            "required": ["appliance_name", "command", "purpose"],
        },
    },
    {
        "name": "f5_run_tmsh_command",
        "description": (
            "Run a single F5 TMSH configuration command over SSH. "
            "Use ONLY after search_f5_tmsh_reference confirms syntax from memory."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "appliance_name": {"type": "string"},
                "command": {"type": "string"},
                "purpose": {"type": "string"},
                "confirmed": {
                    "type": "boolean",
                    "description": "Required true for destructive commands on retry",
                },
            },
            "required": ["appliance_name", "command", "purpose"],
        },
    },
    {
        "name": "f5_run_tmsh_commands",
        "description": (
            "Run ordered F5 TMSH commands over SSH. "
            "Use ONLY after search_f5_tmsh_reference confirms syntax."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "appliance_name": {"type": "string"},
                "commands": {"type": "array", "items": {"type": "string"}},
                "purpose": {"type": "string"},
                "confirmed": {"type": "boolean"},
            },
            "required": ["appliance_name", "commands", "purpose"],
        },
    },
]

SDX_COPILOT_TOOLS = [
    {
        "name": "sdx_test_connection",
        "description": "Test SSH connectivity to a NetScaler SDX Management Service using show version.",
        "parameters": {
            "type": "object",
            "properties": {
                "appliance_name": {"type": "string", "description": "Inventory name of the SDX appliance"},
            },
            "required": ["appliance_name"],
        },
    },
    {
        "name": "sdx_ssh_run_command",
        "description": (
            "Run a read-only NetScaler SDX SVM command over SSH (show only). "
            "Use search_sdx_cli_reference first when syntax is uncertain."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "appliance_name": {"type": "string"},
                "command": {"type": "string"},
                "purpose": {"type": "string", "description": "Why this command is needed"},
            },
            "required": ["appliance_name", "command", "purpose"],
        },
    },
    {
        "name": "sdx_run_cli_command",
        "description": (
            "Run a single NetScaler SDX SVM CLI command over SSH. "
            "Use ONLY after search_sdx_cli_reference confirms syntax from memory."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "appliance_name": {"type": "string"},
                "command": {"type": "string"},
                "purpose": {"type": "string"},
                "confirmed": {
                    "type": "boolean",
                    "description": "Required true for destructive commands on retry",
                },
            },
            "required": ["appliance_name", "command", "purpose"],
        },
    },
    {
        "name": "sdx_run_cli_commands",
        "description": (
            "Run ordered NetScaler SDX SVM CLI commands over SSH. "
            "Use ONLY after search_sdx_cli_reference confirms syntax."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "appliance_name": {"type": "string"},
                "commands": {"type": "array", "items": {"type": "string"}},
                "purpose": {"type": "string"},
                "confirmed": {"type": "boolean"},
            },
            "required": ["appliance_name", "commands", "purpose"],
        },
    },
]

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
    "netscaler_run_diagnostic": "netscaler_run_diagnostic",
    "netscaler_telnet": "netscaler_telnet",
    "netscaler_collect_nsconmsg": "netscaler_collect_nsconmsg",
    "netscaler_nextgen_request": "netscaler_nextgen_request",
    "netscaler_list_lb_vservers": "netscaler_list_virtual_servers",
    "cisco_test_connection": "cisco_test_connection",
    "cisco_ssh_run_command": "cisco_ssh_run_command",
    "cisco_run_cli_command": "cisco_run_cli_command",
    "cisco_run_cli_commands": "cisco_run_cli_commands",
    "sdx_test_connection": "sdx_test_connection",
    "sdx_ssh_run_command": "sdx_ssh_run_command",
    "sdx_run_cli_command": "sdx_run_cli_command",
    "sdx_run_cli_commands": "sdx_run_cli_commands",
    "f5_test_connection": "f5_test_connection",
    "f5_ssh_run_command": "f5_ssh_run_command",
    "f5_run_tmsh_command": "f5_run_tmsh_command",
    "f5_run_tmsh_commands": "f5_run_tmsh_commands",
}


async def resolve_appliance_credentials(db, appliance_name: str) -> tuple[str, str, str]:
    appliance = await db.appliances.find_one({"name": appliance_name})
    if appliance is None:
        raise ValueError(f"Appliance '{appliance_name}' not found in inventory")

    from app.services.encryption_service import decrypt_value
    from app.services.vendor_registry import is_vendor_copilot_supported

    vendor = str(appliance.get("vendor") or "netscaler").strip().lower()
    if not is_vendor_copilot_supported(vendor):
        raise ValueError(
            f"Appliance '{appliance_name}' (vendor '{vendor}') is not supported for JPilot chat yet."
        )

    return (
        decrypt_value(appliance["encryptedHost"]),
        decrypt_value(appliance["encryptedUsername"]),
        decrypt_value(appliance["encryptedPassword"]),
    )


import contextvars

# Per-request kill switch (set from the chat request's webSearch flag). When False,
# the chat never reaches out to the web regardless of the global/admin setting —
# a quick way to shrink the prompt-injection surface for a given conversation.
_web_search_allowed = contextvars.ContextVar("jpilot_web_search_allowed", default=True)


def set_web_search_allowed(allowed: bool) -> None:
    _web_search_allowed.set(bool(allowed))


async def _web_search_block(
    db,
    query: str,
    topic_hint: str,
    local_weak: bool,
    *,
    vendor: str = "netscaler",
    always_search: bool = False,
) -> dict[str, Any]:
    """Domain-restricted Brave results, only when web search is permitted AND local docs fell short."""
    if not _web_search_allowed.get():
        return {"webSearchEnabled": False, "webSearchReason": "disabled for this chat"}

    from app.services.copilot_platform_service import get_web_search_runtime
    from app.services.vendor_doc_domains import get_allowed_domains_for_vendor

    runtime = await get_web_search_runtime(db)
    if not runtime.get("enabled"):
        return {"webSearchEnabled": False}

    if not local_weak and not always_search:
        # Local memory/official docs already answered — don't fetch external content.
        return {
            "webSearchEnabled": True,
            "webSearchSkipped": "official memory/docs matched; web search reserved for gaps",
        }

    from app.services.brave_search_service import search_web

    allowed_domains = await get_allowed_domains_for_vendor(db, vendor)
    try:
        raw = await search_web(
            runtime["apiKey"],
            query,
            count=5,
            allowed_domains=allowed_domains,
            topic_hint=topic_hint,
        )
        from app.services.model_usage_service import record_brave_search_usage

        await record_brave_search_usage(db, queries=1)
        return {"webSearchEnabled": True, "webResults": json.loads(raw)}
    except Exception as exc:  # never let a search-provider hiccup break the tool
        return {"webSearchEnabled": True, "webSearchError": str(exc)}


async def execute_copilot_tool(
    db,
    name: str,
    arguments: dict[str, Any],
    default_appliance_name: str | None = None,
    role: str | None = None,
    vendor: str | None = None,
) -> str:
    from app.services.copilot_roles import assert_tool_allowed_for_role

    assert_tool_allowed_for_role(name, role, vendor=vendor)

    if name == "jpilot_check_doc_connectivity":
        from app.services.connectivity_service import check_doc_connectivity

        return json.dumps(await check_doc_connectivity(db), indent=2)

    if name == "search_netscaler_nextgen_api":
        from app.services.nextgen_docs_service import search_nextgen_guide
        from app.services.copilot_platform_service import get_allowed_domains

        query = arguments.get("query", "").strip()
        if not query:
            raise ValueError("query is required")

        guide_matches = await search_nextgen_guide(query)
        local_strong = bool(
            guide_matches.get("memoryExcerptCount")
            or guide_matches.get("apiReferenceMatches")
            or guide_matches.get("matchingApiPaths")
            or (guide_matches.get("excerptCount") or 0) >= 2
        )
        chat_vendor = (vendor or "netscaler").strip().lower()
        web_block = await _web_search_block(
            db, query, "NetScaler Next-Gen API", local_weak=not local_strong, vendor=chat_vendor
        )
        payload = {
            "guideMatches": guide_matches,
            "officialDocsOnly": True,
            "allowedDomains": await get_allowed_domains(db, chat_vendor),
            **web_block,
        }
        return json.dumps(payload, separators=(",", ":"))

    if name == "search_netscaler_cli_reference":
        from app.services.cli_reference_service import search_cli_reference

        query = arguments.get("query", "").strip()
        if not query:
            raise ValueError("query is required")
        result = await search_cli_reference(query)
        local_strong = bool(result.get("memoryExcerptCount") or result.get("recommendedCommands"))
        chat_vendor = (vendor or "netscaler").strip().lower()
        result.update(
            await _web_search_block(
                db, query, "NetScaler ADC CLI", local_weak=not local_strong, vendor=chat_vendor
            )
        )
        return json.dumps(result, separators=(",", ":"))

    if name == "search_jpilot_architect_resources":
        from app.services.architect_resource_service import search_architect_resources

        query = arguments.get("query", "").strip()
        if not query:
            raise ValueError("query is required")
        return json.dumps(search_architect_resources(query, vendor=vendor or "netscaler"), separators=(",", ":"))

    if name == "search_cisco_cli_reference":
        from app.services.cisco_cli_memory_service import search_cisco_cli_memory
        from app.services.vendor_doc_domains import get_allowed_domains_for_vendor

        query = arguments.get("query", "").strip()
        if not query:
            raise ValueError("query is required")
        result = search_cisco_cli_memory(query)
        local_strong = bool(result.get("memoryExcerpts") or result.get("recommendedCommands"))
        result.update(
            await _web_search_block(
                db, query, "Cisco IOS CLI", local_weak=not local_strong, vendor="cisco"
            )
        )
        result["officialDocsOnly"] = True
        result["allowedDomains"] = await get_allowed_domains_for_vendor(db, "cisco")
        return json.dumps(result, separators=(",", ":"))

    if name == "search_f5_tmsh_reference":
        from app.services.f5_tmsh_memory_service import search_f5_tmsh_memory
        from app.services.vendor_doc_domains import get_allowed_domains_for_vendor

        query = arguments.get("query", "").strip()
        if not query:
            raise ValueError("query is required")
        result = search_f5_tmsh_memory(query)
        local_strong = bool(result.get("memoryExcerpts") or result.get("recommendedCommands"))
        result.update(
            await _web_search_block(db, query, "F5 BIG-IP TMSH", local_weak=not local_strong, vendor="f5")
        )
        result["officialDocsOnly"] = True
        result["allowedDomains"] = await get_allowed_domains_for_vendor(db, "f5")
        return json.dumps(result, separators=(",", ":"))

    if name == "search_f5_documentation":
        from app.services.vendor_doc_domains import get_allowed_domains_for_vendor

        query = arguments.get("query", "").strip()
        if not query:
            raise ValueError("query is required")
        web_block = await _web_search_block(
            db,
            query,
            "F5 BIG-IP",
            local_weak=True,
            vendor="f5",
            always_search=True,
        )
        payload = {
            "vendor": "f5",
            "query": query,
            "officialDocsOnly": True,
            "allowedDomains": await get_allowed_domains_for_vendor(db, "f5"),
            **web_block,
        }
        return json.dumps(payload, separators=(",", ":"))

    if name == "search_sdx_cli_reference":
        from app.services.sdx_cli_memory_service import search_sdx_cli_memory

        query = arguments.get("query", "").strip()
        if not query:
            raise ValueError("query is required")
        return json.dumps(search_sdx_cli_memory(query), separators=(",", ":"))

    if name == "netscaler_list_inventory":
        appliances = await db.appliances.find().sort("name", 1).to_list(length=None)
        items = [
            {
                "name": item["name"],
                "environment": item["environment"],
                "enabled": item.get("enabled", True),
                "vendor": item.get("vendor", "netscaler"),
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

    if name == "netscaler_run_diagnostic":
        operation = arguments.get("operation", "").strip()
        target = arguments.get("target", "").strip()
        if not operation:
            raise ValueError("operation is required (ping, ping6, traceroute, traceroute6, tcp_port)")
        if not target:
            raise ValueError("target is required")
        mcp_args["operation"] = operation
        mcp_args["target"] = target
        if arguments.get("count") is not None:
            mcp_args["count"] = int(arguments["count"])
        if arguments.get("max_hops") is not None:
            mcp_args["max_hops"] = int(arguments["max_hops"])
        if arguments.get("port") is not None:
            mcp_args["port"] = int(arguments["port"])
        if operation == "tcp_port" and arguments.get("port") is None:
            raise ValueError("port is required for tcp_port operation")

    if name == "netscaler_telnet":
        target = arguments.get("target", "").strip()
        port = arguments.get("port")
        if not target:
            raise ValueError("target is required")
        if port is None:
            raise ValueError("port is required")
        mcp_args["target"] = target
        mcp_args["port"] = int(port)
        if arguments.get("timeout_seconds") is not None:
            mcp_args["timeout_seconds"] = int(arguments["timeout_seconds"])

    if name == "netscaler_collect_nsconmsg":
        operation = arguments.get("operation", "").strip()
        if not operation:
            raise ValueError("operation is required (current, stats, event, memstats, oldconmsg, ...)")
        mcp_args["operation"] = operation
        if arguments.get("logfile"):
            mcp_args["logfile"] = arguments["logfile"].strip()
        if arguments.get("counter"):
            mcp_args["counter"] = arguments["counter"].strip()
        if arguments.get("vserver"):
            mcp_args["vserver"] = arguments["vserver"].strip()
        if arguments.get("selectors"):
            mcp_args["selectors"] = arguments["selectors"]
        if arguments.get("interval") is not None:
            mcp_args["interval"] = int(arguments["interval"])

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

    if name in {"cisco_ssh_run_command", "cisco_run_cli_command"}:
        command = arguments.get("command", "").strip()
        purpose = arguments.get("purpose", "").strip()
        if not command:
            raise ValueError("command is required")
        if not purpose:
            raise ValueError("purpose is required")
        mcp_args["command"] = command
        mcp_args["purpose"] = purpose

    if name == "cisco_run_cli_commands":
        commands = arguments.get("commands") or []
        purpose = arguments.get("purpose", "").strip()
        if not commands:
            raise ValueError("commands is required")
        if not purpose:
            raise ValueError("purpose is required")
        mcp_args["commands"] = commands
        mcp_args["purpose"] = purpose

    if name in {"sdx_ssh_run_command", "sdx_run_cli_command"}:
        command = arguments.get("command", "").strip()
        purpose = arguments.get("purpose", "").strip()
        if not command:
            raise ValueError("command is required")
        if not purpose:
            raise ValueError("purpose is required")
        mcp_args["command"] = command
        mcp_args["purpose"] = purpose

    if name == "sdx_run_cli_commands":
        commands = arguments.get("commands") or []
        purpose = arguments.get("purpose", "").strip()
        if not commands:
            raise ValueError("commands is required")
        if not purpose:
            raise ValueError("purpose is required")
        mcp_args["commands"] = commands
        mcp_args["purpose"] = purpose

    if name in {"f5_ssh_run_command", "f5_run_tmsh_command"}:
        command = arguments.get("command", "").strip()
        purpose = arguments.get("purpose", "").strip()
        if not command:
            raise ValueError("command is required")
        if not purpose:
            raise ValueError("purpose is required")
        mcp_args["command"] = command
        mcp_args["purpose"] = purpose

    if name == "f5_run_tmsh_commands":
        commands = arguments.get("commands") or []
        purpose = arguments.get("purpose", "").strip()
        if not commands:
            raise ValueError("commands is required")
        if not purpose:
            raise ValueError("purpose is required")
        mcp_args["commands"] = commands
        mcp_args["purpose"] = purpose

    return await invoke_mcp_tool(mcp_tool, mcp_args, db=db)


async def get_enabled_copilot_tools(
    db,
    role: str | None = None,
    vendor: str | None = None,
) -> list[dict[str, Any]]:
    from app.services.copilot_roles import filter_tools_for_role, normalize_role
    from app.services.copilot_vendors import filter_tools_by_vendor
    from app.services.mcp_config_service import get_mcp_settings
    from app.services.vendor_registry import get_vendor_manifest, resolve_chat_vendor

    parsed_role = normalize_role(role)
    chat_vendor = resolve_chat_vendor(appliance_vendor=vendor, role=parsed_role.value)
    manifest = get_vendor_manifest(chat_vendor)

    settings = await get_mcp_settings(db)
    enabled = set(settings.enabledTools)
    tools = [
        tool
        for tool in [*COPILOT_TOOLS, *CISCO_COPILOT_TOOLS, *SDX_COPILOT_TOOLS, *F5_COPILOT_TOOLS]
        if tool["name"] == "netscaler_list_inventory" or tool["name"] in enabled
    ]
    tools.append(SELF_CONNECTIVITY_TOOL)
    if manifest:
        search_tool_map = {
            "search_netscaler_nextgen_api": SEARCH_TOOL,
            "search_netscaler_cli_reference": CLI_SEARCH_TOOL,
            "search_jpilot_architect_resources": ARCHITECT_SEARCH_TOOL,
            "search_cisco_cli_reference": CISCO_SEARCH_TOOL,
            "search_sdx_cli_reference": SDX_SEARCH_TOOL,
            "search_f5_tmsh_reference": F5_SEARCH_TOOL,
            "search_f5_documentation": F5_DOC_SEARCH_TOOL,
        }
        for search_tool_name in manifest.search_tools:
            mapped = search_tool_map.get(search_tool_name)
            if mapped:
                tools.append(mapped)
    else:
        tools.extend([SEARCH_TOOL, CLI_SEARCH_TOOL])
    tools = filter_tools_for_role(tools, role, vendor=chat_vendor)
    return filter_tools_by_vendor(tools, chat_vendor)


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
    provider_type: str = "OpenAI-Compatible",
    provider_name: str = "",
) -> dict[str, Any]:
    url = f"{base_url.rstrip('/')}/chat/completions"
    headers = build_openai_compatible_headers(api_key)
    headers["Content-Type"] = "application/json"
    payload = {"model": model, "messages": messages, "tools": tools, "tool_choice": "auto"}

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(url, json=payload, headers=headers)
        if response.status_code >= 400:
            from app.services.ai_provider_errors import raise_for_ai_provider_response

            raise_for_ai_provider_response(
                response,
                provider_type=provider_type,
                model=model,
                provider_name=provider_name,
            )
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
    provider_type: str = "OpenAI-Compatible",
    provider_name: str = "",
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
                provider_type=provider_type,
                provider_name=provider_name,
            )
            return data, candidate
        except httpx.ConnectError as exc:
            errors.append(f"{candidate}: connection failed ({exc})")
            continue
        except httpx.TimeoutException:
            errors.append(f"{candidate}: timed out")
            continue
        except ValueError as exc:
            from app.services.ai_provider_errors import AiProviderError

            if isinstance(exc, AiProviderError):
                raise
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
    provider_name: str = "",
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
            from app.services.ai_provider_errors import raise_for_ai_provider_response

            raise_for_ai_provider_response(
                response,
                provider_type="Anthropic",
                model=model,
                provider_name=provider_name,
            )
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
    provider_name: str = "",
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
            from app.services.ai_provider_errors import raise_for_ai_provider_response

            raise_for_ai_provider_response(
                response,
                provider_type="Gemini",
                model=model,
                provider_name=provider_name,
            )
        return response.json()
