# JPilot

**JPilot** — an AI-assisted management platform for Citrix NetScaler ADC appliances. Register appliances, configure AI providers, and use the JPilot chat that reads and writes configuration through the **NetScaler Next-Gen API**, **read-only NITRO**, and **SSH CLI** — with official documentation baked into memory files so the assistant does not invent syntax.

Repository: [github.com/juandiab/nsagent](https://github.com/juandiab/nsagent)

> **Disclaimer:** JPilot is an independent project and is not affiliated with, endorsed by, or sponsored by Citrix Systems, Inc. NetScaler is a trademark of Citrix Systems, Inc.

**Current release:** `v0.14` — viewport-fit layout for Dashboard, Plans, and JPilot on 1080p and iPad Pro landscape.

Bump the root [`VERSION`](VERSION) file when tagging a release so in-app update checks match GitHub.

## Features

- **Appliance inventory** — store NetScaler hosts and encrypted credentials (Fernet).
- **AI provider management** — OpenAI, Anthropic, Gemini, Grok, DeepSeek, LM Studio, and OpenAI-compatible endpoints.
- **JPilot chat** — tool-calling agent bound to the selected appliance; credentials never sent to the LLM.
- **JPilot roles** — **Architect** (plan without a connected appliance), **Operator** (configure the ADC), **Investigator** (read-first troubleshooting); dual-pane defaults to Architect + Operator.
- **MCP server** — Model Context Protocol tools for Next-Gen API, classic CLI over SSH, NITRO helpers, diagnostics, and SSL key/CSR generation.
- **Memory-guided RAG** — `netscaler_nextgen_api_memory.md` and `netscaler_adc_cli_memory.md` gate API/CLI usage before execution.
- **Classic + Next-Gen** — list virtual servers from Next-Gen applications and classic `lbvserver`; create apps via Next-Gen or multi-step LB setup via CLI.
- **Guided load balancer forms** — JPilot can embed interactive `jpilot-form` blocks in chat (VIP, service type, backends, monitors); submissions drive CLI execution after reference lookup.
- **Smart form routing** — responder, rewrite, transform, and other policy-on-vserver requests do not trigger the LB creation form.
- **Authentication** — password login until a passkey is registered; then passkey-only sign-in (password login blocked server-side).
- **Account recovery** — email OTP via SMTP; self-service at `/account-recovery` or admin-initiated from Users; revokes passkeys and resets password and/or registers a new passkey.
- **User management** — admin CRUD for users (roles `admin` / `user`), email for resets, initial password on create, passkey count and removal.
- **SSL certificate tools** — generate CSRs or self-signed certificates on the appliance (UI + API + MCP).
- **NetScaler diagnostics** — ICMP ping/traceroute, TCP port reachability via telnet from the appliance shell, and read-only `nsconmsg` performance/event collection.
- **Optional Brave Search** — domain-restricted web augmentation when local memory/docs are weak (Settings → AI Providers).
- **Dashboard shortcuts** — recommended JPilot prompts and links (health summary, list IPs/vservers, diagnostics, guided LB).
- **Model usage dashboard** — Settings → AI Providers shows monthly LLM token/request usage and Brave Search query usage with progress bars (tracked locally per calendar month).

## What's new in v0.14

| Area | Highlights |
|------|------------|
| **JPilot layout** | Copilot page height accounts for shell padding and main-content bottom spacing (`calc(100vh - 5rem)`); `overflow: hidden` prevents page scroll. |
| **Dashboard & Plans** | `@media (max-height: 900px)` compacts welcome/hero spacing, grids, marketing blog cards, and plan cards so Dashboard and Plans fit 1080p and iPad Pro 13″ landscape without scrolling past the footer. |

## What's new in v0.13

| Area | Highlights |
|------|------------|
| **Production compose** | `docker-compose.prod.yml` is now an **overlay** on `docker-compose.yml` (use both `-f` flags or `./compose.sh`). Clears dev bind mounts, drops the dev frontend via profile, and fixes nginx `depends_on` merging. |
| **Startup order** | MCP and backend healthchecks; API waits for healthy MongoDB **and** MCP before starting; nginx waits for a healthy backend. |
| **MCP URL migration** | Stored MCP settings that point at `localhost` are rewritten to `http://mcp-server:8001` on startup (fixes MCP calls from inside Docker). |
| **MongoDB connect** | Backend verifies MongoDB with an admin `ping` and a 5s server-selection timeout during startup. |

## What's new in v0.12

| Area | Highlights |
|------|------------|
| **JPilot roles** | **Architect** (plan without a connected appliance), **Operator** (configure the ADC), **Investigator** (read-first troubleshooting). Icon `SelectButton` per chat pane; dual-pane layout defaults to Architect + Operator. `GET /api/copilot/roles`. |
| **Architect fixes** | No false “no changes applied” banner or auto LB creation form when planning changes on an existing vserver (e.g. secure headers on `lb_01`). |
| **Settings** | Fixed `KeepAlive` template structure so Settings tabs cache correctly without a Vue compile error. |
| **MongoDB (prod)** | Pin `mongo:8.2`, `restart: unless-stopped`, healthcheck; `backend-api` / `mcp-server` wait for healthy MongoDB. |
| **nginx** | Separate **login** zone (`10r/m`) for `POST /api/auth/login`; **contact** zone (`5r/m`) for recovery and other `/api/auth` paths. |

## What's new in v0.11

| Area | Highlights |
|------|------------|
| **Auth** | nginx `/api/auth` rate limit raised from 5 to **15 requests/minute** (burst 15) for login, passkey, and recovery flows. |

## What's new in v0.10

| Area | Highlights |
|------|------------|
| **Fix** | Settings sections cached with `KeepAlive` so switching tabs no longer remounts panels and refetches `/api/ai-providers`, platform settings, and usage dashboard on every visit. |
| **Fix** | Production nginx API rate limit aligned with dev (`30r/s`, burst 60) — fixes 503 errors when jumping between Settings tabs (was `20r/m` in prod templates). |
| **UI** | Login page visual refresh (animated background, scroll-in animations). |
| **UI** | Global page fade transitions on route changes. |

## What's new in v0.09

| Area | Highlights |
|------|------------|
| **Settings UX** | Tabs grouped as Platform, People, Personal, and App; setup-first order (AI Providers → JPilot → MCP → Next-Gen → Users → Security → About → Legal). |
| **Naming** | Settings tab renamed from Chat to JPilot. |

## What's new in v0.08

| Area | Highlights |
|------|------------|
| **Fix** | Dev stack mounts `VERSION` at `/usr/share/jpilot/VERSION` so it no longer conflicts with the `./backend-api:/app` bind mount. |

## What's new in v0.07

| Area | Highlights |
|------|------------|
| **Updates** | Settings → About checks GitHub for new versions; banner when an update is available; copy-paste rebuild instructions for macOS/Linux and Windows. |
| **Versioning** | Root `VERSION` file baked into the backend; compares against GitHub tags (falls back when no GitHub Release is published). |
| **Deploy modes** | Installer lets you pick production (compiled) or development (hot reload); `compose.sh` / `compose.ps1` pick the right stack from `.env`. |
| **Production stack** | `docker-compose.yml` + `docker-compose.prod.yml` overlay — compiled frontend in nginx, no dev bind mounts on API services. |

## What's new in v0.06

| Area | Highlights |
|------|------------|
| **Settings hub** | Single Settings page with tabs: MCP Server, Chat, AI Providers, Next-Gen API, Security, Legal. |
| **AI Providers** | LLM provider CRUD and Brave Search (visually separate from LLMs) moved from the main menu; usage dashboard lives in the same tab. |
| **Next-Gen API** | Connection and reference panel moved to Settings → Next-Gen API (`/next-gen-api` redirects). |
| **NetScalers** | SSL Certificate Tools moved to NetScalers → SSL Certificates tab (`/ssl-csr` redirects). |
| **Navigation** | Slimmer sidebar: Dashboard, JPilot, NetScalers, Settings (+ Users for admins). |
| **MCP catalog** | Settings tool list synced with server — Next-Gen request, diagnostics, telnet, nsconmsg, CSR generation. |
| **Performance** | nginx API rate limit raised (`30r/s`, burst 60) to prevent 503s when Settings loads multiple endpoints. |
| **Fixes** | Settings lazy-loads section data on tab switch; route redirects for moved pages. |

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

The only prerequisite is **Docker**. The installer downloads the project, generates the
secrets and TLS certificate, writes `.env`, launches the stack, and opens JPilot in your
browser. Pick your platform:

### Windows

Install [Docker Desktop](https://docs.docker.com/desktop/install/windows-install/) (and
[Git for Windows](https://git-scm.com/download/win)). Then, in **PowerShell**:

```powershell
irm https://raw.githubusercontent.com/juandiab/nsagent/main/get.ps1 | iex
```

### macOS

Install [Docker Desktop](https://docs.docker.com/desktop/install/mac-install/) (or let the
installer set it up via Homebrew). Then, in **Terminal**:

```bash
curl -fsSL https://raw.githubusercontent.com/juandiab/nsagent/main/get.sh | bash
```

### Ubuntu / Linux

Docker Engine is required — if it's missing, the installer offers to install it for you.
Then run:

```bash
curl -fsSL https://raw.githubusercontent.com/juandiab/nsagent/main/get.sh | bash
```

---

The script checks for Docker (offering to install it if absent), downloads JPilot, and
starts the setup wizard. Then:

1. Open **https://localhost:9443** (the installer uses a self-signed certificate, so
   accept the one-time browser warning).
2. Complete the wizard: admin account, domain, **deploy mode** (production or development),
   and TLS (self-signed or your own cert).
3. On the **Review** step, **save the generated `NSAGENT_ENCRYPTION_KEY`** — it is
   required to restore or migrate the install and cannot be recovered.
4. Click **Install JPilot**. The wizard writes `.env` and `nginx/ssl/`, and your
   terminal automatically launches the full stack and opens it in your browser.
5. Sign in at **https://&lt;your-domain&gt;** with the admin account you created.

> Already cloned the repo? Skip the one-liner and just run `./install.sh` (macOS/Linux) or
> `.\install.ps1` (Windows) from the project root.

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

   - **NetScalers** — add your appliance (name, host, API/SSH user and password); **SSL Certificates** tab for CSR/self-signed generation.
   - **Settings → AI Providers** — add an LLM provider, set default, configure optional Brave Search, and view usage.
   - **Settings → MCP Server** — tool toggles, **SSH fallback** (required for diagnostics and SSL shell), SMTP, timeouts.
   - **Settings → Next-Gen API** — test Next-Gen connection and browse API reference.
   - **Settings → Security** — register an optional passkey after password login.
   - **Users** (admin) — create users with email (for password reset) and initial passwords.
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
   | `NSAGENT_DEPLOY_MODE`    | `prod` (compiled, default) or `dev` (hot reload) |
   | `NGINX_HOSTNAME`         | Public hostname for nginx TLS        |
   | `WEBAUTHN_RP_ID`         | WebAuthn RP ID (usually your hostname or `localhost`) |
   | `WEBAUTHN_ORIGIN`        | Exact UI origin (e.g. `https://your-domain`) |
   | `CORS_ORIGINS`           | Comma-separated allowed browser origins |
   | `SMTP_*`                 | Optional — required for email password reset |
   | `PASSWORD_RESET_LOG_CODES` | Dev only: log reset codes to backend logs |

3. **Provide TLS certificates** — place `cert.crt` and `cert.key` in `nginx/ssl/`
   (see [nginx/ssl/README.md](nginx/ssl/README.md)). nginx will not start without them.

4. **Start the stack** — `./compose.sh up --build` (reads `NSAGENT_DEPLOY_MODE` from `.env`), then open `https://<NGINX_HOSTNAME>`.

## Authentication

| Flow | Description |
|------|-------------|
| **Password login** | `POST /auth/login` — allowed only while the user has **no** registered passkeys. |
| **Passkey login** | Required once a passkey exists; `POST /auth/webauthn/login/begin\|finish`. |
| **Passkey registration** | Authenticated users register in **Settings → Security** (email required on the account). |
| **Account recovery** | `POST /auth/account-recovery/request` (self-service) or admin from **Users**; user completes at `/account-recovery` via `POST /auth/password-reset/confirm` (removes passkeys; optional new password; optional short-lived token to register a new passkey). |
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
| `POST` | `/auth/login` | Password login (blocked if user has passkeys) |
| `GET` | `/auth/me` | Current user |
| `POST` | `/auth/logout` | Logout |
| `POST` | `/auth/account-recovery/request` | Self-service recovery code (generic response) |
| `POST` | `/auth/password-reset/confirm` | Complete account recovery with emailed code |
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
| `GET` | `/copilot/usage-dashboard` | LLM and Brave Search usage vs monthly limits |
| `PUT` | `/copilot/usage-limits` | Update monthly usage caps (optional) |
| `GET` | `/copilot/status` | JPilot readiness (default provider) |
| `POST` | `/ssl/generate-csr` | Generate CSR or self-signed cert on appliance |

## Development

Set `NSAGENT_DEPLOY_MODE=dev` in `.env` (or pick **Development** in the installer). Source is
bind-mounted into containers; **Uvicorn `--reload`** and **Vite HMR** pick up changes without rebuild.

```bash
./compose.sh up
# or explicitly: docker compose --profile dev up --build
```

Health checks (dev stack exposes service ports via containers):

- Backend: [http://localhost:8000/health](http://localhost:8000/health)
- MCP: [http://localhost:8001/health](http://localhost:8001/health)
- MCP tools: [http://localhost:8001/tools](http://localhost:8001/tools)

After changing Python dependencies in `requirements.txt`, rebuild the affected image:

```bash
./compose.sh build backend-api mcp-server && ./compose.sh up -d backend-api mcp-server
```

## Production

Set `NSAGENT_DEPLOY_MODE=prod` in `.env` (the installer default). Production merges the base
stack with `docker-compose.prod.yml`: the frontend is compiled into the nginx image, and API
services run without reload or source bind mounts.

```bash
./compose.sh up -d --build
# or explicitly:
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

Do **not** use `docker-compose.prod.yml` alone — it only contains production overrides. The base
`docker-compose.yml` defines MongoDB, networks, volumes, and shared service settings.

After changing the domain or `VITE_API_BASE_URL`, rebuild nginx so the UI picks up the new API URL:

```bash
./compose.sh up -d --build nginx
```

Use strong secrets, TLS in front of the UI/API, restrict MongoDB network access, configure SMTP
for password reset, and set `WEBAUTHN_RP_ID`, `WEBAUTHN_ORIGIN`, and `CORS_ORIGINS` to your
real hostname.

### MongoDB crashes (production)

The stack pins **`mongo:8.2`** (not `latest`), uses **`restart: unless-stopped`** on all
services, and a **healthcheck** so `backend-api` and `mcp-server` start only after MongoDB
responds to `ping`.

**Why 8.2 and not 7.0?** Recent installs used `mongo:latest` (MongoDB **8.2.x**). Existing
data has feature compatibility version **8.2** — `mongo:7.0` or `mongo:8.0` exit with code
**62**. Pin **`mongo:8.2`** on existing servers; use **`mongo:7.0`** only for a **new** volume.

Before recreating, confirm the running image:

```bash
docker inspect nsagent-mongodb-1 --format '{{index .Config.Labels "org.opencontainers.image.version"}} {{.Config.Image}}'
```

**Check logs for corruption / abrupt shutdown:**

```bash
docker logs nsagent-mongodb-1 2>&1 | grep -i "fatal\|assert\|crash\|signal\|segfault\|abrupt\|unclean"
```

**Redeploy after pulling compose changes** (recreate Mongo so the pinned image applies):

```bash
./compose.sh up -d --force-recreate mongodb
./compose.sh up -d backend-api mcp-server nginx
```

**If MongoDB keeps exiting with code 139**, stop the stack and repair the data volume (volume
name is usually `<project>_nsagent_mongodb_data`, e.g. `nsagent_nsagent_mongodb_data`):

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml stop mongodb
docker run --rm -v nsagent_nsagent_mongodb_data:/data/db mongo:8.2 mongod --repair
./compose.sh up -d mongodb
./compose.sh up -d backend-api mcp-server nginx
```

### Project layout

```
├── frontend/          # Vue 3 + PrimeVue UI
├── backend-api/       # FastAPI backend, JPilot orchestrator
├── mcp-server/        # MCP NetScaler tool server
├── backend-api/tests/ # Backend unit tests (e.g. form heuristics)
├── docker-compose.yml
├── docker-compose.prod.yml
├── compose.sh              # picks dev/prod compose from .env
├── netscaler_nextgen_api_memory.md
├── netscaler_adc_cli_memory.md
└── .env.example
```

## License

**JPilot** distributed via Docker or installer is **proprietary software** licensed under the [EULA](frontend/src/legal/eula.md) (Nexxus-Tech SAS). Open-source **third-party** components are listed in [THIRD_PARTY_NOTICES.txt](THIRD_PARTY_NOTICES.txt) (regenerate with `./scripts/generate-third-party-notices.sh`).

The repository `LICENSE` file applies only where expressly stated for specific open-source artifacts; it does not grant rights to the commercial product.
