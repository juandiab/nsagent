"""Catalog of JPilot beta platform tools (SDX, Cisco IOS/XE, F5 BIG-IP)."""

from __future__ import annotations

BETA_PRODUCTS: list[dict] = [
    {
        "id": "sdx",
        "vendorId": "sdx",
        "label": "NetScaler SDX",
        "vendorGroup": "Citrix",
        "description": "SDX Management Service (SVM) over SSH — VPX lifecycle and platform show commands.",
        "transport": "SSH (port 22)",
        "accessHint": "SSH to the SDX Management Service (SVM).",
        "docUrls": [
            {
                "label": "NetScaler documentation",
                "url": "https://docs.netscaler.com/",
            },
            {
                "label": "Citrix Tech Zone",
                "url": "https://community.citrix.com/tech-zone/",
            },
        ],
        "options": [
            {
                "name": "sdx_test_connection",
                "label": "Test Connection",
                "description": "Verify SSH connectivity using show version on the SVM.",
                "configurable": True,
                "surfaces": ["mcp", "copilot"],
            },
            {
                "name": "sdx_ssh_run_command",
                "label": "Read-only SSH",
                "description": "Run read-only show commands on the SDX SVM.",
                "configurable": True,
                "surfaces": ["mcp", "copilot"],
            },
            {
                "name": "sdx_run_cli_command",
                "label": "Run CLI Command",
                "description": "Run a single SDX SVM write command (VPX lifecycle, VLAN, firmware).",
                "configurable": True,
                "surfaces": ["mcp", "copilot"],
            },
            {
                "name": "sdx_run_cli_commands",
                "label": "Run CLI Sequence",
                "description": "Run ordered SDX SVM commands over SSH.",
                "configurable": True,
                "surfaces": ["mcp", "copilot"],
            },
            {
                "name": "search_sdx_cli_reference",
                "label": "Search CLI Reference",
                "description": "Search SDX memory before write commands. Required for provisioning.",
                "configurable": False,
                "surfaces": ["copilot"],
            },
        ],
    },
    {
        "id": "cisco",
        "vendorId": "cisco",
        "label": "Cisco IOS/XE Switches",
        "vendorGroup": "Cisco",
        "description": "Cisco IOS/XE switches over SSH — show/configure with official Cisco doc search.",
        "transport": "SSH (port 22)",
        "accessHint": "SSH to the switch management IP.",
        "docUrls": [
            {"label": "Cisco documentation", "url": "https://docs.cisco.com/"},
            {"label": "Cisco DevNet", "url": "https://developer.cisco.com/"},
        ],
        "options": [
            {
                "name": "cisco_test_connection",
                "label": "Test Connection",
                "description": "Verify SSH connectivity using show version.",
                "configurable": True,
                "surfaces": ["mcp", "copilot"],
            },
            {
                "name": "cisco_ssh_run_command",
                "label": "Read-only SSH",
                "description": "Run read-only show, display, ping, or traceroute commands.",
                "configurable": True,
                "surfaces": ["mcp", "copilot"],
            },
            {
                "name": "cisco_run_cli_command",
                "label": "Run CLI Command",
                "description": "Run a single IOS/XE configuration or exec command.",
                "configurable": True,
                "surfaces": ["mcp", "copilot"],
            },
            {
                "name": "cisco_run_cli_commands",
                "label": "Run CLI Sequence",
                "description": "Run ordered IOS/XE commands (e.g. conf t, interface, copy run start).",
                "configurable": True,
                "surfaces": ["mcp", "copilot"],
            },
            {
                "name": "search_cisco_cli_reference",
                "label": "Search CLI Reference",
                "description": "Search Cisco memory and official cisco.com docs before writes.",
                "configurable": False,
                "surfaces": ["copilot"],
            },
        ],
    },
    {
        "id": "f5",
        "vendorId": "f5",
        "label": "F5 BIG-IP",
        "vendorGroup": "F5",
        "description": "F5 BIG-IP over SSH (TMSH) — discovery, troubleshooting, basic LB, and Architect doc search.",
        "transport": "SSH (port 22)",
        "accessHint": "SSH to the BIG-IP management IP (TMSH).",
        "docUrls": [
            {"label": "F5 Cloud Docs", "url": "https://clouddocs.f5.com/"},
            {"label": "F5 TechDocs", "url": "https://techdocs.f5.com/"},
            {"label": "DevCentral", "url": "https://devcentral.f5.com/"},
        ],
        "options": [
            {
                "name": "f5_test_connection",
                "label": "Test Connection",
                "description": "Verify SSH connectivity using tmsh show sys version.",
                "configurable": True,
                "surfaces": ["mcp", "copilot"],
            },
            {
                "name": "f5_ssh_run_command",
                "label": "Read-only SSH",
                "description": "Run read-only tmsh show/list, ping, or traceroute.",
                "configurable": True,
                "surfaces": ["mcp", "copilot"],
            },
            {
                "name": "f5_run_tmsh_command",
                "label": "Run TMSH Command",
                "description": "Run a single TMSH configuration command (pools, virtual servers, profiles).",
                "configurable": True,
                "surfaces": ["mcp", "copilot"],
            },
            {
                "name": "f5_run_tmsh_commands",
                "label": "Run TMSH Sequence",
                "description": "Run ordered TMSH commands over SSH.",
                "configurable": True,
                "surfaces": ["mcp", "copilot"],
            },
            {
                "name": "search_f5_tmsh_reference",
                "label": "Search TMSH Reference",
                "description": "Search F5 TMSH memory and official F5 docs before writes.",
                "configurable": False,
                "surfaces": ["copilot"],
            },
            {
                "name": "search_f5_documentation",
                "label": "Search F5 Documentation",
                "description": "Official F5 web documentation for Architect role (design/HA).",
                "configurable": False,
                "surfaces": ["copilot"],
            },
        ],
    },
]


def get_beta_products() -> list[dict]:
    return [dict(product) for product in BETA_PRODUCTS]


def get_beta_feature_options() -> list[dict]:
    """Flat list of all beta tool options (Next-Gen options shape)."""
    items: list[dict] = []
    for product in BETA_PRODUCTS:
        for option in product["options"]:
            row = dict(option)
            row["productId"] = product["id"]
            row["productLabel"] = product["label"]
            items.append(row)
    return items


def get_beta_features_info() -> dict:
    configurable = [o for p in BETA_PRODUCTS for o in p["options"] if o.get("configurable")]
    return {
        "productCount": len(BETA_PRODUCTS),
        "configurableToolCount": len(configurable),
        "transport": "SSH",
        "sshSettingsNote": (
            "SSH port, timeout, and fallback are configured on the Next-Gen API settings tab "
            "(shared MCP runtime)."
        ),
        "statusLabel": "Beta Available",
    }
