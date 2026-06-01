# NetScaler Next-Gen API — LLM Copilot Memory File

> **Source:** Official NetScaler developer documentation  
> **Base URL pattern:** `https://<netscaler-host>/mgmt/api/nextgen/v1`  
> **Last updated from docs:** May 2026 (NetScaler 14.1 12.30+)

---

## 1. OVERVIEW & CORE CONCEPTS

### What is the Next-Gen API?
- A modern RESTful, **declarative, desired-state** API for NetScaler — simpler than the legacy Nitro API.
- Application-centric: all config for one application is grouped into one resource tree.
- Uses a **new config infrastructure** that separates validation/commit (fast, synchronous) from data-plane apply (async background).
- Configuration is **persistent across reboots** and is NOT stored in `ns.conf`.
- Supports two paradigms:
  - **Application-Centric Model** — high-level abstraction for common use cases.
  - **Entity-Centric / Config Sets Model** — full Nitro entity access in desired-state form.

### System Requirements
- NetScaler release **14.1 12.30** or later.
- VPX requires at least **4 GB RAM**.
- Standalone and HA (MPX/VPX) supported. **Cluster NOT supported** (as of docs date).

### Enabling Next-Gen API (CLI)
```bash
# First enable SSL default profile if not already done
set ssl parameter -defaultProfile ENABLED

# Then enable Next-Gen API
enable ns nextgenapi

# Verify
show ns nextgenapi
# Expected output: Next-Gen API State: STARTED
```

### Config View (CLI)
```bash
switch ns configview NEXTGENAPI   # View only Next-Gen API configs (read-only for classic)
switch ns configview ALL          # Default — read-only Next-Gen + unrestricted classic
switch ns configview CLASSIC      # Only classic CLI/GUI/Nitro configs

# Delete ALL Next-Gen API resources at once
clear ns nextgenapi

# Note: clear ns config basic/extended does NOT clear Next-Gen API config.
# clear ns config full DOES clear it.
```

### Logging (CLI prerequisite)
```bash
set syslogparams -userDefinedAuditlog YES
```

---

## 2. AUTHENTICATION

### Base URL
```
POST /mgmt/api/nextgen/v1/login
POST /mgmt/api/nextgen/v1/logout
```

### Login — Obtain Session Token
```json
POST /mgmt/api/nextgen/v1/login

{
  "login": {
    "username": "user1",
    "password": "verysecret"
  }
}
```
**Success response (200 OK):**
```
Set-Cookie: sessionid=%23%23B2A100C6D1F36AAE2......A50FA2C576171; Path=/mgmt/api/nextgen/v1
```

With session timeout:
```json
{
  "login": {
    "username": "user1",
    "password": "verysecret",
    "timeout": "5min"
  }
}
```
> Time units accepted: `5m`, `5min`, `300s`, `300sec` — unit is always required.

### Authenticated Requests
Include the `sessionid` cookie in every subsequent request:
```
GET /mgmt/api/nextgen/v1/applications
Cookie: sessionid=%23%23B2A100C6D1F36AAE2......A50FA2C576171
```

### Logout — Invalidate Session
```json
POST /mgmt/api/nextgen/v1/logout
Cookie: sessionid=<token>
```
**Success response (200 OK):**
```
Set-Cookie: sessionid=deleted; expires=Thu, 01-Jan-1970 00:00:01 GMT; Max-Age=0; Path=/mgmt/api/nextgen/v1
```
No response body. Session cookie is invalidated immediately.

> Next-Gen API and Nitro API share the same system users. User/group management still done via CLI/GUI/Nitro.

---

## 3. API CALLS STRUCTURE

### URL Format
```
<HTTP_VERB> /mgmt/api/nextgen/v1/<resource_type>/<resource_name>
<HTTP_VERB> /mgmt/api/nextgen/v1/<resource_type>/<resource_name>/<subresource_type>/<subresource_name>
```

### HTTP Verbs
| Verb   | Semantics |
|--------|-----------|
| GET    | Retrieve one resource (by name) or list all of a type. |
| POST   | Create new resource (fails if exists — 409). Or create/update via desired-state (idempotent when name in URL). Returns 201 on create, 200 on update. |
| PUT    | Update existing resource — full desired-state replacement. Fails if resource does not exist. |
| DELETE | Delete an existing resource. |

### Desired State vs. Incremental
- **Desired State (POST with name in URL / PUT):** Specify the full target config. System reconciles. Adding a server to a 1000-server backend requires listing all 1001.
- **Incremental (POST without name in URL):** Add/create only what is specified. Existing resources not affected.

**Example — desired state (create or update app1):**
```
POST /mgmt/api/nextgen/v1/applications/app1    ← name in URL = desired state
```
**Example — incremental (create new, fail if exists):**
```
POST /mgmt/api/nextgen/v1/applications          ← no name in URL = strict create
```

---

## 4. RESOURCE HIERARCHY

```
Application
├── Frontend (sub-resource, represents one VIP)
│   └── Listener (sub-resource, represents one port on a VIP)
├── Backend (sub-resource, represents a server group)
│   └── Server (sub-resource, individual server IP/port)
└── Route (sub-resource, content-switching rules)

Certificate           (top-level, standalone)
Filter Value Set      (top-level, standalone)
Responder HTML Page   (top-level, standalone)
HTTP Callout          (top-level, standalone)
Config Set            (top-level, standalone)
RBAC Roles & Groups   (top-level, standalone)
```

Reference convention: `<resource_type>_ref` (single), `<resource_type>_refs` (list).

---

## 5. APPLICATIONS

### 5.1 ListApplications
```
GET /mgmt/api/nextgen/v1/applications
Cookie: sessionid=<token>
```
Returns a list of all configured applications.

### 5.2 AddApplication
```
POST /mgmt/api/nextgen/v1/applications
Cookie: sessionid=<token>

{
  "application": {
    "name": "app1",
    "virtual_ip": "70.122.23.11",
    "port": 443,
    "protocol": "HTTPS",
    "default_certificate_ref": "cert1",
    "servers_port": 8080,
    "servers": ["192.168.10.11", "192.168.10.14"]
  }
}
```
Returns **201** on creation. Returns **409** if already exists.

### 5.3 GetApplication
```
GET /mgmt/api/nextgen/v1/applications/{application_name}
Cookie: sessionid=<token>
```

### 5.4 CreateOrUpdateApplication (Desired State)
```
POST /mgmt/api/nextgen/v1/applications/{application_name}
Cookie: sessionid=<token>
```
Idempotent — creates if absent, updates if present.

### 5.5 UpdateApplication
```
PUT /mgmt/api/nextgen/v1/applications/{application_name}
Cookie: sessionid=<token>
```
Full replacement of existing application config. Fails (404) if does not exist.

### 5.6 DeleteApplication
```
DELETE /mgmt/api/nextgen/v1/applications/{application_name}
Cookie: sessionid=<token>
```

### 5.7 GetApplicationConfigStatus
```
GET /mgmt/api/nextgen/v1/applications/{application_name}/config_status
Cookie: sessionid=<token>
```
Returns whether the config has been successfully applied to the data plane. Important when using PIXL filter expressions (not validated until data-plane install).

### 5.8 GetApplicationHealth
```
GET /mgmt/api/nextgen/v1/applications/{application_name}/health
Cookie: sessionid=<token>
```
Returns `configured_state` and `operational_state` for the application and all sub-components (frontends, listeners, backends, servers). App is UP if at least one route where frontend AND backend are both UP.

**Example response (abbreviated):**
```json
{
  "application": {
    "name": "my_app",
    "virtual_ip": "70.122.23.11",
    "configured_state": "ENABLED",
    "operational_state": "UP",
    "backends": [
      {
        "name": "be1",
        "configured_state": "ENABLED",
        "operational_state": "UP",
        "servers": [
          { "ip": "10.102.201.166", "port": 80, "configured_state": "ENABLED", "operational_state": "UP" }
        ]
      }
    ]
  }
}
```

### 5.9 GetApplicationStats
```
GET /mgmt/api/nextgen/v1/applications/{application_name}/statistics
Cookie: sessionid=<token>
```
Returns hits, requests, responses, bytes, connections, and per-sec counters for the app, each frontend/listener, each backend, and each server.

### 5.10 EnableApplication
```
POST /mgmt/api/nextgen/v1/applications/{application_name}/actions/enable
Cookie: sessionid=<token>
```
Allows the application to serve traffic. Reflected in `configured_state: ENABLED` in health response.

### 5.11 DisableApplication
```
POST /mgmt/api/nextgen/v1/applications/{application_name}/actions/disable
Cookie: sessionid=<token>
```
Stops the application from serving traffic. Reflected in `configured_state: DISABLED`.

### 5.12 InstallApplication
```
POST /mgmt/api/nextgen/v1/applications/{application_name}/actions/install
Cookie: sessionid=<token>
```
Installs the application config into the NetScaler data plane (packet engines). Use after an uninstall to re-push config.

### 5.13 UninstallApplication
```
POST /mgmt/api/nextgen/v1/applications/{application_name}/actions/uninstall
Cookie: sessionid=<token>
```
Removes config from data plane but keeps it in Next-Gen API storage. Useful to resolve data-plane config inconsistencies without deleting the resource.

---

## 6. APPLICATION PAYLOAD REFERENCE

### Simple Application (single VIP/port)
```json
{
  "application": {
    "name": "my_app",
    "virtual_ip": "70.122.23.11",
    "port": 443,
    "protocol": "HTTPS",
    "default_certificate_ref": "cert1",
    "servers_port": 8080,
    "servers": ["192.168.10.11", "192.168.10.14"]
  }
}
```

### Application Attributes
| Attribute | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `name` | string | Yes | — | Unique application name |
| `virtual_ip` | IP address | Yes | — | VIP address |
| `port` | integer | No | 443 (HTTPS) or 80 (HTTP) | Listener port |
| `protocol` | string | No | `HTTPS` | `HTTP` or `HTTPS` |
| `default_certificate_ref` | reference | If HTTPS | — | Default TLS cert (serves all SNI) |
| `certificate_refs` | list of references | If HTTPS | — | SNI-matched certificates |
| `servers_port` | integer | No | 80 | Backend server port |
| `servers_protocol` | string | No | HTTP | Backend protocol |
| `servers` | list | Yes | — | Backend server IPs (or objects with ip/port/weight) |
| `load_balancing` | object | No | LEASTCONNECTION, no stickiness | LB algorithm and stickiness |
| `health_check` / `health_checks` | object / list | No | — | Monitor config |
| `rate_limit_settings` | object | No | — | Rate limiting |
| `http_responder` | object | No | — | Respond on behalf of backend |
| `request_transform` | object | No | — | URL/header rewriting |
| `tls_settings` | object | No | MEDIUM | TLS protocol and cipher config |
| `http_config` | object | No | — | HTTP protocol behavior settings |
| `http_to_https_redirect` | boolean | No | false | Redirect HTTP to HTTPS |
| `unavailable_redirect_url` | URL string | No | — | Redirect URL when all servers down |

### Server Object (expanded format)
```json
{ "ip": "192.168.10.16", "port": 8181, "weight": 2 }
```
Weight causes a server to handle proportionally more traffic. Default weight = 1.

### Load Balancing Settings
```json
"load_balancing": {
  "algorithm": "LEASTCONNECTION",
  "stickiness_type": "SOURCEIP",
  "stickiness_timeout": "2hr"
}
```
Algorithms: `ROUNDROBIN`, `LEASTCONNECTION`. Stickiness types: `SOURCEIP`, `COOKIEINSERT`.

### TLS Settings
```json
"tls_settings": {
  "security_level": "HIGH",
  "session_reuse": true,
  "session_timeout": "48s"
}
```
Levels: `HIGH` (TLS 1.3 only, A+), `MEDIUM` (TLS 1.2 + 1.3, default), `LOW` (TLS 1.0–1.3, discouraged). Or specify `tls_protocols` and `tls_cipher_suites` arrays directly.

### Health Check
```json
"health_check": {
  "type": "HTTP",
  "interval": "5s",
  "probe_request_str": "GET /health",
  "probe_healthy_response": { "status_codes": ["200-399"] },
  "num_retries_on_failure": "3",
  "num_retries_on_success": "5"
}
```
Types: `PING` (ICMP), `HTTP`.

### HTTP Responder
```json
"http_responder": {
  "name": "admin_response",
  "filter": "http.request.uri contains 'admin'",
  "response": {
    "raw_response": "'404' Not Found"
  }
}
```
Can also use `"responder_html_page_ref": "page1"` (reference a stored HTML page).

### HTTP Callout in Filter
```
NOT HTTP_CALLOUT(is_ip_allowed)
```

### Request Transform (URL Rewrite)
```json
"request_transform": {
  "name": "rewrite1",
  "filter": "http.request.uri.path equals '/old-path'",
  "action": "replace_url_path",
  "url_path": "/new-path"
}
```

### Audit Logging
```json
"audit_log_defs": [
  {
    "name": "log_port",
    "log_level": "INFORMATIONAL",
    "message": "URL= SOURCE-PORT= DESTINATION-PORT="
  }
]
```
Reference via `"audit_log_ref": "log_port"` on routes, http_responder, transforms, etc.

---

## 7. BACKENDS

Sub-resource of Application. URL pattern:
```
/mgmt/api/nextgen/v1/applications/{app_name}/backends/{backend_name}
```

### 7.1 ListBackends
```
GET /mgmt/api/nextgen/v1/applications/{app_name}/backends
```

### 7.2 GetBackend
```
GET /mgmt/api/nextgen/v1/applications/{app_name}/backends/{backend_name}
```

### 7.3 UpdateBackend
```
PUT /mgmt/api/nextgen/v1/applications/{app_name}/backends/{backend_name}
```

### 7.4 DeleteBackend
```
DELETE /mgmt/api/nextgen/v1/applications/{app_name}/backends/{backend_name}
```

### 7.5 EnableApplicationBackend
```
POST /mgmt/api/nextgen/v1/applications/{app_name}/backends/{backend_name}/actions/enable
```

### 7.6 DisableApplicationBackend
```
POST /mgmt/api/nextgen/v1/applications/{app_name}/backends/{backend_name}/actions/disable
```

### 7.7 ListServers
```
GET /mgmt/api/nextgen/v1/applications/{app_name}/backends/{backend_name}/servers
```

### 7.8 AddServer (Incremental — adds one server without replacing existing ones)
```
POST /mgmt/api/nextgen/v1/applications/{app_name}/backends/{backend_name}/servers

{ "server": "192.168.10.17" }
```
Or with explicit object:
```json
{ "server": { "ip": "192.168.10.17", "port": 8181, "weight": 2 } }
```

### 7.9 UpdateServers (Desired State — replaces entire server list)
```
PUT /mgmt/api/nextgen/v1/applications/{app_name}/backends/{backend_name}/servers

{
  "servers": [
    "192.168.10.11",
    "192.168.10.14",
    "192.168.10.15"
  ]
}
```

### 7.10 DeleteServer
```
DELETE /mgmt/api/nextgen/v1/applications/{app_name}/backends/{backend_name}/servers/{server_ip}
```

### 7.11 EnableApplicationBackendServer
```
POST /mgmt/api/nextgen/v1/applications/{app_name}/backends/{backend_name}/servers/{server_ip}/actions/enable
```

### 7.12 DisableApplicationBackendServer
```
POST /mgmt/api/nextgen/v1/applications/{app_name}/backends/{backend_name}/servers/{server_ip}/actions/disable
```

---

## 8. FRONTENDS

Sub-resource of Application. URL pattern:
```
/mgmt/api/nextgen/v1/applications/{app_name}/frontends/{frontend_name}
```
A Frontend represents one VIP of an application. Applications with a single VIP have an implicit default frontend.

### 8.1 ListFrontends
```
GET /mgmt/api/nextgen/v1/applications/{app_name}/frontends
```

### 8.2 GetFrontend
```
GET /mgmt/api/nextgen/v1/applications/{app_name}/frontends/{frontend_name}
```

### 8.3 UpdateFrontend
```
PUT /mgmt/api/nextgen/v1/applications/{app_name}/frontends/{frontend_name}
```

### 8.4 DeleteFrontend
```
DELETE /mgmt/api/nextgen/v1/applications/{app_name}/frontends/{frontend_name}
```

### 8.5 EnableApplicationFrontend
```
POST /mgmt/api/nextgen/v1/applications/{app_name}/frontends/{frontend_name}/actions/enable
```

### 8.6 DisableApplicationFrontend
```
POST /mgmt/api/nextgen/v1/applications/{app_name}/frontends/{frontend_name}/actions/disable
```

### Frontend Payload Example (multi-VIP application)
```json
{
  "name": "customer_frontend",
  "virtual_ip": "70.122.24.21",
  "default_backend_ref": "billing_servers",
  "listeners": [
    {
      "name": "secure_listener",
      "protocol": "HTTPS",
      "port": 443,
      "default_certificate_ref": "app_cert",
      "http_to_https_redirect": true
    }
  ]
}
```

---

## 9. LISTENERS

Sub-resource of Frontend (which is sub-resource of Application). URL pattern:
```
/mgmt/api/nextgen/v1/applications/{app_name}/frontends/{frontend_name}/listeners/{listener_name}
```
A Listener represents one port on a VIP. Single-port apps have an implicit default listener.

### 9.1 ListListeners
```
GET /mgmt/api/nextgen/v1/applications/{app_name}/frontends/{frontend_name}/listeners
```

### 9.2 GetListener
```
GET /mgmt/api/nextgen/v1/applications/{app_name}/frontends/{frontend_name}/listeners/{listener_name}
```

### 9.3 UpdateListener
```
PUT /mgmt/api/nextgen/v1/applications/{app_name}/frontends/{frontend_name}/listeners/{listener_name}
```

### 9.4 DeleteListener
```
DELETE /mgmt/api/nextgen/v1/applications/{app_name}/frontends/{frontend_name}/listeners/{listener_name}
```

### 9.5 EnableApplicationFrontendListener
```
POST /mgmt/api/nextgen/v1/applications/{app_name}/frontends/{frontend_name}/listeners/{listener_name}/actions/enable
```

### 9.6 DisableApplicationFrontendListener
```
POST /mgmt/api/nextgen/v1/applications/{app_name}/frontends/{frontend_name}/listeners/{listener_name}/actions/disable
```

### Listener Attributes
| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | string | Yes | Listener name |
| `port` | integer | Yes | Port number |
| `protocol` | string | No (defaults to HTTP) | `HTTP` or `HTTPS` |
| `default_certificate_ref` | reference | If HTTPS | Default cert (serves non-SNI clients too) |
| `certificate_refs` | list | If HTTPS | SNI-only certs |
| `http_to_https_redirect` | boolean | No | Auto-redirect HTTP→HTTPS |
| `http_redirect_port` | integer | No | Custom HTTP redirect source port |
| `default_backend_ref` | reference | No | Catch-all backend for unmatched routes |
| `http_config` | object | No | HTTP protocol settings for this listener |
| `tls_settings` | object | No | TLS settings per-listener |

---

## 10. ROUTES

Sub-resource of Application. URL pattern:
```
/mgmt/api/nextgen/v1/applications/{app_name}/routes/{route_name}
```
Routes define content-switching rules. Evaluated **in listed order** — first match wins. Unmatched requests are dropped unless a `default_backend_ref` is set.

### 10.1 ListRoutes
```
GET /mgmt/api/nextgen/v1/applications/{app_name}/routes
```

### 10.2 AddRoute
```
POST /mgmt/api/nextgen/v1/applications/{app_name}/routes

{
  "route": {
    "name": "account_route",
    "filter": "http.request.uri startswith '/account/'",
    "backend_ref": "account_servers"
  }
}
```

### 10.3 GetRoute
```
GET /mgmt/api/nextgen/v1/applications/{app_name}/routes/{route_name}
```

### 10.4 CreateOrUpdateRoute
```
POST /mgmt/api/nextgen/v1/applications/{app_name}/routes/{route_name}
```
Idempotent create-or-update.

### 10.5 UpdateRoute
```
PUT /mgmt/api/nextgen/v1/applications/{app_name}/routes/{route_name}
```

### 10.6 DeleteRoute
```
DELETE /mgmt/api/nextgen/v1/applications/{app_name}/routes/{route_name}
```

### Route Attributes
| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | string | Yes | Route name |
| `filter` | string | No | Wireshark or PIXL expression. Omit to match all. |
| `filter_format` | string | No | `wireshark` (default) or `pixl` |
| `backend_ref` | reference | Yes | Target backend name |
| `frontend_ref` | reference | No | Scope to specific frontend |
| `listener_ref` | reference | No | Scope to specific listener |

---

## 11. CERTIFICATES

Top-level resource. URL pattern:
```
/mgmt/api/nextgen/v1/certificates/{certificate_name}
```

### 11.1 ListCertificates
```
GET /mgmt/api/nextgen/v1/certificates
```

### 11.2 AddCertificate
```
POST /mgmt/api/nextgen/v1/certificates

{
  "certificate": {
    "name": "app1_cert",
    "public_cert": "-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----\n",
    "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
    "passphrase": "optional_passphrase",
    "ca_certs": [
      "-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----\n"
    ]
  }
}
```
> **Tip:** Convert PEM to JSON string with: `jq -sR . mycert.pem` (replaces newlines with `\n`)

### 11.3 GetCertificate
```
GET /mgmt/api/nextgen/v1/certificates/{certificate_name}
```

### 11.4 AddOrUpdateCertificate
```
POST /mgmt/api/nextgen/v1/certificates/{certificate_name}
```
Idempotent create-or-update.

### 11.5 UpdateCertificate
```
PUT /mgmt/api/nextgen/v1/certificates/{certificate_name}
```

### 11.6 DeleteCertificate
```
DELETE /mgmt/api/nextgen/v1/certificates/{certificate_name}
```
> **Note:** Cannot delete a certificate that is currently referenced by an application. Returns 409.

### 11.7 GetCertificateConfigStatus
```
GET /mgmt/api/nextgen/v1/certificates/{certificate_name}/config_status
```

### Certificate Reference Usage
| Attribute | Effect |
|-----------|--------|
| `default_certificate_ref` | Serves all clients regardless of SNI match |
| `certificate_refs` | Only serves clients whose SNI matches a configured cert |
| Both combined | SNI-matched certs used preferentially; default cert is fallback |

---

## 12. CONFIG SETS

Top-level resource for entity-centric (Nitro-based) desired-state config. URL pattern:
```
/mgmt/api/nextgen/v1/config_sets/{config_set_name}
```

### 12.1 GetConfigSets
```
GET /mgmt/api/nextgen/v1/config_sets
```

### 12.2 AddConfigSet
```
POST /mgmt/api/nextgen/v1/config_sets
```

### 12.3 GetConfigSet
```
GET /mgmt/api/nextgen/v1/config_sets/{config_set_name}
```

### 12.4 AddorUpdateConfigSet
```
POST /mgmt/api/nextgen/v1/config_sets/{config_set_name}
```
Idempotent create-or-update.

### 12.5 UpdateConfigSet
```
PUT /mgmt/api/nextgen/v1/config_sets/{config_set_name}
```

### 12.6 DeleteConfigSet
```
DELETE /mgmt/api/nextgen/v1/config_sets/{config_set_name}
```

### 12.7 GetConfigSetStatistics
```
GET /mgmt/api/nextgen/v1/config_sets/{config_set_name}/statistics
```

### 12.8 GetConfigSetConfigStatus
```
GET /mgmt/api/nextgen/v1/config_sets/{config_set_name}/config_status
```

---

## 13. FILTER VALUE SETS

Top-level resource. Used to create reusable named sets of values for use in Wireshark filter expressions (equivalent to Nitro PatSets/DataSets). URL pattern:
```
/mgmt/api/nextgen/v1/filters/value_sets/{value_set_name}
```

### 13.1 GetFilterValueSets
```
GET /mgmt/api/nextgen/v1/filters/value_sets
```

### 13.2 AddFilterValueSet
```
POST /mgmt/api/nextgen/v1/filters/value_sets

{
  "value_set": {
    "name": "valid_hostnames",
    "type": "string",
    "values": ["www.site1", "www.site2", "www.site3"]
  }
}
```
`type` options: `string`, `number`, `ipv4`, `ipv6`.

### 13.3 GetFilterValueSet
```
GET /mgmt/api/nextgen/v1/filters/value_sets/{value_set_name}
```

### 13.4 AddorUpdateFilterValueSet
```
POST /mgmt/api/nextgen/v1/filters/value_sets/{value_set_name}
```
Idempotent create-or-update.

### 13.5 UpdateFilterValueSet
```
PUT /mgmt/api/nextgen/v1/filters/value_sets/{value_set_name}
```

### 13.6 DeleteFilterValueSet
```
DELETE /mgmt/api/nextgen/v1/filters/value_sets/{value_set_name}
```

### 13.7 GetFilterValueSetConfigStatus
```
GET /mgmt/api/nextgen/v1/filters/value_sets/{value_set_name}/config_status
```

### Using Value Sets in Expressions
```
http.host equals_any valid_hostnames
http.request.uri startswith_any allowed_paths
```
Operators for value sets: `equals_any`, `contains_any`, `startswith_any`, `endswith_any`.

---

## 14. HTTP CALLOUTS

Top-level resource. HTTP callouts let NetScaler make HTTP/HTTPS requests to an external service during policy evaluation. URL pattern:
```
/mgmt/api/nextgen/v1/http_callouts/{callout_name}
```

### 14.1 GetHttpCallouts
```
GET /mgmt/api/nextgen/v1/http_callouts
```

### 14.2 AddHttpCallout
```
POST /mgmt/api/nextgen/v1/http_callouts

{
  "http_callout": {
    "name": "is_ip_allowed",
    "callout_request": {
      "method": "POST",
      "scheme": "HTTPS",
      "host": "1.2.3.4",
      "port": 443,
      "path_expression": "/check_valid_ip",
      "headers": [
        { "name": "Content-Type", "value_expression": "application/json" },
        { "name": "api-key", "value_expression": "8395-3c22-abj4-0a29" }
      ],
      "body_expression": "{\"client_ip\": \"\"}"
    },
    "callout_response": {
      "return_value_expression": "http.response.code == 200",
      "return_value_datatype": "boolean",
      "cache_duration": "1min"
    }
  }
}
```

### 14.3 GetHttpCallout
```
GET /mgmt/api/nextgen/v1/http_callouts/{callout_name}
```

### 14.4 AddorUpdateHttpCallout
```
POST /mgmt/api/nextgen/v1/http_callouts/{callout_name}
```
Idempotent create-or-update.

### 14.5 UpdateHttpCallout
```
PUT /mgmt/api/nextgen/v1/http_callouts/{callout_name}
```

### 14.6 DeleteHttpCallout
```
DELETE /mgmt/api/nextgen/v1/http_callouts/{callout_name}
```

### 14.7 GetHttpCalloutConfigStatus
```
GET /mgmt/api/nextgen/v1/http_callouts/{callout_name}/config_status
```

### Using HTTP Callout in a Filter
```json
{
  "http_responder": {
    "name": "ip_check_responder",
    "filter": "NOT HTTP_CALLOUT(is_ip_allowed)",
    "response": { "raw_response": "'403' Forbidden" }
  }
}
```

---

## 15. RESPONDER HTML PAGES

Top-level resource for storing HTML page content used by HTTP Responder. Content is base64-encoded. URL pattern:
```
/mgmt/api/nextgen/v1/responder_html_page/{page_name}
```

### 15.1 GetResponderHtmlPages
```
GET /mgmt/api/nextgen/v1/responder_html_page
```

### 15.2 AddResponderHtmlPage
```
POST /mgmt/api/nextgen/v1/responder_html_page

{
  "responder_html_page": {
    "name": "page1",
    "content": "PGh0bWw+PGhlYWQ+PHRpdGxlPkV4YW1wbGU8L3RpdGxlPjwvaGVhZD48Ym9keT48aDE+SGVsbG8hPC9oMT48L2JvZHk+PC9odG1sPg=="
  }
}
```
`content` is the **base64-encoded** HTML string.

### 15.3 GetResponderHtmlPage
```
GET /mgmt/api/nextgen/v1/responder_html_page/{page_name}
```

### 15.4 AddorUpdateResponderHtmlPage
```
POST /mgmt/api/nextgen/v1/responder_html_page/{page_name}
```
Idempotent create-or-update.

### 15.5 UpdateResponderHtmlPage
```
PUT /mgmt/api/nextgen/v1/responder_html_page/{page_name}
```

### 15.6 DeleteResponderHtmlPage
```
DELETE /mgmt/api/nextgen/v1/responder_html_page/{page_name}
```

### 15.7 GetResponderHtmlPageConfigStatus
```
GET /mgmt/api/nextgen/v1/responder_html_page/{page_name}/config_status
```

### Using an HTML Page in HTTP Responder
```json
"http_responder": {
  "name": "maintenance_page",
  "filter": "http.request.uri contains 'admin'",
  "response": {
    "responder_html_page_ref": "page1"
  }
}
```

---

## 16. RBAC (Role-Based Access Control)

### URL Patterns
```
/mgmt/api/nextgen/v1/roles/{role_name}
/mgmt/api/nextgen/v1/groups/{group_name}/roles/{role_name}
```

### 16.1 GetRoles
```
GET /mgmt/api/nextgen/v1/roles
```

### 16.2 AddRole
```
POST /mgmt/api/nextgen/v1/roles

{
  "role": {
    "name": "apps-admin-role",
    "permissions": [
      {
        "method": "ALL",
        "resources": "/applications/.+"
      }
    ]
  }
}
```
`method` values: `GET`, `POST`, `PUT`, `DELETE`, `ALL`.
`resources` is a regex matching API paths.

### 16.3 GetRole
```
GET /mgmt/api/nextgen/v1/roles/{role_name}
```

### 16.4 AddOrUpdateRole
```
POST /mgmt/api/nextgen/v1/roles/{role_name}
```
Idempotent create-or-update.

### 16.5 UpdateRole
```
PUT /mgmt/api/nextgen/v1/roles/{role_name}
```

### 16.6 DeleteRole
```
DELETE /mgmt/api/nextgen/v1/roles/{role_name}
```
> Cannot delete a role that is still assigned to a group. Remove group assignment first.

### 16.7 GetGroups
```
GET /mgmt/api/nextgen/v1/groups
```
Returns all user groups visible to Next-Gen API.

### 16.8 GetGroupRoles
```
GET /mgmt/api/nextgen/v1/groups/{group_name}/roles
```

### 16.9 AddGroupRole (Assign one role to a group)
```
POST /mgmt/api/nextgen/v1/groups/{group_name}/roles

{
  "role": "apps-admin-role"
}
```

### 16.10 AddGroupRoles (Replace full role list for a group — desired state)
```
PUT /mgmt/api/nextgen/v1/groups/{group_name}/roles

{
  "roles": ["apps-admin-role", "certs-read-role"]
}
```

### 16.11 DeleteGroupRole
```
DELETE /mgmt/api/nextgen/v1/groups/{group_name}/roles/{role_name}
```

### RBAC Behavior
- Logged-in users are restricted to endpoints allowed by roles assigned to their user groups.
- Unauthorized access returns **401**.
- User/group accounts still managed via NetScaler CLI/GUI/Nitro (LDAP/RADIUS also configured there).

---

## 17. WIRESHARK FILTER EXPRESSIONS

Used in `filter` attributes of routes, http_responder, request_transform, etc.

### Supported Fields
| Field | Description |
|-------|-------------|
| `http.host` | Request hostname |
| `http.request.uri` | Full URL |
| `http.request.uri.path` | URL path only |
| `http.request.uri.query` | Query string |
| `http.request.method` | HTTP method (GET, POST, etc.) |
| `http.request.header.cookie` | Cookie header |
| `http.request.header.<name>` | Any request header |

### Operators
| Operator | Aliases | Description |
|----------|---------|-------------|
| `==` | `eq` | Equality |
| `!=` | `ne` | Inequality |
| `>=` | `ge` | Greater or equal |
| `<=` | `le` | Less or equal |
| `>` | `gt` | Greater |
| `<` | `lt` | Less |
| `contains` | | Substring match |
| `startswith` | | Prefix match |
| `endswith` | | Suffix match |
| `equals_any` | | Match against a value set |
| `contains_any` | | Substring match against a value set |
| `startswith_any` | | Prefix match against a value set |
| `endswith_any` | | Suffix match against a value set |
| `and` | | Logical AND |
| `or` | | Logical OR |
| `upper()` | | Convert to uppercase |
| `lower()` | | Convert to lowercase |

### Expression Examples
```
http.host == "www.cloud.com"
http.request.uri startswith '/account/'
http.request.uri contains '/checkout/'
http.request.method == "POST"
lower(http.host) == "www.cloud.com" and http.request.header.user-agent contains "mobile"
http.host equals_any valid_hostnames
```

### PIXL Alternative
Set `"filter_format": "pixl"` to use native NetScaler PIXL expressions:
```json
{
  "filter": "HTTP.REQ.URL.PATH_AND_QUERY.CONTAINS(\"admin\")",
  "filter_format": "pixl"
}
```
> **Warning:** PIXL expressions are not validated until data-plane install. Always check `config_status` after applying PIXL-based configs.

---

## 18. ERROR HANDLING

### HTTP Status Codes
| Code | Meaning |
|------|---------|
| 200 | Success (GET, POST update, PUT) |
| 201 | Resource created (POST) |
| 400 | Bad request / validation error |
| 401 | Unauthorized — auth failed, session expired, or RBAC denied |
| 403 | Forbidden — user lacks permission for this resource/method |
| 404 | Resource not found |
| 406 | Only JSON responses supported |
| 409 | Conflict — resource already exists, or referenced by other resources |
| 415 | Only JSON request payloads supported |
| 422 | Validation failed |
| 500 | Internal server error |

### Error Response Format
```json
{
  "errorcode": 400,
  "errormessage": "Validation Error",
  "details": [
    {
      "instance": "{'name': 'color_app', 'virtual_ip': '10.102.201.171', ...}",
      "message": "'certificate_ref' is a required property for 'protocol':'HTTPS'"
    }
  ]
}
```

### Internal Error Codes (Selected)
| HTTP | Code | Message |
|------|------|---------|
| 400 | 1000 | Bad Request |
| 400 | 1001 | Invalid JSON data |
| 400 | 1002 | Resource name different in URL and payload |
| 401 | 1101 | Session expired — please login again |
| 401 | 1102 | User not authorized for this operation |
| 401 | 1104 | Invalid username or password |
| 401 | 1105 | Operation not permitted on HA secondary node |
| 404 | 1201–1214 | Specific resource not found (app, frontend, listener, backend, server, route, cert, role, value set, HTML page, HTTP callout) |
| 409 | 1400 | Resource already exists |
| 409 | 1402 | Cannot delete — resource referenced by others |
| 409 | 1403 | Cannot uninstall — resource referenced by others |
| 409 | 1420 | Blocking operation in progress — retry later |
| 422 | 2000 | Validation Failed |
| 422 | 3001 | Cannot delete — last remaining resource of its kind |
| 500 | 1600 | Internal Server Error |

---

## 19. COMPLETE ENDPOINT QUICK REFERENCE

| Category | Operation | Method | URL |
|----------|-----------|--------|-----|
| **Auth** | Login | POST | `/mgmt/api/nextgen/v1/login` |
| **Auth** | Logout | POST | `/mgmt/api/nextgen/v1/logout` |
| **Applications** | List | GET | `/mgmt/api/nextgen/v1/applications` |
| **Applications** | Add | POST | `/mgmt/api/nextgen/v1/applications` |
| **Applications** | Get | GET | `/mgmt/api/nextgen/v1/applications/{name}` |
| **Applications** | Create or Update | POST | `/mgmt/api/nextgen/v1/applications/{name}` |
| **Applications** | Update | PUT | `/mgmt/api/nextgen/v1/applications/{name}` |
| **Applications** | Delete | DELETE | `/mgmt/api/nextgen/v1/applications/{name}` |
| **Applications** | Config Status | GET | `/mgmt/api/nextgen/v1/applications/{name}/config_status` |
| **Applications** | Health | GET | `/mgmt/api/nextgen/v1/applications/{name}/health` |
| **Applications** | Statistics | GET | `/mgmt/api/nextgen/v1/applications/{name}/statistics` |
| **Applications** | Enable | POST | `/mgmt/api/nextgen/v1/applications/{name}/actions/enable` |
| **Applications** | Disable | POST | `/mgmt/api/nextgen/v1/applications/{name}/actions/disable` |
| **Applications** | Install | POST | `/mgmt/api/nextgen/v1/applications/{name}/actions/install` |
| **Applications** | Uninstall | POST | `/mgmt/api/nextgen/v1/applications/{name}/actions/uninstall` |
| **Backends** | List | GET | `/mgmt/api/nextgen/v1/applications/{app}/backends` |
| **Backends** | Get | GET | `/mgmt/api/nextgen/v1/applications/{app}/backends/{name}` |
| **Backends** | Update | PUT | `/mgmt/api/nextgen/v1/applications/{app}/backends/{name}` |
| **Backends** | Delete | DELETE | `/mgmt/api/nextgen/v1/applications/{app}/backends/{name}` |
| **Backends** | Enable | POST | `/mgmt/api/nextgen/v1/applications/{app}/backends/{name}/actions/enable` |
| **Backends** | Disable | POST | `/mgmt/api/nextgen/v1/applications/{app}/backends/{name}/actions/disable` |
| **Servers** | List | GET | `/mgmt/api/nextgen/v1/applications/{app}/backends/{be}/servers` |
| **Servers** | Add (incremental) | POST | `/mgmt/api/nextgen/v1/applications/{app}/backends/{be}/servers` |
| **Servers** | Update (desired state) | PUT | `/mgmt/api/nextgen/v1/applications/{app}/backends/{be}/servers` |
| **Servers** | Delete | DELETE | `/mgmt/api/nextgen/v1/applications/{app}/backends/{be}/servers/{ip}` |
| **Servers** | Enable | POST | `/mgmt/api/nextgen/v1/applications/{app}/backends/{be}/servers/{ip}/actions/enable` |
| **Servers** | Disable | POST | `/mgmt/api/nextgen/v1/applications/{app}/backends/{be}/servers/{ip}/actions/disable` |
| **Frontends** | List | GET | `/mgmt/api/nextgen/v1/applications/{app}/frontends` |
| **Frontends** | Get | GET | `/mgmt/api/nextgen/v1/applications/{app}/frontends/{name}` |
| **Frontends** | Update | PUT | `/mgmt/api/nextgen/v1/applications/{app}/frontends/{name}` |
| **Frontends** | Delete | DELETE | `/mgmt/api/nextgen/v1/applications/{app}/frontends/{name}` |
| **Frontends** | Enable | POST | `/mgmt/api/nextgen/v1/applications/{app}/frontends/{name}/actions/enable` |
| **Frontends** | Disable | POST | `/mgmt/api/nextgen/v1/applications/{app}/frontends/{name}/actions/disable` |
| **Listeners** | List | GET | `/mgmt/api/nextgen/v1/applications/{app}/frontends/{fe}/listeners` |
| **Listeners** | Get | GET | `/mgmt/api/nextgen/v1/applications/{app}/frontends/{fe}/listeners/{name}` |
| **Listeners** | Update | PUT | `/mgmt/api/nextgen/v1/applications/{app}/frontends/{fe}/listeners/{name}` |
| **Listeners** | Delete | DELETE | `/mgmt/api/nextgen/v1/applications/{app}/frontends/{fe}/listeners/{name}` |
| **Listeners** | Enable | POST | `/mgmt/api/nextgen/v1/applications/{app}/frontends/{fe}/listeners/{name}/actions/enable` |
| **Listeners** | Disable | POST | `/mgmt/api/nextgen/v1/applications/{app}/frontends/{fe}/listeners/{name}/actions/disable` |
| **Routes** | List | GET | `/mgmt/api/nextgen/v1/applications/{app}/routes` |
| **Routes** | Add | POST | `/mgmt/api/nextgen/v1/applications/{app}/routes` |
| **Routes** | Get | GET | `/mgmt/api/nextgen/v1/applications/{app}/routes/{name}` |
| **Routes** | Create or Update | POST | `/mgmt/api/nextgen/v1/applications/{app}/routes/{name}` |
| **Routes** | Update | PUT | `/mgmt/api/nextgen/v1/applications/{app}/routes/{name}` |
| **Routes** | Delete | DELETE | `/mgmt/api/nextgen/v1/applications/{app}/routes/{name}` |
| **Certificates** | List | GET | `/mgmt/api/nextgen/v1/certificates` |
| **Certificates** | Add | POST | `/mgmt/api/nextgen/v1/certificates` |
| **Certificates** | Get | GET | `/mgmt/api/nextgen/v1/certificates/{name}` |
| **Certificates** | Add or Update | POST | `/mgmt/api/nextgen/v1/certificates/{name}` |
| **Certificates** | Update | PUT | `/mgmt/api/nextgen/v1/certificates/{name}` |
| **Certificates** | Delete | DELETE | `/mgmt/api/nextgen/v1/certificates/{name}` |
| **Certificates** | Config Status | GET | `/mgmt/api/nextgen/v1/certificates/{name}/config_status` |
| **Config Sets** | Get All | GET | `/mgmt/api/nextgen/v1/config_sets` |
| **Config Sets** | Add | POST | `/mgmt/api/nextgen/v1/config_sets` |
| **Config Sets** | Get | GET | `/mgmt/api/nextgen/v1/config_sets/{name}` |
| **Config Sets** | Add or Update | POST | `/mgmt/api/nextgen/v1/config_sets/{name}` |
| **Config Sets** | Update | PUT | `/mgmt/api/nextgen/v1/config_sets/{name}` |
| **Config Sets** | Delete | DELETE | `/mgmt/api/nextgen/v1/config_sets/{name}` |
| **Config Sets** | Statistics | GET | `/mgmt/api/nextgen/v1/config_sets/{name}/statistics` |
| **Config Sets** | Config Status | GET | `/mgmt/api/nextgen/v1/config_sets/{name}/config_status` |
| **Value Sets** | Get All | GET | `/mgmt/api/nextgen/v1/filters/value_sets` |
| **Value Sets** | Add | POST | `/mgmt/api/nextgen/v1/filters/value_sets` |
| **Value Sets** | Get | GET | `/mgmt/api/nextgen/v1/filters/value_sets/{name}` |
| **Value Sets** | Add or Update | POST | `/mgmt/api/nextgen/v1/filters/value_sets/{name}` |
| **Value Sets** | Update | PUT | `/mgmt/api/nextgen/v1/filters/value_sets/{name}` |
| **Value Sets** | Delete | DELETE | `/mgmt/api/nextgen/v1/filters/value_sets/{name}` |
| **Value Sets** | Config Status | GET | `/mgmt/api/nextgen/v1/filters/value_sets/{name}/config_status` |
| **HTTP Callouts** | Get All | GET | `/mgmt/api/nextgen/v1/http_callouts` |
| **HTTP Callouts** | Add | POST | `/mgmt/api/nextgen/v1/http_callouts` |
| **HTTP Callouts** | Get | GET | `/mgmt/api/nextgen/v1/http_callouts/{name}` |
| **HTTP Callouts** | Add or Update | POST | `/mgmt/api/nextgen/v1/http_callouts/{name}` |
| **HTTP Callouts** | Update | PUT | `/mgmt/api/nextgen/v1/http_callouts/{name}` |
| **HTTP Callouts** | Delete | DELETE | `/mgmt/api/nextgen/v1/http_callouts/{name}` |
| **HTTP Callouts** | Config Status | GET | `/mgmt/api/nextgen/v1/http_callouts/{name}/config_status` |
| **HTML Pages** | Get All | GET | `/mgmt/api/nextgen/v1/responder_html_page` |
| **HTML Pages** | Add | POST | `/mgmt/api/nextgen/v1/responder_html_page` |
| **HTML Pages** | Get | GET | `/mgmt/api/nextgen/v1/responder_html_page/{name}` |
| **HTML Pages** | Add or Update | POST | `/mgmt/api/nextgen/v1/responder_html_page/{name}` |
| **HTML Pages** | Update | PUT | `/mgmt/api/nextgen/v1/responder_html_page/{name}` |
| **HTML Pages** | Delete | DELETE | `/mgmt/api/nextgen/v1/responder_html_page/{name}` |
| **HTML Pages** | Config Status | GET | `/mgmt/api/nextgen/v1/responder_html_page/{name}/config_status` |
| **RBAC Roles** | Get All | GET | `/mgmt/api/nextgen/v1/roles` |
| **RBAC Roles** | Add | POST | `/mgmt/api/nextgen/v1/roles` |
| **RBAC Roles** | Get | GET | `/mgmt/api/nextgen/v1/roles/{name}` |
| **RBAC Roles** | Add or Update | POST | `/mgmt/api/nextgen/v1/roles/{name}` |
| **RBAC Roles** | Update | PUT | `/mgmt/api/nextgen/v1/roles/{name}` |
| **RBAC Roles** | Delete | DELETE | `/mgmt/api/nextgen/v1/roles/{name}` |
| **RBAC Groups** | Get Groups | GET | `/mgmt/api/nextgen/v1/groups` |
| **RBAC Groups** | Get Group Roles | GET | `/mgmt/api/nextgen/v1/groups/{group}/roles` |
| **RBAC Groups** | Add Group Role | POST | `/mgmt/api/nextgen/v1/groups/{group}/roles` |
| **RBAC Groups** | Set Group Roles | PUT | `/mgmt/api/nextgen/v1/groups/{group}/roles` |
| **RBAC Groups** | Delete Group Role | DELETE | `/mgmt/api/nextgen/v1/groups/{group}/roles/{role}` |

---

## 20. IMPORTANT BEHAVIORAL RULES FOR THE COPILOT

1. **Always authenticate first.** No API call works without a valid `sessionid` cookie.
2. **POST without name = strict create** (fails if exists). **POST with name in URL = create or update** (idempotent). **PUT = update only** (fails if not found).
3. **`clear ns config basic/extended` does NOT clear Next-Gen API data.** Only `clear ns config full` does.
4. **Certificates must be created before applications that reference them.** Deleting a cert used by an app returns 409.
5. **Routes are evaluated in order.** First match wins. Unmatched requests are dropped unless `default_backend_ref` is set.
6. **Config is async on the data plane.** After a write operation, check `/config_status` before assuming the data plane is updated.
7. **PIXL filter expressions are not validated at commit time.** Always check `config_status` after creating/updating resources with PIXL filters.
8. **HA secondary node cannot accept write operations.** Returns error 1105.
9. **All requests and responses use JSON.** `Content-Type: application/json` must be present on POST/PUT requests.
10. **Next-Gen API configs are not visible in `ns.conf`** and survive `save ns config` + reboot intact.
11. **Disable vs. Uninstall difference:**
    - `disable` — keeps config in data plane, marks VIP as DOWN (no traffic).
    - `uninstall` — removes config from data plane entirely; resource stays in Next-Gen storage.
12. **Time durations always require units.** e.g. `"5min"`, `"300s"`, `"2hr"`, `"48s"`, `"100ms"`.
13. **PEM certificates must have newlines escaped as `\n` in JSON payloads.** Use `jq -sR . cert.pem` to convert.
14. **A role must be removed from all groups before it can be deleted.**
15. **Responder HTML page content must be base64-encoded.**
