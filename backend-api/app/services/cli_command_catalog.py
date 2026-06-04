"""Curated read-only NetScaler CLI commands from the official ADC command reference."""

CLI_REFERENCE_ROOT = (
    "https://developer-docs.netscaler.com/en-us/adc-command-reference-int/current-release"
)

OFFICIAL_DOC_DOMAINS = (
    "developer-docs.netscaler.com",
    "docs.netscaler.com",
    "docs.citrix.com",
    "community.citrix.com",
    "citrix.com",
    "netscaler.com",
)

# docPath is relative to CLI_REFERENCE_ROOT
READONLY_CLI_COMMANDS: list[dict] = [
    {
        "command": "add ns ip <IPAddress> <netmask> -type VIP",
        "topic": "add a classic VIP address on the appliance",
        "docPath": "ns/ns-ip.html",
        "section": "add ns ip",
        "keywords": ("add vip", "add ip", "new vip", "create vip", "ns ip"),
        "write": True,
    },
    {
        "command": "show ns ip",
        "topic": "all appliance IP addresses (NSIP, SNIP, VIP)",
        "docPath": "ns/ns-ip.html",
        "section": "show ns ip",
        "keywords": ("ip", "nsip", "snip", "vip", "address", "show ns ip"),
    },
    {
        "command": "show ns version",
        "topic": "firmware version and build",
        "docPath": "ns/ns-version.html",
        "section": "show ns version",
        "keywords": ("version", "firmware", "build", "release", "system info"),
    },
    {
        "command": "show ns hostname",
        "topic": "appliance hostname",
        "docPath": "ns/ns-hostName.html",
        "section": "show ns hostname",
        "keywords": ("hostname", "host name", "system name", "system info"),
    },
    {
        "command": "show ns hardware",
        "topic": "hardware platform and serial number",
        "docPath": "ns/ns-hardware.html",
        "section": "show ns hardware",
        "keywords": ("hardware", "serial", "serial number", "platform", "system info"),
    },
    {
        "command": "show lb vserver",
        "topic": "list load balancing virtual servers",
        "docPath": "lb/lb-vserver.html",
        "section": "show lb vserver",
        "keywords": ("lb vserver", "virtual server", "list vserver", "virtual servers", "vservers"),
    },
    {
        "command": "add lb vserver <name> <serviceType> <IPAddress> <port>",
        "topic": "create a load balancing virtual server (classic)",
        "docPath": "lb/lb-vserver.html",
        "section": "add lb vserver",
        "keywords": (
            "add lb vserver",
            "create vserver",
            "create virtual server",
            "load balancer",
            "lb vserver",
            "webserver",
        ),
        "write": True,
    },
    {
        "command": "add serviceGroup <name> <serviceType>",
        "topic": "create a service group for backend servers",
        "docPath": "basic/serviceGroup.html",
        "section": "add serviceGroup",
        "keywords": ("service group", "servicegroup", "backend pool", "server group"),
        "write": True,
    },
    {
        "command": "bind serviceGroup <name> <IPAddress> <port>",
        "topic": "add a backend server to a service group",
        "docPath": "basic/serviceGroup.html",
        "section": "bind serviceGroup",
        "keywords": ("bind servicegroup", "backend server", "member server"),
        "write": True,
    },
    {
        "command": "bind lb vserver <name> -serviceGroupName <serviceGroupName>",
        "topic": "attach a service group to a load balancing virtual server",
        "docPath": "lb/lb-vserver.html",
        "section": "bind lb vserver",
        "keywords": ("bind lb vserver", "bind vserver servicegroup", "attach backend"),
        "write": True,
    },
    {
        "command": "save ns config",
        "topic": "persist running classic configuration",
        "docPath": "ns/ns-config.html",
        "section": "save ns config",
        "keywords": ("save config", "save ns config", "persist", "write config"),
        "write": True,
    },
    {
        "command": "show lb vserver <name>",
        "topic": "details for one load balancing virtual server",
        "docPath": "lb/lb-vserver.html",
        "section": "show lb vserver",
        "keywords": ("lb vserver detail", "vserver detail"),
    },
    {
        "command": "stat lb vserver <name>",
        "topic": "statistics for a load balancing virtual server",
        "docPath": "lb/lb-vserver.html",
        "section": "stat lb vserver",
        "aliases": ("show lb vserver stats",),
        "invalidPatterns": ("show lb vserver statistics", "show lb vserver <name> statistics"),
        "keywords": ("lb vserver stat", "vserver statistics", "vserver stats", "lb_dns"),
    },
    {
        "command": "stat lb vserver",
        "topic": "statistics for all load balancing virtual servers",
        "docPath": "lb/lb-vserver.html",
        "section": "stat lb vserver",
        "keywords": ("all vserver statistics",),
    },
    {
        "command": "show ns runningconfig",
        "topic": "running configuration summary",
        "docPath": "ns/ns-runningConfig.html",
        "section": "show ns runningconfig",
        "keywords": ("running config", "runningconfig"),
    },
    {
        "command": "show ns mode",
        "topic": "appliance modes",
        "docPath": "ns/ns-mode.html",
        "section": "show ns mode",
        "keywords": ("mode",),
    },
    {
        "command": "show ns feature",
        "topic": "enabled features",
        "docPath": "ns/ns-feature.html",
        "section": "show ns feature",
        "keywords": ("feature",),
    },
    {
        "command": "show vlan",
        "topic": "VLAN configuration and bindings",
        "docPath": "network/vlan.html",
        "section": "show vlan",
        "keywords": ("vlan", "vlans", "layer 2", "l2"),
    },
    {
        "command": "show vlan <id>",
        "topic": "details for one VLAN",
        "docPath": "network/vlan.html",
        "section": "show vlan",
        "keywords": ("vlan detail", "vlan id"),
    },
    {
        "command": "show route",
        "topic": "static routing table",
        "docPath": "network/route.html",
        "section": "show route",
        "keywords": ("route", "routing", "routing table", "routes", "gateway", "static route"),
    },
    {
        "command": "show router dynamicRouting",
        "topic": "dynamic routing protocols (BGP/OSPF/RIP via ZebOS)",
        "docPath": "router/router-dynamicRouting.html",
        "section": "show router dynamicRouting",
        "keywords": ("dynamic routing", "bgp", "ospf", "rip", "zebos", "vtysh"),
    },
    {
        "command": "ping -c 4 <host>",
        "topic": "test ICMP reachability to a host (connectivity troubleshooting)",
        "docPath": "utility/ping.html",
        "section": "ping",
        "keywords": (
            "ping",
            "connectivity",
            "reachability",
            "reachable",
            "icmp",
            "troubleshoot",
            "troubleshooting",
            "network test",
            "is it up",
        ),
    },
    {
        "command": "ping6 -c 4 <host>",
        "topic": "test ICMPv6 reachability to an IPv6 host",
        "docPath": "utility/ping6.html",
        "section": "ping6",
        "keywords": ("ping6", "ipv6 ping", "ipv6 connectivity", "icmpv6"),
    },
    {
        "command": "traceroute <host>",
        "topic": "trace the network path/hops to a host (connectivity troubleshooting)",
        "docPath": "utility/traceroute.html",
        "section": "traceroute",
        "keywords": (
            "traceroute",
            "trace route",
            "trace path",
            "hops",
            "path to",
            "route to host",
            "troubleshoot",
            "troubleshooting",
            "network path",
        ),
    },
    {
        "command": "traceroute6 <host>",
        "topic": "trace the network path/hops to an IPv6 host",
        "docPath": "utility/traceroute6.html",
        "section": "traceroute6",
        "keywords": ("traceroute6", "ipv6 traceroute", "ipv6 path", "ipv6 hops"),
    },
    {
        "command": "show arp",
        "topic": "ARP table — IP-to-MAC resolution (L2 connectivity troubleshooting)",
        "docPath": "network/arp.html",
        "section": "show arp",
        "keywords": (
            "arp",
            "arp table",
            "mac address",
            "mac",
            "l2",
            "layer 2",
            "ip to mac",
            "neighbor",
            "troubleshoot",
        ),
    },
    {
        "command": "show interface",
        "topic": "interface link state, speed/duplex, and error counters",
        "docPath": "network/interface.html",
        "section": "show interface",
        "keywords": (
            "interface",
            "interfaces",
            "link",
            "link state",
            "nic",
            "port status",
            "speed",
            "duplex",
            "troubleshoot",
        ),
    },
    {
        "command": "stat interface",
        "topic": "interface statistics: throughput, drops, and errors",
        "docPath": "network/interface.html",
        "section": "stat interface",
        "aliases": ("show interface stats",),
        "invalidPatterns": ("show interface statistics",),
        "keywords": ("interface stats", "interface statistics", "nic errors", "packet drops", "link errors"),
    },
    {
        "command": "start nstrace -size 0 -mode RX TX",
        "topic": "start a packet capture (nstrace) for deep network troubleshooting",
        "docPath": "basic/nstrace.html",
        "section": "start nstrace",
        "keywords": (
            "nstrace",
            "packet capture",
            "packet trace",
            "capture traffic",
            "tcpdump",
            "sniff",
            "trace packets",
            "pcap",
        ),
        "write": True,
    },
    {
        "command": "show nstrace",
        "topic": "status of a running packet capture (nstrace)",
        "docPath": "basic/nstrace.html",
        "section": "show nstrace",
        "keywords": ("nstrace status", "show nstrace", "capture status"),
    },
    {
        "command": "stop nstrace",
        "topic": "stop a running packet capture (nstrace)",
        "docPath": "basic/nstrace.html",
        "section": "stop nstrace",
        "keywords": ("stop nstrace", "stop capture", "end packet capture"),
        "write": True,
    },
]


def official_doc_url(doc_path: str) -> str:
    return f"{CLI_REFERENCE_ROOT}/{doc_path.lstrip('/')}"


def is_official_doc_url(url: str) -> bool:
    lowered = (url or "").lower()
    return any(domain in lowered for domain in OFFICIAL_DOC_DOMAINS)


def search_command_catalog(query: str, max_results: int = 8) -> list[dict]:
    cleaned = query.strip().lower()
    cleaned = cleaned.replace("routnig", "routing")
    if not cleaned:
        return []

    terms = [term for term in cleaned.replace("<", " ").replace(">", " ").split() if len(term) > 1]
    if not terms:
        terms = [cleaned]

    query_tokens = cleaned.split()
    scored: list[tuple[int, dict]] = []
    for entry in READONLY_CLI_COMMANDS:
        command_lower = entry.get("command", "").lower()
        haystack = " ".join(
            [
                command_lower,
                entry.get("topic", ""),
                " ".join(entry.get("keywords", ())),
                " ".join(entry.get("aliases", ())),
            ]
        )
        score = sum(2 for term in terms if term in haystack)
        cmd_tokens = command_lower.split()
        if len(query_tokens) >= 2 and len(cmd_tokens) >= 2:
            if query_tokens[0] == cmd_tokens[0] and query_tokens[1] == cmd_tokens[1]:
                score += 10
        if cleaned in command_lower:
            score += 12
        min_score = 2 if len(terms) >= 2 else 1
        if score >= min_score:
            row = dict(entry)
            row["docUrl"] = official_doc_url(row["docPath"])
            row["score"] = score
            scored.append((score, row))

    scored.sort(key=lambda item: item[0], reverse=True)
    return [row for _, row in scored[:max_results]]


def topic_paths_for_query(query: str) -> list[str]:
    seen: set[str] = set()
    paths: list[str] = []
    for row in search_command_catalog(query, max_results=12):
        path = row.get("docPath", "")
        if path and path not in seen:
            seen.add(path)
            paths.append(path)
    return paths
