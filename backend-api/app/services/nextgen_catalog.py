"""Catalog of NetScaler Next-Gen API capabilities exposed to Copilot and MCP."""

NEXTGEN_API_BASE = "/mgmt/api/nextgen/v1"
NEXTGEN_GUIDE_URL = "https://developer-docs.netscaler.com/en-us/nextgen-api/getting-started-guide.html"
NEXTGEN_API_DOCS_URL = "https://developer-docs.netscaler.com/en-us/nextgen-api/apis/"

NEXTGEN_OPTIONS: list[dict] = [
    {
        "name": "netscaler_test_connection",
        "label": "Test Connection",
        "description": "Verify Next-Gen API connectivity and authentication to an appliance.",
        "nextGenEndpoints": ["POST /login"],
        "configurable": True,
        "surfaces": ["mcp", "copilot"],
    },
    {
        "name": "netscaler_get_system_info",
        "label": "System Info",
        "description": "Management IP, firmware version, hostname, serial, and application count.",
        "nextGenEndpoints": ["GET /applications"],
        "configurable": True,
        "surfaces": ["mcp", "copilot"],
    },
    {
        "name": "netscaler_list_applications",
        "label": "List Applications",
        "description": "List Next-Gen API applications only.",
        "nextGenEndpoints": ["GET /applications"],
        "configurable": True,
        "surfaces": ["mcp", "copilot"],
    },
    {
        "name": "netscaler_list_virtual_servers",
        "label": "List Virtual Servers",
        "description": "List Next-Gen applications plus classic NITRO lbvserver entries.",
        "nextGenEndpoints": ["GET /applications"],
        "configurable": True,
        "surfaces": ["mcp", "copilot"],
    },
    {
        "name": "netscaler_list_virtual_ips",
        "label": "List Virtual IPs",
        "description": "List load-balancing VIPs from Next-Gen applications, frontends, and listeners.",
        "nextGenEndpoints": ["GET /applications", "GET /applications/{name}"],
        "configurable": True,
        "surfaces": ["mcp", "copilot"],
    },
    {
        "name": "netscaler_list_ip_addresses",
        "label": "List All IP Addresses",
        "description": (
            "List NSIP, SNIP, VIP, server, and application IPs via Next-Gen API "
            "(applications, config_sets) with read-only NITRO supplement for classic config."
        ),
        "nextGenEndpoints": [
            "GET /applications",
            "GET /applications/{name}",
            "GET /config_sets",
            "GET /config_sets/{name}/config",
        ],
        "configurable": True,
        "surfaces": ["mcp", "copilot"],
    },
    {
        "name": "netscaler_nextgen_get",
        "label": "Next-Gen GET",
        "description": "Read-only GET against a Next-Gen API resource path.",
        "nextGenEndpoints": ["GET /{path}"],
        "configurable": True,
        "surfaces": ["mcp", "copilot"],
    },
    {
        "name": "netscaler_create_application",
        "label": "Create Application",
        "description": "Create a Next-Gen application (POST /applications) with VIP and backend servers.",
        "nextGenEndpoints": ["POST /applications"],
        "configurable": True,
        "surfaces": ["mcp", "copilot"],
    },
    {
        "name": "netscaler_add_ip_address",
        "label": "Add IP Address",
        "description": "Add classic NSIP/SNIP/VIP via NITRO (add ns ip). Requires CLI memory review first.",
        "nextGenEndpoints": [],
        "configurable": True,
        "surfaces": ["mcp", "copilot"],
    },
    {
        "name": "netscaler_run_cli_command",
        "label": "Run CLI Command",
        "description": "Run any classic NetScaler CLI command via SSH (add/set/bind/save/show/stat/get).",
        "nextGenEndpoints": [],
        "configurable": True,
        "surfaces": ["mcp", "copilot"],
    },
    {
        "name": "netscaler_run_cli_commands",
        "label": "Run CLI Command Sequence",
        "description": "Run multiple classic CLI commands in order via SSH (multi-step LB setup).",
        "nextGenEndpoints": [],
        "configurable": True,
        "surfaces": ["mcp", "copilot"],
    },
    {
        "name": "netscaler_ssh_run_command",
        "label": "SSH CLI Command",
        "description": "Run read-only show/stat/get CLI commands via SSH when Next-Gen API is insufficient.",
        "nextGenEndpoints": [],
        "configurable": True,
        "surfaces": ["mcp", "copilot"],
    },
    {
        "name": "netscaler_list_inventory",
        "label": "List Inventory",
        "description": "List NetScaler appliances registered in the platform inventory.",
        "nextGenEndpoints": [],
        "configurable": False,
        "surfaces": ["copilot"],
    },
    {
        "name": "search_netscaler_nextgen_api",
        "label": "Search API Documentation",
        "description": "Search netscaler_nextgen_api_memory.md and official API reference. Required before Next-Gen API tools.",
        "nextGenEndpoints": [],
        "configurable": False,
        "surfaces": ["copilot"],
    },
    {
        "name": "search_netscaler_cli_reference",
        "label": "Search CLI Reference",
        "description": "Search netscaler_adc_cli_memory.md and official CLI reference. Required before SSH.",
        "nextGenEndpoints": [],
        "configurable": False,
        "surfaces": ["copilot"],
    },
]


CLI_REFERENCE_URL = (
    "https://developer-docs.netscaler.com/en-us/adc-command-reference-int/current-release.html"
)


def get_nextgen_api_info() -> dict:
    from app.services.nextgen_api_reference import NEXTGEN_API_DOCS_URL as API_DOCS_URL, get_api_categories

    return {
        "apiBase": NEXTGEN_API_BASE,
        "guideUrl": NEXTGEN_GUIDE_URL,
        "apiDocsUrl": API_DOCS_URL,
        "cliReferenceUrl": CLI_REFERENCE_URL,
        "transport": "HTTPS (port 443)",
        "auth": "POST /login with session cookie",
        "sshFallback": "Read-only show/stat/get via SSH when Next-Gen API is insufficient",
        "apiCategoryCount": len(get_api_categories()),
    }


def get_nextgen_options() -> list[dict]:
    return [dict(item) for item in NEXTGEN_OPTIONS]


def get_tool_catalog() -> list[dict]:
    """Legacy shape used by MCP settings toggles."""
    return [
        {
            "name": item["name"],
            "label": item["label"],
            "description": item["description"],
        }
        for item in NEXTGEN_OPTIONS
        if item["configurable"]
    ]
