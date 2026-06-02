# JPilot — Project Prompt

> **IMPORTANT: Read the entire prompt before generating any code.**

---

## PROJECT OBJECTIVE

Build a **JPilot** platform using:

- Python 3.12
- MongoDB
- Docker Compose
- MCP Server (Anthropic `mcp` Python SDK)
- Vue 3
- PrimeVue 4

**Milestone 1 scope — build only the following:**

1. Platform foundation
2. MCP Server (Anthropic `mcp` SDK, SSE transport)
3. MongoDB integration
4. Administration UI
5. NetScaler inventory management
6. AI Provider management
7. Foundation prepared for future NetScaler Next-Gen API integration

---

## ARCHITECTURE

The solution must contain **exactly four containers**:

| Container     | Technology        | Port  |
|---------------|-------------------|-------|
| `frontend`    | Vue 3 + Vite      | 5173  |
| `backend-api` | FastAPI + Uvicorn | 8000  |
| `mcp-server`  | MCP Python SDK    | 8001  |
| `mongodb`     | MongoDB latest    | 27017 |

**Do NOT add:**
- Mongo Express
- Redis
- PostgreSQL
- Vector Database
- RAG pipeline
- RabbitMQ

**Communication flow:**

```
Browser
  └─► Frontend (Vue 3) :5173
        └─► Backend API (FastAPI) :8000
              ├─► MongoDB :27017
              └─► MCP Server :8001

MCP Server (future connections):
  ├─► NetScaler Next-Gen API
  ├─► OpenAI
  ├─► Anthropic
  ├─► Gemini
  └─► LM Studio
```

The **Backend API does NOT communicate directly with NetScaler**.  
All NetScaler communication goes through the MCP Server.

---

## DEVELOPMENT MODEL

### Two-Mode Design (CRITICAL)

Every Dockerfile must support **both modes** without modification:

| Mode | How it works |
|------|-------------|
| **Development** | `docker-compose.yml` bind mounts overlay the container's `/app` directory with the host folder. Code changes on the host reflect immediately. Hot reload / auto-reload handles the rest. |
| **Production (future)** | Remove the bind mount volume lines from `docker-compose.yml`. The container runs from the code already baked in via `COPY . .` in the Dockerfile. No rebuild, no separate Dockerfile needed. |

### How this works

Each Dockerfile must:
1. `COPY . .` the source code into the image (bakes code in for production)
2. The `docker-compose.yml` bind mount overrides that COPY at runtime during development

```
Dockerfile:  COPY . /app          ← production code (always present in image)
Compose:     - ./backend-api:/app  ← dev override (takes precedence at runtime)
```

When the bind mount is active, Docker uses the host folder. When it is removed, Docker uses the COPY'd code. The same image serves both purposes.

### Development requirements

- Source code lives on the **host machine** in its respective folder.
- Changes made locally must reflect immediately in running containers.
- **Backend / MCP Server:** Uvicorn `--reload` flag — no container rebuild needed.
- **Frontend:** Vite HMR — no container rebuild needed.
- **Rebuilding containers must not be required** during development.

---

## DOCKER COMPOSE

**File:** `docker-compose.yml`

### Network

```
netscaler-copilot-network
```

### Volumes

```
mongodb_data   (persistent, for MongoDB data)
```

### Services

#### frontend

```yaml
build: ./frontend
ports: ["5173:5173"]
volumes:
  - ./frontend:/app
  - /app/node_modules        # anonymous volume — prevents host node_modules collision
environment:
  - VITE_API_BASE_URL=http://localhost:8000
networks: [netscaler-copilot-network]
depends_on: [backend-api]
```

#### backend-api

```yaml
build: ./backend-api
ports: ["8000:8000"]
volumes:
  - ./backend-api:/app
environment:
  - NSAGENT_ENCRYPTION_KEY=${NSAGENT_ENCRYPTION_KEY}
  - MONGO_URI=mongodb://mongodb:27017
  - MONGO_DB=netscaler_copilot
  - MCP_SERVER_URL=http://mcp-server:8001
networks: [netscaler-copilot-network]
depends_on: [mongodb, mcp-server]
```

#### mcp-server

```yaml
build: ./mcp-server
ports: ["8001:8001"]
volumes:
  - ./mcp-server:/app
environment:
  - MCP_HOST=0.0.0.0
  - MCP_PORT=8001
networks: [netscaler-copilot-network]
```

#### mongodb

```yaml
image: mongo:latest
ports: ["27017:27017"]
volumes:
  - mongodb_data:/data/db
networks: [netscaler-copilot-network]
```

> MongoDB runs **without authentication** in the development environment.

---

## BACKEND API

**Folder:** `/backend-api`

### Technology

- Python 3.12
- FastAPI
- Uvicorn with `--reload`
- Motor (async MongoDB driver)
- Pydantic v2
- Pydantic-Settings
- HTTPX
- Cryptography (Fernet)
- python-dotenv

### Folder Structure

```
backend-api/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── dependencies.py
│   ├── routers/
│   │   ├── health.py
│   │   ├── appliances.py
│   │   └── ai_providers.py
│   ├── models/
│   │   ├── appliance.py
│   │   └── ai_provider.py
│   ├── schemas/
│   │   ├── appliance.py
│   │   └── ai_provider.py
│   ├── services/
│   │   └── encryption_service.py
│   ├── utils/
│   └── middleware/
├── requirements.txt
├── Dockerfile
└── .env.example
```

### requirements.txt

```
fastapi>=0.115.0
uvicorn[standard]>=0.30.0
motor>=3.5.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
httpx>=0.27.0
cryptography>=42.0.0
python-dotenv>=1.0.0
```

### .env.example

```
NSAGENT_ENCRYPTION_KEY=replace_with_generated_fernet_key
MONGO_URI=mongodb://mongodb:27017
MONGO_DB=netscaler_copilot
MCP_SERVER_URL=http://mcp-server:8001
```

> **Generate a valid Fernet key with:**
> ```
> python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
> ```

### Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install dependencies first (layer cache optimization)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code into the image
# In development: docker-compose bind mount overrides this at runtime
# In production: remove the bind mount and this COPY'd code runs instead
COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

### config.py

Use `pydantic-settings` to load:

```python
class Settings(BaseSettings):
    nsagent_encryption_key: str
    mongo_uri: str = "mongodb://mongodb:27017"
    mongo_db: str = "netscaler_copilot"
    mcp_server_url: str = "http://mcp-server:8001"
```

### CORS

Configure `CORSMiddleware` in `main.py`:

```python
allow_origins=["http://localhost:5173"]
allow_credentials=True
allow_methods=["*"]
allow_headers=["*"]
```

### Health Endpoint

```
GET /health

Response:
{
  "status": "ok"
}
```

### API Routes (no versioning prefix)

```
GET     /health

GET     /appliances
GET     /appliances/{id}
POST    /appliances
PUT     /appliances/{id}
DELETE  /appliances/{id}
PATCH   /appliances/{id}/enable
PATCH   /appliances/{id}/disable

GET     /ai-providers
GET     /ai-providers/{id}
POST    /ai-providers
PUT     /ai-providers/{id}
DELETE  /ai-providers/{id}
PATCH   /ai-providers/{id}/set-default
```

---

## ENCRYPTION SERVICE

**File:** `backend-api/app/services/encryption_service.py`

Use `cryptography.fernet.Fernet`.

```python
def encrypt_value(plain_text: str) -> str:
    """Encrypt a string value using the Fernet key."""

def decrypt_value(cipher_text: str) -> str:
    """Decrypt a Fernet-encrypted string value."""
```

- Encryption key source: `NSAGENT_ENCRYPTION_KEY` from Settings.
- All sensitive fields must be encrypted before saving to MongoDB.
- Decrypted values must **never** be returned to the frontend.

---

## MCP SERVER

**Folder:** `/mcp-server`

### Technology

- Python 3.12
- `mcp` Python SDK (latest stable — Anthropic MCP SDK)
- Starlette (required by mcp SSE transport)
- Uvicorn
- HTTPX
- Pydantic v2
- python-dotenv

> **Transport: SSE (Server-Sent Events)**  
> The MCP server must use SSE transport so it is reachable over the Docker network.  
> Do NOT use stdio transport.

### Folder Structure

```
mcp-server/
├── app/
│   ├── server.py
│   ├── config.py
│   ├── services/
│   ├── providers/
│   ├── tools/
│   └── models/
├── requirements.txt
├── Dockerfile
└── .env.example
```

### requirements.txt

```
mcp[cli]
starlette
uvicorn[standard]
httpx>=0.27.0
pydantic>=2.0.0
python-dotenv>=1.0.0
```

### .env.example

```
MCP_HOST=0.0.0.0
MCP_PORT=8001
```

### server.py

Implement using the `mcp` SDK with SSE transport:

```python
from mcp.server import Server
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.routing import Mount, Route
from starlette.responses import JSONResponse
import uvicorn

# MCP server instance
mcp_app = Server("netscaler-copilot")

# SSE transport
sse = SseServerTransport("/messages")

# SSE connection handler
async def handle_sse(request):
    async with sse.connect_sse(
        request.scope, request.receive, request._send
    ) as streams:
        await mcp_app.run(
            streams[0], streams[1], mcp_app.create_initialization_options()
        )

# Health endpoint handler
async def health(request):
    return JSONResponse({"status": "ok"})

# Starlette app with routes
app = Starlette(
    routes=[
        Route("/health", endpoint=health),
        Route("/sse", endpoint=handle_sse),
        Mount("/messages", app=sse.handle_post_message),
    ]
)
```

### Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install dependencies first (layer cache optimization)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code into the image
# In development: docker-compose bind mount overrides this at runtime
# In production: remove the bind mount and this COPY'd code runs instead
COPY . .

EXPOSE 8001

CMD ["uvicorn", "app.server:app", "--host", "0.0.0.0", "--port", "8001", "--reload"]
```

### Health Endpoint

```
GET /health

Response:
{
  "status": "ok"
}
```

### Scope for Milestone 1

- Register zero tools (foundation only).
- No NetScaler API calls.
- No LLM calls.
- Folder structure and SSE transport must be in place for future tools.

---

## MONGODB

- Image: `mongo:latest`
- No authentication in development.
- Persistent volume: `mongodb_data` → `/data/db`
- Database name: `netscaler_copilot`
- Collections: `appliances`, `aiProviders`

**MongoDB is the single system of record.**  
Do NOT store inventory data in YAML, JSON, environment variables, or Python files.

---

## SECURITY

The **only** secret in `.env` files is:

```
NSAGENT_ENCRYPTION_KEY
```

**Never store in any `.env` file:**
- NetScaler hostnames
- NetScaler usernames
- NetScaler passwords
- OpenAI API keys
- Anthropic API keys
- Gemini API keys
- LM Studio endpoints

All operational data must be stored in MongoDB with sensitive fields encrypted.

---

## NETSCALER INVENTORY

### MongoDB Collection: `appliances`

```json
{
  "_id": "ObjectId",
  "name": "NS-PROD-01",
  "environment": "PROD",
  "encryptedHost": "<fernet encrypted>",
  "encryptedUsername": "<fernet encrypted>",
  "encryptedPassword": "<fernet encrypted>",
  "enabled": true,
  "notes": "",
  "createdAt": "ISO8601",
  "updatedAt": "ISO8601"
}
```

### Pydantic Schemas

**Create / Update request body:**

```python
class ApplianceCreate(BaseModel):
    name: str
    environment: Literal["LAB", "DEV", "TEST", "UAT", "PROD"]
    host: str
    username: str
    password: str
    notes: str = ""
    enabled: bool = True
```

**Response (never include decrypted credentials):**

```python
class ApplianceResponse(BaseModel):
    id: str
    name: str
    environment: str
    enabled: bool
    notes: str
    createdAt: datetime
    updatedAt: datetime
    # host, username, password are NEVER included in responses
```

### Credential Update Rule (CRITICAL)

On `PUT /appliances/{id}`:
- If `host` field is empty or absent → **do not update** `encryptedHost`
- If `username` field is empty or absent → **do not update** `encryptedUsername`
- If `password` field is empty or absent → **do not update** `encryptedPassword`
- Only update a credential field if the user provides a **non-empty new value**

### CRUD Operations

| Method | Route                            | Description                   |
|--------|----------------------------------|-------------------------------|
| GET    | `/appliances`                    | List all (no credentials)     |
| GET    | `/appliances/{id}`               | Get one (no credentials)      |
| POST   | `/appliances`                    | Create + encrypt credentials  |
| PUT    | `/appliances/{id}`               | Update (skip empty creds)     |
| DELETE | `/appliances/{id}`               | Delete                        |
| PATCH  | `/appliances/{id}/enable`        | Set enabled: true             |
| PATCH  | `/appliances/{id}/disable`       | Set enabled: false            |

---

## AI PROVIDERS

### MongoDB Collection: `aiProviders`

```json
{
  "_id": "ObjectId",
  "providerName": "OpenAI Production",
  "providerType": "OpenAI",
  "encryptedApiKey": "<fernet encrypted>",
  "endpoint": "",
  "model": "gpt-4o",
  "enabled": true,
  "isDefault": false,
  "createdAt": "ISO8601",
  "updatedAt": "ISO8601"
}
```

### Supported Provider Types

```python
Literal["OpenAI", "Anthropic", "Gemini", "LM Studio", "OpenAI-Compatible"]
```

### Pydantic Schemas

**Create / Update request body:**

```python
class AIProviderCreate(BaseModel):
    providerName: str
    providerType: Literal["OpenAI", "Anthropic", "Gemini", "LM Studio", "OpenAI-Compatible"]
    apiKey: str
    endpoint: str = ""
    model: str
    enabled: bool = True
    isDefault: bool = False
```

**Response (never include decrypted API key):**

```python
class AIProviderResponse(BaseModel):
    id: str
    providerName: str
    providerType: str
    endpoint: str
    model: str
    enabled: bool
    isDefault: bool
    createdAt: datetime
    updatedAt: datetime
    # apiKey is NEVER included in responses
```

### API Key Update Rule (CRITICAL)

On `PUT /ai-providers/{id}`:
- If `apiKey` field is empty or absent → **do not update** `encryptedApiKey`
- Only update if the user provides a **non-empty new value**

### Default Provider Rule (CRITICAL — backend enforced)

On `PATCH /ai-providers/{id}/set-default`:

The backend must execute **two sequential operations**:

1. Set `isDefault: false` on **all** providers
2. Set `isDefault: true` on the target provider

Only one provider may have `isDefault: true` at any time.  
This rule is enforced exclusively by the **backend**, not the frontend.

### CRUD Operations

| Method | Route                               | Description                          |
|--------|-------------------------------------|--------------------------------------|
| GET    | `/ai-providers`                     | List all (no API keys)               |
| GET    | `/ai-providers/{id}`                | Get one (no API key)                 |
| POST   | `/ai-providers`                     | Create + encrypt API key             |
| PUT    | `/ai-providers/{id}`                | Update (skip empty API key)          |
| DELETE | `/ai-providers/{id}`                | Delete                               |
| PATCH  | `/ai-providers/{id}/set-default`    | Set as default (unset all others)    |

---

## FRONTEND

**Folder:** `/frontend`

### Technology

- Vue 3 (Composition API **only** — no Options API)
- Vite 5
- PrimeVue **4** with **Aura** theme preset
- PrimeIcons 7
- PrimeFlex 3
- Vue Router 4
- Axios

### Folder Structure

```
frontend/
├── src/
│   ├── main.js
│   ├── App.vue
│   ├── views/
│   │   ├── DashboardView.vue
│   │   ├── NetScalersView.vue
│   │   ├── AIProvidersView.vue
│   │   └── SettingsView.vue
│   ├── components/
│   ├── services/
│   │   └── api.js
│   ├── router/
│   │   └── index.js
│   ├── layouts/
│   │   └── MainLayout.vue
│   └── stores/
├── public/
├── index.html
├── vite.config.js
├── package.json
└── Dockerfile
```

### package.json dependencies

```json
{
  "dependencies": {
    "vue": "^3.4.0",
    "vue-router": "^4.3.0",
    "primevue": "^4.0.0",
    "@primevue/themes": "^4.0.0",
    "primeicons": "^7.0.0",
    "primeflex": "^3.3.0",
    "axios": "^1.7.0"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^5.0.0",
    "vite": "^5.3.0"
  }
}
```

### PrimeVue 4 Setup in main.js

```javascript
import { createApp } from 'vue'
import PrimeVue from 'primevue/config'
import Aura from '@primevue/themes/aura'
import 'primeicons/primeicons.css'
import App from './App.vue'
import router from './router'

const app = createApp(App)
app.use(PrimeVue, {
  theme: {
    preset: Aura
  }
})
app.use(router)
app.mount('#app')
```

### vite.config.js (CRITICAL — required for Docker hot reload)

```javascript
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    watch: {
      usePolling: true   // required for file watching inside Docker on Linux/WSL2
    }
  }
})
```

### Dockerfile

```dockerfile
FROM node:20-alpine

WORKDIR /app

# Install dependencies first (layer cache optimization)
COPY package*.json ./
RUN npm install

# Copy source code into the image
# In development: docker-compose bind mount overrides this at runtime
# In production: remove the bind mount and this COPY'd code runs instead
COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev"]
```

### API Service (services/api.js)

```javascript
import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
})

export default api
```

### Vue Router Routes

```
/              → DashboardView
/netscalers    → NetScalersView
/ai-providers  → AIProvidersView
/settings      → SettingsView
```

### Navigation Menu

Use PrimeVue `Menubar` or sidebar layout.  
Menu items:

```
Dashboard      → /
NetScalers     → /netscalers
AI Providers   → /ai-providers
Settings       → /settings
```

---

## NETSCALERS PAGE (`/netscalers`)

Use PrimeVue `DataTable`.

### Columns

| Column      | Notes                                |
|-------------|--------------------------------------|
| Name        |                                      |
| Environment | Badge/Tag (LAB, DEV, TEST, UAT, PROD)|
| Status      | Enabled / Disabled indicator         |
| Notes       |                                      |
| Actions     | Edit, Delete, Enable/Disable toggle  |

### Add / Edit Dialog

Use PrimeVue `Dialog` component.

**Fields:**
- Name (text input)
- Environment (dropdown: LAB, DEV, TEST, UAT, PROD)
- Hostname (text input)
- Username (text input)
- Password (password input)
- Notes (textarea)
- Enabled (toggle)

**Edit mode credential rule:**
- Hostname, Username, and Password fields must render **empty** on edit.
- Display a hint message: *"Leave blank to keep existing value."*
- Only send the field to the backend if the user enters a new value.

### Delete Confirmation

Use PrimeVue `ConfirmDialog` or inline confirmation before deleting.

---

## AI PROVIDERS PAGE (`/ai-providers`)

Use PrimeVue `DataTable`.

### Columns

| Column        | Notes                                  |
|---------------|----------------------------------------|
| Provider Name |                                        |
| Type          | Badge (OpenAI, Anthropic, etc.)        |
| Model         |                                        |
| Status        | Enabled / Disabled indicator           |
| Default       | Star or badge if isDefault: true       |
| Actions       | Edit, Delete, Set Default              |

### Add / Edit Dialog

Use PrimeVue `Dialog` component.

**Fields:**
- Provider Name (text input)
- Provider Type (dropdown: OpenAI, Anthropic, Gemini, LM Studio, OpenAI-Compatible)
- API Key (password input)
- Endpoint (text input — required for LM Studio and OpenAI-Compatible)
- Model (text input)
- Enabled (toggle)

**Edit mode credential rule:**
- API Key field must render **empty** on edit.
- Display a hint message: *"Leave blank to keep existing value."*
- Only send the field to the backend if the user enters a new value.

**Set Default:**
- Action button in the DataTable row.
- Calls `PATCH /ai-providers/{id}/set-default`.
- Visually reflects the new default immediately on success.

---

## PLACEHOLDER PAGES

### Dashboard (`/`)

Render a simple welcome card:

```
Welcome to JPilot
Your intelligent NetScaler management platform.
```

No data fetching required. Placeholder only.

### Settings (`/settings`)

Render a simple placeholder card:

```
Settings
Coming soon.
```

---

## DELIVERABLES CHECKLIST

Generate all of the following. Every file must be executable with no modifications.

```
docker-compose.yml
.env.example                          (root level, contains NSAGENT_ENCRYPTION_KEY only)

backend-api/
  Dockerfile
  requirements.txt
  .env.example
  app/main.py
  app/config.py
  app/database.py
  app/dependencies.py
  app/routers/health.py
  app/routers/appliances.py
  app/routers/ai_providers.py
  app/models/appliance.py
  app/models/ai_provider.py
  app/schemas/appliance.py
  app/schemas/ai_provider.py
  app/services/encryption_service.py

mcp-server/
  Dockerfile
  requirements.txt
  .env.example
  app/server.py
  app/config.py

frontend/
  Dockerfile
  package.json
  vite.config.js
  index.html
  src/main.js
  src/App.vue
  src/router/index.js
  src/services/api.js
  src/layouts/MainLayout.vue
  src/views/DashboardView.vue
  src/views/NetScalersView.vue
  src/views/AIProvidersView.vue
  src/views/SettingsView.vue
```

---

## SUCCESS CRITERIA

The project must start successfully with:

```bash
docker compose up --build
```

After startup:
- `http://localhost:5173` → Vue frontend with navigation
- `http://localhost:8000/health` → `{"status": "ok"}`
- `http://localhost:8001/health` → `{"status": "ok"}`
- NetScalers CRUD fully functional
- AI Providers CRUD fully functional
- No credentials exposed in any API response
- Hot reload active on frontend code changes
- Auto-reload active on backend and MCP server code changes

### Switching to production mode (future)

To run the code fully inside containers, remove the three bind mount lines from `docker-compose.yml`:

```yaml
# Remove these lines per service when going to production:
# - ./frontend:/app
# - ./backend-api:/app
# - ./mcp-server:/app
```

Then run `docker compose up --build`. The containers will use the code baked in via `COPY . .` in each Dockerfile. No other changes required.
