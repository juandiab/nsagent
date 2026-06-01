"""Static NetScaler Next-Gen API reference for UI catalog and Copilot RAG."""

NEXTGEN_API_DOCS_URL = "https://developer-docs.netscaler.com/en-us/nextgen-api/apis/"

# Paths are relative to /mgmt/api/nextgen/v1/
NEXTGEN_API_CATEGORIES: list[dict] = [
    {
        "category": "Applications",
        "operations": [
            {"name": "ListApplications", "method": "GET", "path": "applications"},
            {"name": "AddApplication", "method": "POST", "path": "applications"},
            {"name": "GetApplication", "method": "GET", "path": "applications/{name}"},
            {"name": "CreateOrUpdateApplication", "method": "POST", "path": "applications/{name}"},
            {"name": "UpdateApplication", "method": "PUT", "path": "applications/{name}"},
            {"name": "DeleteApplication", "method": "DELETE", "path": "applications/{name}"},
            {"name": "GetApplicationConfigStatus", "method": "GET", "path": "applications/{name}/config_status"},
            {"name": "GetApplicationHealth", "method": "GET", "path": "applications/{name}/health"},
            {"name": "GetApplicationStats", "method": "GET", "path": "applications/{name}/stats"},
            {"name": "EnableApplication", "method": "POST", "path": "applications/{name}/enable"},
            {"name": "DisableApplication", "method": "POST", "path": "applications/{name}/disable"},
            {"name": "InstallApplication", "method": "POST", "path": "applications/{name}/install"},
            {"name": "UninstallApplication", "method": "POST", "path": "applications/{name}/uninstall"},
        ],
    },
    {
        "category": "Authentication",
        "operations": [
            {"name": "Login", "method": "POST", "path": "login"},
            {"name": "Logout", "method": "POST", "path": "logout"},
        ],
    },
    {
        "category": "Backends",
        "operations": [
            {"name": "ListBackends", "method": "GET", "path": "applications/{name}/backends"},
            {"name": "GetBackend", "method": "GET", "path": "applications/{name}/backends/{backend}"},
            {"name": "UpdateBackend", "method": "PUT", "path": "applications/{name}/backends/{backend}"},
            {"name": "DeleteBackend", "method": "DELETE", "path": "applications/{name}/backends/{backend}"},
            {"name": "EnableApplicationBackend", "method": "POST", "path": "applications/{name}/backends/{backend}/enable"},
            {"name": "DisableApplicationBackend", "method": "POST", "path": "applications/{name}/backends/{backend}/disable"},
            {"name": "ListServers", "method": "GET", "path": "applications/{name}/backends/{backend}/servers"},
            {"name": "AddServer", "method": "POST", "path": "applications/{name}/backends/{backend}/servers"},
            {"name": "UpdateServers", "method": "PUT", "path": "applications/{name}/backends/{backend}/servers"},
            {"name": "DeleteServer", "method": "DELETE", "path": "applications/{name}/backends/{backend}/servers/{server}"},
            {"name": "EnableApplicationBackendServer", "method": "POST", "path": "applications/{name}/backends/{backend}/servers/{server}/enable"},
            {"name": "DisableApplicationBackendServer", "method": "POST", "path": "applications/{name}/backends/{backend}/servers/{server}/disable"},
        ],
    },
    {
        "category": "Certificates",
        "operations": [
            {"name": "ListCertificates", "method": "GET", "path": "certificates"},
            {"name": "AddCertificate", "method": "POST", "path": "certificates"},
            {"name": "GetCertificate", "method": "GET", "path": "certificates/{name}"},
            {"name": "AddOrUpdateCertificate", "method": "POST", "path": "certificates/{name}"},
            {"name": "UpdateCertificate", "method": "PUT", "path": "certificates/{name}"},
            {"name": "DeleteCertificate", "method": "DELETE", "path": "certificates/{name}"},
            {"name": "GetCertificateConfigStatus", "method": "GET", "path": "certificates/{name}/config_status"},
        ],
    },
    {
        "category": "Config Sets",
        "operations": [
            {"name": "GetConfigSets", "method": "GET", "path": "config_sets"},
            {"name": "AddConfigSet", "method": "POST", "path": "config_sets"},
            {"name": "GetConfigSet", "method": "GET", "path": "config_sets/{name}"},
            {"name": "AddOrUpdateConfigSet", "method": "POST", "path": "config_sets/{name}"},
            {"name": "UpdateConfigSet", "method": "PUT", "path": "config_sets/{name}"},
            {"name": "DeleteConfigSet", "method": "DELETE", "path": "config_sets/{name}"},
            {"name": "GetConfigSetStatistics", "method": "GET", "path": "config_sets/{name}/stats"},
            {"name": "GetConfigSetConfigStatus", "method": "GET", "path": "config_sets/{name}/config_status"},
            {"name": "GetConfigSetConfig", "method": "GET", "path": "config_sets/{name}/config"},
        ],
    },
    {
        "category": "Filter Value Sets",
        "operations": [
            {"name": "GetFilterValueSets", "method": "GET", "path": "filter_value_sets"},
            {"name": "AddFilterValueSet", "method": "POST", "path": "filter_value_sets"},
            {"name": "GetFilterValueSet", "method": "GET", "path": "filter_value_sets/{name}"},
            {"name": "AddOrUpdateFilterValueSet", "method": "POST", "path": "filter_value_sets/{name}"},
            {"name": "UpdateFilterValueSet", "method": "PUT", "path": "filter_value_sets/{name}"},
            {"name": "DeleteFilterValueSet", "method": "DELETE", "path": "filter_value_sets/{name}"},
            {"name": "GetFilterValueSetConfigStatus", "method": "GET", "path": "filter_value_sets/{name}/config_status"},
        ],
    },
    {
        "category": "Frontends",
        "operations": [
            {"name": "ListFrontends", "method": "GET", "path": "applications/{name}/frontends"},
            {"name": "GetFrontend", "method": "GET", "path": "applications/{name}/frontends/{frontend}"},
            {"name": "UpdateFrontend", "method": "PUT", "path": "applications/{name}/frontends/{frontend}"},
            {"name": "DeleteFrontend", "method": "DELETE", "path": "applications/{name}/frontends/{frontend}"},
            {"name": "EnableApplicationFrontend", "method": "POST", "path": "applications/{name}/frontends/{frontend}/enable"},
            {"name": "DisableApplicationFrontend", "method": "POST", "path": "applications/{name}/frontends/{frontend}/disable"},
            {"name": "ListListeners", "method": "GET", "path": "applications/{name}/frontends/{frontend}/listeners"},
            {"name": "GetListener", "method": "GET", "path": "applications/{name}/frontends/{frontend}/listeners/{listener}"},
            {"name": "UpdateListener", "method": "PUT", "path": "applications/{name}/frontends/{frontend}/listeners/{listener}"},
            {"name": "DeleteListener", "method": "DELETE", "path": "applications/{name}/frontends/{frontend}/listeners/{listener}"},
            {"name": "EnableApplicationFrontendListener", "method": "POST", "path": "applications/{name}/frontends/{frontend}/listeners/{listener}/enable"},
            {"name": "DisableApplicationFrontendListener", "method": "POST", "path": "applications/{name}/frontends/{frontend}/listeners/{listener}/disable"},
        ],
    },
    {
        "category": "HTTP Callouts",
        "operations": [
            {"name": "GetHttpCallouts", "method": "GET", "path": "http_callouts"},
            {"name": "AddHttpCallout", "method": "POST", "path": "http_callouts"},
            {"name": "GetHttpCallout", "method": "GET", "path": "http_callouts/{name}"},
            {"name": "AddOrUpdateHttpCallout", "method": "POST", "path": "http_callouts/{name}"},
            {"name": "UpdateHttpCallout", "method": "PUT", "path": "http_callouts/{name}"},
            {"name": "DeleteHttpCallout", "method": "DELETE", "path": "http_callouts/{name}"},
            {"name": "GetHttpCalloutConfigStatus", "method": "GET", "path": "http_callouts/{name}/config_status"},
        ],
    },
    {
        "category": "RBAC",
        "operations": [
            {"name": "GetRoles", "method": "GET", "path": "roles"},
            {"name": "AddRole", "method": "POST", "path": "roles"},
            {"name": "GetRole", "method": "GET", "path": "roles/{name}"},
            {"name": "AddOrUpdateRole", "method": "POST", "path": "roles/{name}"},
            {"name": "UpdateRole", "method": "PUT", "path": "roles/{name}"},
            {"name": "DeleteRole", "method": "DELETE", "path": "roles/{name}"},
            {"name": "GetGroups", "method": "GET", "path": "groups"},
            {"name": "GetGroupRoles", "method": "GET", "path": "groups/{name}/roles"},
            {"name": "AddGroupRole", "method": "POST", "path": "groups/{name}/roles"},
            {"name": "AddGroupRoles", "method": "PUT", "path": "groups/{name}/roles"},
            {"name": "DeleteGroupRole", "method": "DELETE", "path": "groups/{name}/roles/{role}"},
        ],
    },
    {
        "category": "Responder HTML Pages",
        "operations": [
            {"name": "GetResponderHtmlPages", "method": "GET", "path": "responder_html_pages"},
            {"name": "AddResponderHtmlPage", "method": "POST", "path": "responder_html_pages"},
            {"name": "GetResponderHtmlPage", "method": "GET", "path": "responder_html_pages/{name}"},
            {"name": "AddOrUpdateResponderHtmlPage", "method": "POST", "path": "responder_html_pages/{name}"},
            {"name": "UpdateResponderHtmlPage", "method": "PUT", "path": "responder_html_pages/{name}"},
            {"name": "DeleteResponderHtmlPage", "method": "DELETE", "path": "responder_html_pages/{name}"},
            {"name": "GetResponderHtmlPageConfigStatus", "method": "GET", "path": "responder_html_pages/{name}/config_status"},
        ],
    },
    {
        "category": "Routes",
        "operations": [
            {"name": "ListRoutes", "method": "GET", "path": "routes"},
            {"name": "AddRoute", "method": "POST", "path": "routes"},
            {"name": "GetRoute", "method": "GET", "path": "routes/{name}"},
            {"name": "CreateOrUpdateRoute", "method": "POST", "path": "routes/{name}"},
            {"name": "UpdateRoute", "method": "PUT", "path": "routes/{name}"},
            {"name": "DeleteRoute", "method": "DELETE", "path": "routes/{name}"},
        ],
    },
]

_IP_KEYWORDS = ("ip", "address", "vip", "nsip", "snip", "listener", "frontend", "server", "route", "config_set")


def get_api_categories() -> list[dict]:
    return [dict(item) for item in NEXTGEN_API_CATEGORIES]


def flatten_operations() -> list[dict]:
    rows: list[dict] = []
    for group in NEXTGEN_API_CATEGORIES:
        category = group["category"]
        for operation in group["operations"]:
            rows.append(
                {
                    "category": category,
                    "name": operation["name"],
                    "method": operation["method"],
                    "path": operation["path"],
                    "fullPath": f"/mgmt/api/nextgen/v1/{operation['path']}",
                }
            )
    return rows


def build_reference_index_text() -> str:
    parts: list[str] = []
    for row in flatten_operations():
        parts.append(
            f"{row['category']} {row['name']} {row['method']} {row['path']} {row['fullPath']}"
        )
    return " ".join(parts)


def search_api_reference(query: str, max_results: int = 15) -> list[dict]:
    cleaned = query.strip().lower()
    rows = flatten_operations()
    if not cleaned:
        return rows[:max_results]

    terms = [term for term in cleaned.replace("/", " ").split() if len(term) > 1]
    if not terms:
        terms = [cleaned]

    scored: list[tuple[int, dict]] = []
    for row in rows:
        haystack = f"{row['category']} {row['name']} {row['method']} {row['path']}".lower()
        score = sum(1 for term in terms if term in haystack)
        if score:
            scored.append((score, row))

    scored.sort(key=lambda item: item[0], reverse=True)
    return [row for _, row in scored[:max_results]]


def suggest_read_paths_for_query(query: str) -> list[str]:
    """Suggest GET paths Copilot can call via netscaler_nextgen_get."""
    lowered = query.lower()
    suggestions: list[str] = []

    if any(term in lowered for term in ("all ip", "list ip", "every ip", "nsip", "snip", "vip", "address")):
        suggestions.extend(
            [
                "applications",
                "config_sets",
                "certificates",
            ]
        )

    for row in search_api_reference(query, max_results=8):
        if row["method"] == "GET" and "{" not in row["path"]:
            suggestions.append(row["path"])

    seen: set[str] = set()
    ordered: list[str] = []
    for path in suggestions:
        if path not in seen:
            seen.add(path)
            ordered.append(path)
    return ordered
