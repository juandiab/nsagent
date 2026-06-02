# NSAgent

**JPilot** — an AI-assisted management platform for Citrix NetScaler ADC appliances. Register appliances, configure AI providers, and use the JPilot chat that reads and writes configuration through the **NetScaler Next-Gen API**, **read-only NITRO**, and **SSH CLI** — with official documentation baked into memory files so the assistant does not invent syntax.

Repository: [github.com/juandiab/nsagent](https://github.com/juandiab/nsagent)

> **Disclaimer:** NSAgent is an independent project and is not affiliated with, endorsed by, or sponsored by Citrix Systems, Inc. NetScaler is a trademark of Citrix Systems, Inc.

**Current release:** `v0.02` — NetScaler diagnostics (ICMP, TCP port checks, nsconmsg), auth improvements, and JPilot auto port-check.

## Features

- **Appliance inventory** — store NetScaler hosts and encrypted credentials (Fernet).
- **AI provider management** — OpenAI, Anthropic, Gemini, Grok, LM Studio, and OpenAI-compatible endpoints.
- **JPilot chat** — tool-calling agent bound to the selected appliance; credentials never sent to the LLM.
- **MCP server** — Model Context Protocol tools for Next-Gen API, classic CLI over SSH, NITRO helpers, and diagnostics.
- **Memory-guided RAG** — `netscaler_nextgen_api_memory.md` and `netscaler_adc_cli_memory.md` gate API/CLI usage before execution.
- **Classic + Next-Gen** — list virtual servers from Next-Gen applications and classic `lbvserver`; create apps via Next-Gen or multi-step LB setup via CLI.
- **Authentication** — password login for all users; optional passkey (WebAuthn) sign-in after registration in Settings → Security.
- **User management** — admin CRUD for users (roles `admin` / `user`), initial password on create, passkey count and removal.
- **NetScaler diagnostics** — ICMP ping/traceroute, TCP port reachability via telnet from the appliance shell, and read-only `nsconmsg` performance/event collection.

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌──────────────────┐
│  Vue 3 UI   │────▶│  Backend API │────▶│ MCP Server  │────▶│ NetScaler ADC    │
│  (5173)     │     │  FastAPI     │     │  (8001)     │     │ Next-Gen / SSH   │
└─────────────┘     └──────┬───────┘     └─────────────┘     └──────────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │  MongoDB    │
                    └─────────────┘
```

| Service      | Port  | Role                                      |
|--------------|-------|-------------------------------------------|
| Frontend     | 5173  | Vue 3 + PrimeVue admin UI and JPilot     |
| Backend API  | 8000  | Auth, CRUD, JPilot orchestration, MCP proxy |
| MCP Server   | 8001  | NetScaler tool execution (SSE-capable)    |
| MongoDB      | 27017 | Settings, appliances, AI providers, users |

## Prerequisites

- Docker and Docker Compose
- NetScaler ADC with **Next-Gen API** enabled (`enable ns nextgenapi`) for API tools
- SSH access to the appliance for classic CLI and diagnostic tools (port 22)
- Python 3.12+ (optional, only to generate a Fernet key locally)

## Quick start

1. **Generate an encryption key**

   ```bash
   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   ```

2. **Configure environment**

   ```bash
   cp .env.example .env
   ```

   Edit `.env`:

   | Variable                 | Description                          |
   |--------------------------|--------------------------------------|
   | `NSAGENT_ENCRYPTION_KEY` | Fernet key for appliance credentials |
   | `JWT_SECRET_KEY`         | Secret for session JWTs              |
   | `ADMIN_USERNAME`         | Initial admin user (seeded once)     |
   | `ADMIN_PASSWORD`         | Initial admin password               |
   | `WEBAUTHN_RP_ID`         | WebAuthn RP ID (usually `localhost` or your hostname) |
   | `WEBAUTHN_ORIGIN`        | Exact UI origin (e.g. `http://localhost:5173`) |
   | `CORS_ORIGINS`           | Comma-separated allowed browser origins |

3. **Start the stack**

   ```bash
   docker compose up --build
   ```

4. **Open the UI**

   - App: [http://localhost:5173](http://localhost:5173) or [http://127.0.0.1:5173](http://127.0.0.1:5173)
   - Default login: `admin` / `admin` (change via `.env` before first run)

5. **Configure**

   - **NetScalers** — add your appliance (name, host, API/SSH user and password).
   - **AI Providers** — add an LLM provider and set it as default.
   - **Settings → MCP** — tool toggles, **SSH fallback** (required for diagnostics), timeouts.
   - **Settings → Security** — register an optional passkey after password login.
   - **Users** (admin) — create users with initial passwords.
   - **JPilot** — select an appliance and ask questions or request changes.

## Authentication

| Flow | Description |
|------|-------------|
| **Password login** | Primary sign-in via `POST /auth/login`. Required for all users. |
| **Passkey login** | Optional on the login screen if the user has registered passkeys. |
| **Passkey registration** | Authenticated users register in **Settings → Security** (not from the login page). |
| **Bootstrap admin** | Seeded from `ADMIN_USERNAME` / `ADMIN_PASSWORD` on first startup. |

WebAuthn and CORS origins must match how users open the UI (see `.env.example`).

## JPilot behavior

The orchestrator enforces:

1. **`search_netscaler_nextgen_api`** before Next-Gen API tools.
2. **`search_netscaler_cli_reference`** before SSH/CLI write tools.
3. **Tool execution** for config changes — the model must call `netscaler_run_cli_command` or `netscaler_run_cli_commands`, not only list commands.
4. **Confirmation** for destructive CLI/API operations (`rm`, `DELETE`, `unbind`, etc.) via `confirmed=true` after user approval.
5. **Diagnostics run immediately** — no memory search required for ping, traceroute, TCP port checks, or nsconmsg.

### Connectivity and diagnostics routing

| User question | Tool | Notes |
|---------------|------|-------|
| Can the appliance ping / reach host (no port)? | `netscaler_run_diagnostic` | `operation`: `ping`, `ping6`, `traceroute`, `traceroute6` |
| Is port N open on host? / reach `IP:PORT`? | `netscaler_telnet` or `netscaler_run_diagnostic` | `operation`: `tcp_port`, plus `port` |
| Performance stats, counters, event logs | `netscaler_collect_nsconmsg` | Read-only `/netscaler/nsconmsg` over SSH |

**Auto TCP port check:** when a JPilot message includes a host and port (e.g. `192.168.20.36:1234`), the backend runs `netscaler_telnet` automatically and returns the verdict — no need for the LLM to choose the tool.

**NetScaler ADC note:** TCP port checks use `/usr/bin/telnet` via `shell sh -c 'telnet HOST PORT </dev/null'`. NetScaler does not ship `nc`/netcat or GNU `timeout`. The CLI may append `ERROR: Export failed` after shell commands; ignore that when telnet output shows `Connected to` or `Connection refused`.

Example — classic LB virtual server with service group:

```text
add lb vserver webserver_02 HTTP 192.168.20.227 80
add serviceGroup webserver_02_sg HTTP
bind serviceGroup webserver_02_sg 192.168.20.36 5173
bind lb vserver webserver_02 -serviceGroupName webserver_02_sg
save ns config
```

JPilot runs these via **`netscaler_run_cli_commands`** in one tool call after CLI reference lookup.

## MCP tools

### Configuration and inventory

| Tool | Description |
|------|-------------|
| `netscaler_test_connection` | Next-Gen API login test |
| `netscaler_get_system_info` | Management IP, version, hostname, serial |
| `netscaler_list_applications` | Next-Gen applications only |
| `netscaler_list_virtual_servers` | Next-Gen apps + classic NITRO `lbvserver` |
| `netscaler_list_virtual_ips` | VIPs from Next-Gen applications |
| `netscaler_list_ip_addresses` | NSIP, SNIP, VIP, servers (Next-Gen + NITRO) |

### Next-Gen API and classic CLI

| Tool | Description |
|------|-------------|
| `netscaler_nextgen_get` | Read-only GET on any Next-Gen path |
| `netscaler_nextgen_request` | GET/POST/PUT/DELETE on Next-Gen paths |
| `netscaler_create_application` | POST `/applications` (VIP + backends) |
| `netscaler_add_ip_address` | Classic VIP/SNIP/NSIP via NITRO |
| `netscaler_ssh_run_command` | Read-only CLI (`show` / `stat` / `get`) |
| `netscaler_run_cli_command` | Single classic CLI command (read or write) |
| `netscaler_run_cli_commands` | Ordered sequence of CLI commands (multi-step setup) |

### Diagnostics (v0.02)

| Tool | Description |
|------|-------------|
| `netscaler_run_diagnostic` | ICMP/path diagnostics: `ping`, `ping6`, `traceroute`, `traceroute6`, or **`tcp_port`** (with `port`) |
| `netscaler_telnet` | TCP port reachability from the appliance via telnet; returns verdict **`open`**, **`refused`**, or **`no_response`** |
| `netscaler_collect_nsconmsg` | Read-only performance/event collection via `/netscaler/nsconmsg` (`current`, `stats`, `event`, `memstats`, etc.) |

Enable or disable tools under **Settings → MCP Server**. **SSH fallback must be enabled** for diagnostic tools.

## Memory files

Official-syntax references mounted into the backend (edit at repo root):

- `netscaler_nextgen_api_memory.md` — Next-Gen API endpoints, payloads, behavioral rules
- `netscaler_adc_cli_memory.md` — ADC CLI namespaces, commands, behavioral rules

JPilot search tools read these before executing NetScaler write operations.

## API endpoints (backend)

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/health` | Health check |
| `POST` | `/auth/login` | Password login |
| `GET` | `/auth/me` | Current user |
| `POST` | `/auth/logout` | Logout |
| `POST` | `/auth/webauthn/status` | Passkey availability for username |
| `POST` | `/auth/webauthn/register/begin\|finish` | Register passkey (authenticated) |
| `POST` | `/auth/webauthn/login/begin\|finish` | Passkey sign-in |
| `GET/POST/PUT/DELETE` | `/users` | User management (admin) |
| `DELETE` | `/users/{id}/passkeys/{passkeyId}` | Remove a user's passkey |
| `GET/POST` | `/appliances` | Appliance CRUD |
| `GET/POST` | `/ai-providers` | AI provider CRUD |
| `GET/PUT` | `/mcp/config` | MCP settings |
| `GET` | `/mcp/tools` | Enabled MCP tools |
| `GET` | `/mcp/status` | MCP server online status |
| `POST` | `/copilot/chat` | JPilot chat with tool traces |
| `GET` | `/copilot/status` | JPilot readiness (default provider) |

## Development

Source is bind-mounted into containers; **Uvicorn `--reload`** and **Vite HMR** pick up changes without rebuild.

```bash
docker compose up
```

Health checks:

- Backend: [http://localhost:8000/health](http://localhost:8000/health)
- MCP: [http://localhost:8001/health](http://localhost:8001/health)
- MCP tools: [http://localhost:8001/tools](http://localhost:8001/tools)

After changing Python dependencies in `requirements.txt`, rebuild the affected image:

```bash
docker compose build backend-api mcp-server && docker compose up -d backend-api mcp-server
```

### Project layout

```
├── frontend/          # Vue 3 + PrimeVue UI
├── backend-api/       # FastAPI backend, JPilot orchestrator
├── mcp-server/        # MCP NetScaler tool server
├── docker-compose.yml
├── netscaler_nextgen_api_memory.md
├── netscaler_adc_cli_memory.md
└── .env.example
```

## Production notes

For production images, remove bind-mount volume lines for `frontend`, `backend-api`, and `mcp-server` in `docker-compose.yml` so containers use code baked into each Dockerfile. Use strong secrets, TLS in front of the UI/API, restrict MongoDB network access, and set `WEBAUTHN_RP_ID`, `WEBAUTHN_ORIGIN`, and `CORS_ORIGINS` to your real hostname.

## License

[MIT](LICENSE) — see [LICENSE](LICENSE) for details.

Copyright (c) 2026 [juandiab](https://github.com/juandiab).
