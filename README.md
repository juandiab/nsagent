# NSAgent

**JPilot** — an AI-assisted management platform for Citrix NetScaler ADC appliances. Register appliances, configure AI providers, and use the JPilot chat that reads and writes configuration through the **NetScaler Next-Gen API**, **read-only NITRO**, and **SSH CLI** — with official documentation baked into memory files so the assistant does not invent syntax.

Repository: [github.com/juandiab/nsagent](https://github.com/juandiab/nsagent)

> **Disclaimer:** NSAgent is an independent project and is not affiliated with, endorsed by, or sponsored by Citrix Systems, Inc. NetScaler is a trademark of Citrix Systems, Inc.

**Current release:** `v0.05` — guided LB forms, memory gates, SSL CSR tools, password reset, expanded LLM providers, CLI reference upgrades, and JPilot UX improvements.

## Features

- **Appliance inventory** — store NetScaler hosts and encrypted credentials (Fernet).
- **AI provider management** — OpenAI, Anthropic, Gemini, Grok, DeepSeek, LM Studio, and OpenAI-compatible endpoints.
- **JPilot chat** — tool-calling agent bound to the selected appliance; credentials never sent to the LLM.
- **MCP server** — Model Context Protocol tools for Next-Gen API, classic CLI over SSH, NITRO helpers, diagnostics, and SSL key/CSR generation.
- **Memory-guided RAG** — `netscaler_nextgen_api_memory.md` and `netscaler_adc_cli_memory.md` gate API/CLI usage before execution.
- **Classic + Next-Gen** — list virtual servers from Next-Gen applications and classic `lbvserver`; create apps via Next-Gen or multi-step LB setup via CLI.
- **Guided load balancer forms** — JPilot can embed interactive `jpilot-form` blocks in chat (VIP, service type, backends, monitors); submissions drive CLI execution after reference lookup.
- **Smart form routing** — responder, rewrite, transform, and other policy-on-vserver requests do not trigger the LB creation form.
- **Authentication** — password login for all users; optional passkey (WebAuthn) sign-in after registration in Settings → Security.
- **Password reset** — admins send email reset codes (SMTP); users complete reset at `/reset-password`.
- **User management** — admin CRUD for users (roles `admin` / `user`), email for resets, initial password on create, passkey count and removal.
- **SSL certificate tools** — generate CSRs or self-signed certificates on the appliance (UI + API + MCP).
- **NetScaler diagnostics** — ICMP ping/traceroute, TCP port reachability via telnet from the appliance shell, and read-only `nsconmsg` performance/event collection.
- **Optional Brave Search** — domain-restricted web augmentation when local memory/docs are weak (Settings → Platform).
- **Dashboard shortcuts** — recommended JPilot prompts and links (health summary, list IPs/vservers, diagnostics, guided LB).

## What's new in v0.05

| Area | Highlights |
|------|------------|
| **JPilot forms** | `ChatConfigForm` in chat; backend parses `jpilot-form` JSON; default classic LB form when creating vservers; workload-aware defaults (StoreFront, Delivery Controllers). |
| **Form heuristics** | LB form only for real provisioning requests — not responder/rewrite/redirect/bind-to-existing-vserver work. |
| **Memory gates** | `search_netscaler_nextgen_api` required before Next-Gen inventory tools; `search_netscaler_cli_reference` before SSH/CLI writes; destructive ops need `confirmed=true`. |
| **Orchestrator** | Stronger tool-execution nudges, retry hints, discovery vs config-change detection, improved tool traces in the UI. |
| **CLI reference** | Command index, expanded catalog, richer memory search and recommended commands for JPilot. |
| **System info** | Firmware/version via NITRO `nsversion` when Next-Gen summary is incomplete. |
| **SSL tools** | `POST /ssl/generate-csr`, MCP CSR/self-signed generation on appliance via OpenSSL shell. |
| **Auth** | User email field, admin-triggered reset codes, public reset-password page. |
| **AI providers** | Grok (xAI), DeepSeek, LM Studio, OpenAI-Compatible with in-app setup hints. |
| **UI** | Dashboard actions, SSL CSR page, pricing/plans view, login/reset flows, session and chat polish. |

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
- SMTP server (optional, for password reset emails)

## Quick start

The only prerequisite is **Docker** (Docker Desktop on Mac/Windows, Docker Engine on
Linux). The installer downloads the project and generates secrets, the TLS certificate,
and `.env` for you.

**macOS / Linux**

```bash
curl -fsSL https://raw.githubusercontent.com/juandiab/nsagent/main/get.sh | bash
```

**Windows (PowerShell)**

```powershell
irm https://raw.githubusercontent.com/juandiab/nsagent/main/get.ps1 | iex
```

(Already cloned the repo? Just run `./install.sh` — or `.\install.ps1` on Windows — from
the project root.)

Then:

1. Open **https://localhost:9443** (the installer uses a self-signed certificate, so
   accept the one-time browser warning).
2. Complete the wizard: admin account, domain, TLS (self-signed or your own cert), and
   optional SMTP.
3. On the **Review** step, **save the generated `NSAGENT_ENCRYPTION_KEY`** — it is
   required to restore or migrate the install and cannot be recovered.
4. Click **Install JPilot**. The wizard writes `.env` and `nginx/ssl/`, and your
   terminal automatically launches the full stack.
5. Open **https://&lt;your-domain&gt;** and sign in with the admin account you created.

To reconfigure an existing install (overwrites `.env`):

```bash
./install.sh --reconfigure      # macOS / Linux
.\install.ps1 -Reconfigure      # Windows (PowerShell)
```

> The installer generates `NSAGENT_ENCRYPTION_KEY` (Fernet) and `JWT_SECRET_KEY`
> automatically and derives the WebAuthn, CORS, and API-URL settings from the domain
> you choose. See [Manual setup](#manual-setup-advanced) below if you prefer to
> configure `.env` by hand.

After first login:

   - **NetScalers** — add your appliance (name, host, API/SSH user and password).
   - **AI Providers** — add an LLM provider and set it as default.
   - **Settings → MCP** — tool toggles, **SSH fallback** (required for diagnostics and SSL shell), timeouts.
   - **Settings → Platform** — optional Brave Search API key for JPilot doc augmentation.
   - **Settings → Security** — register an optional passkey after password login.
   - **Users** (admin) — create users with email (for password reset) and initial passwords.
   - **SSL Certificate Tools** — generate CSR or self-signed cert on an appliance.
   - **JPilot** — select an appliance and ask questions or request changes.

### Manual setup (advanced)

Prefer to configure things by hand instead of the wizard? You can:

1. **Generate an encryption key**

   ```bash
   python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   ```

2. **Configure environment** — `cp .env.example .env` and edit:

   | Variable                 | Description                          |
   |--------------------------|--------------------------------------|
   | `NSAGENT_ENCRYPTION_KEY` | Fernet key for appliance credentials |
   | `JWT_SECRET_KEY`         | Secret for session JWTs              |
   | `ADMIN_USERNAME`         | Initial admin user (seeded once)     |
   | `ADMIN_PASSWORD`         | Initial admin password               |
   | `NGINX_HOSTNAME`         | Public hostname for nginx TLS        |
   | `WEBAUTHN_RP_ID`         | WebAuthn RP ID (usually your hostname or `localhost`) |
   | `WEBAUTHN_ORIGIN`        | Exact UI origin (e.g. `https://your-domain`) |
   | `CORS_ORIGINS`           | Comma-separated allowed browser origins |
   | `SMTP_*`                 | Optional — required for email password reset |
   | `PASSWORD_RESET_LOG_CODES` | Dev only: log reset codes to backend logs |

3. **Provide TLS certificates** — place `cert.crt` and `cert.key` in `nginx/ssl/`
   (see [nginx/ssl/README.md](nginx/ssl/README.md)). nginx will not start without them.

4. **Start the stack** — `docker compose up --build`, then open `https://<NGINX_HOSTNAME>`.

## Authentication

| Flow | Description |
|------|-------------|
| **Password login** | Primary sign-in via `POST /auth/login`. Required for all users. |
| **Passkey login** | Optional on the login screen if the user has registered passkeys. |
| **Passkey registration** | Authenticated users register in **Settings → Security** (not from the login page). |
| **Password reset** | Admin sends a code from **Users**; user opens `/reset-password` and confirms via `POST /auth/password-reset/confirm`. |
| **Bootstrap admin** | Seeded from `ADMIN_USERNAME` / `ADMIN_PASSWORD` on first startup. |

WebAuthn and CORS origins must match how users open the UI (see `.env.example`).

## JPilot behavior

The orchestrator enforces:

1. **`search_netscaler_nextgen_api`** before Next-Gen API tools (returns blocked JSON if skipped).
2. **`search_netscaler_cli_reference`** before SSH/CLI write tools.
3. **Tool execution** for config changes — the model must call `netscaler_run_cli_command` or `netscaler_run_cli_commands`, not only list commands.
4. **Confirmation** for destructive CLI/API operations (`rm`, `DELETE`, `unbind`, etc.) via `confirmed=true` after user approval.
5. **Diagnostics run immediately** — no memory search required for ping, traceroute, TCP port checks, or nsconmsg.
6. **Guided LB forms** — for new classic LB vserver requests, JPilot may show an in-chat form; policy work (responder, rewrite, bind-to-existing vserver) does not use that form.

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

JPilot runs these via **`netscaler_run_cli_commands`** in one tool call after CLI reference lookup (often after the user submits a guided form).

### In-chat configuration forms

JPilot may reply with a short intro and a fenced `jpilot-form` JSON block. The UI renders fields (text, number, select, boolean, textarea). On submit, values are sent back as `Configuration inputs for: …` and the agent executes CLI with those values.

The backend also attaches a default classic LB form when the user clearly asks to **create** a load balancer / lb vserver and the model omitted the form — but **not** for responder, rewrite, transform, redirect, or bind/apply-to-existing-vserver requests.

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

### Diagnostics

| Tool | Description |
|------|-------------|
| `netscaler_run_diagnostic` | ICMP/path diagnostics: `ping`, `ping6`, `traceroute`, `traceroute6`, or **`tcp_port`** (with `port`) |
| `netscaler_telnet` | TCP port reachability from the appliance via telnet; returns verdict **`open`**, **`refused`**, or **`no_response`** |
| `netscaler_collect_nsconmsg` | Read-only performance/event collection via `/netscaler/nsconmsg` (`current`, `stats`, `event`, `memstats`, etc.) |

### SSL (v0.05)

| Tool / API | Description |
|------------|-------------|
| MCP `generate_ssl_csr` | Create key + CSR on appliance (OpenSSL via shell) |
| MCP `generate_ssl_self_signed` | Create key + self-signed certificate on appliance |
| `POST /ssl/generate-csr` | Backend proxy to MCP for the SSL Certificate Tools UI |

Enable or disable tools under **Settings → MCP Server**. **SSH fallback must be enabled** for diagnostic and SSL shell tools.

## Memory files

Official-syntax references mounted into the backend (edit at repo root):

- `netscaler_nextgen_api_memory.md` — Next-Gen API endpoints, payloads, behavioral rules
- `netscaler_adc_cli_memory.md` — ADC CLI namespaces, commands, behavioral rules

JPilot search tools read these before executing NetScaler write operations. Blocked tool responses include `requiredAction` telling the model to search first.

## API endpoints (backend)

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/health` | Health check |
| `POST` | `/auth/login` | Password login |
| `GET` | `/auth/me` | Current user |
| `POST` | `/auth/logout` | Logout |
| `POST` | `/auth/password-reset/confirm` | Complete password reset with emailed code |
| `POST` | `/auth/webauthn/status` | Passkey availability for username |
| `POST` | `/auth/webauthn/register/begin\|finish` | Register passkey (authenticated) |
| `POST` | `/auth/webauthn/login/begin\|finish` | Passkey sign-in |
| `GET/POST/PUT/DELETE` | `/users` | User management (admin) |
| `POST` | `/users/{user_id}/reset-password` | Admin send reset code to user's email |
| `DELETE` | `/users/{id}/passkeys/{passkeyId}` | Remove a user's passkey |
| `GET/POST` | `/appliances` | Appliance CRUD |
| `GET/POST` | `/ai-providers` | AI provider CRUD |
| `GET/PUT` | `/mcp/config` | MCP settings |
| `GET` | `/mcp/tools` | Enabled MCP tools |
| `GET` | `/mcp/status` | MCP server online status |
| `GET/PUT` | `/copilot/platform-settings` | Platform settings (Brave Search, web search toggle) |
| `POST` | `/copilot/platform-settings/test` | Test Brave Search API key |
| `POST` | `/copilot/chat` | JPilot chat with tool traces and optional `inputForm` |
| `GET` | `/copilot/status` | JPilot readiness (default provider) |
| `POST` | `/ssl/generate-csr` | Generate CSR or self-signed cert on appliance |

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
├── backend-api/tests/ # Backend unit tests (e.g. form heuristics)
├── docker-compose.yml
├── netscaler_nextgen_api_memory.md
├── netscaler_adc_cli_memory.md
└── .env.example
```

## Production notes

For production images, remove bind-mount volume lines for `frontend`, `backend-api`, and `mcp-server` in `docker-compose.yml` so containers use code baked into each Dockerfile. Use strong secrets, TLS in front of the UI/API, restrict MongoDB network access, configure SMTP for password reset, and set `WEBAUTHN_RP_ID`, `WEBAUTHN_ORIGIN`, and `CORS_ORIGINS` to your real hostname.

## License

[MIT](LICENSE) — see [LICENSE](LICENSE) for details.

Copyright (c) 2026 [juandiab](https://github.com/juandiab).
