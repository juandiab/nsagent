# NSAgent

**NetScaler Copilot** — an AI-assisted management platform for Citrix NetScaler ADC appliances. Register appliances, configure AI providers, and use a Copilot chat that reads and writes configuration through the **NetScaler Next-Gen API**, **read-only NITRO**, and **SSH CLI** — with official documentation baked into memory files so the assistant does not invent syntax.

Repository: [github.com/juandiab/nsagent](https://github.com/juandiab/nsagent)

## Features

- **Appliance inventory** — store NetScaler hosts and encrypted credentials (Fernet).
- **AI provider management** — OpenAI, Anthropic, Gemini, Grok, LM Studio, and OpenAI-compatible endpoints.
- **Copilot chat** — tool-calling agent bound to the selected appliance; credentials never sent to the LLM.
- **MCP server** — Model Context Protocol tools for Next-Gen API, classic CLI over SSH, and NITRO helpers.
- **Memory-guided RAG** — `netscaler_nextgen_api_memory.md` and `netscaler_adc_cli_memory.md` gate API/CLI usage before execution.
- **Classic + Next-Gen** — list virtual servers from Next-Gen applications and classic `lbvserver`; create apps via Next-Gen or multi-step LB setup via CLI.

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
| Frontend     | 5173  | Vue 3 + PrimeVue admin UI and Copilot     |
| Backend API  | 8000  | Auth, CRUD, Copilot orchestration, MCP proxy |
| MCP Server   | 8001  | NetScaler tool execution (SSE-capable)    |
| MongoDB      | 27017 | Settings, appliances, AI providers          |

## Prerequisites

- Docker and Docker Compose
- NetScaler ADC with **Next-Gen API** enabled (`enable ns nextgenapi`) for API tools
- SSH access to the appliance for classic CLI read/write tools (port 22)
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

3. **Start the stack**

   ```bash
   docker compose up --build
   ```

4. **Open the UI**

   - App: [http://localhost:5173](http://localhost:5173)
   - Default login: `admin` / `admin` (change via `.env` before first run)

5. **Configure**

   - **NetScalers** — add your appliance (name, host, API/SSH user and password).
   - **AI Providers** — add an LLM provider and set it as default.
   - **Settings → MCP** — tool toggles, SSH fallback, timeouts.
   - **Copilot** — select an appliance and ask questions or request changes.

## Copilot behavior

The orchestrator enforces:

1. **`search_netscaler_nextgen_api`** before Next-Gen API tools.
2. **`search_netscaler_cli_reference`** before SSH/CLI write tools.
3. **Tool execution** for config changes — the model cannot only list CLI commands; it must call `netscaler_run_cli_command` or `netscaler_run_cli_commands`.
4. **Confirmation** for destructive CLI/API operations (`rm`, `DELETE`, `unbind`, etc.) via `confirmed=true` after user approval.

Example — classic LB virtual server with service group:

```text
add lb vserver webserver_02 HTTP 192.168.20.227 80
add serviceGroup webserver_02_sg HTTP
bind serviceGroup webserver_02_sg 192.168.20.36 5173
bind lb vserver webserver_02 -serviceGroupName webserver_02_sg
save ns config
```

Copilot runs these via **`netscaler_run_cli_commands`** in one tool call after CLI reference lookup.

## MCP tools

| Tool | Description |
|------|-------------|
| `netscaler_test_connection` | Next-Gen API login test |
| `netscaler_get_system_info` | Management IP, version, hostname, serial |
| `netscaler_list_applications` | Next-Gen applications only |
| `netscaler_list_virtual_servers` | Next-Gen apps + classic NITRO `lbvserver` |
| `netscaler_list_virtual_ips` | VIPs from Next-Gen applications |
| `netscaler_list_ip_addresses` | NSIP, SNIP, VIP, servers (Next-Gen + NITRO) |
| `netscaler_nextgen_get` | Read-only GET on any Next-Gen path |
| `netscaler_nextgen_request` | GET/POST/PUT/DELETE on Next-Gen paths |
| `netscaler_create_application` | POST `/applications` (VIP + backends) |
| `netscaler_add_ip_address` | Classic VIP/SNIP/NSIP via NITRO |
| `netscaler_ssh_run_command` | Read-only CLI (`show` / `stat` / `get`) |
| `netscaler_run_cli_command` | Single classic CLI command (read or write) |
| `netscaler_run_cli_commands` | Ordered sequence of CLI commands (multi-step setup) |

Enable or disable tools under **Settings → MCP Server**.

## Memory files

Official-syntax references mounted into the backend (edit at repo root):

- `netscaler_nextgen_api_memory.md` — Next-Gen API endpoints, payloads, behavioral rules
- `netscaler_adc_cli_memory.md` — ADC CLI namespaces, commands, behavioral rules

Copilot search tools read these before executing NetScaler operations.

## API endpoints (backend)

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/health` | Health check |
| `POST` | `/auth/login` | Admin login |
| `GET/POST` | `/appliances` | Appliance CRUD |
| `GET/POST` | `/ai-providers` | AI provider CRUD |
| `GET/PUT` | `/mcp/config` | MCP settings |
| `GET` | `/mcp/tools` | Enabled MCP tools |
| `POST` | `/copilot/chat` | Copilot chat with tool traces |

## Development

Source is bind-mounted into containers; **Uvicorn `--reload`** and **Vite HMR** pick up changes without rebuild.

```bash
docker compose up
```

Health checks:

- Backend: [http://localhost:8000/health](http://localhost:8000/health)
- MCP: [http://localhost:8001/health](http://localhost:8001/health)
- MCP tools: [http://localhost:8001/tools](http://localhost:8001/tools)

### Project layout

```
├── frontend/          # Vue 3 + PrimeVue UI
├── backend-api/       # FastAPI backend, Copilot orchestrator
├── mcp-server/        # MCP NetScaler tool server
├── docker-compose.yml
├── netscaler_nextgen_api_memory.md
├── netscaler_adc_cli_memory.md
└── .env.example
```

## Production notes

For production images, remove bind-mount volume lines for `frontend`, `backend-api`, and `mcp-server` in `docker-compose.yml` so containers use code baked into each Dockerfile. Use strong secrets, TLS in front of the UI/API, and restrict MongoDB network access.

## License

No license file is included yet. Add one if you plan to open-source the project.
