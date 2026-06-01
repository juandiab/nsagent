from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import close_mongo_connection, connect_to_mongo, get_database
from app.dependencies import get_current_user
from app.routers import ai_providers, appliance_ops, appliances, auth, copilot, health, mcp
from app.services.mcp_client import push_config_to_mcp_server
from app.services.mcp_config_service import ensure_default_settings, get_mcp_settings
from app.services.ai_provider_service import migrate_lm_studio_endpoints
from app.services.user_service import ensure_default_admin


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongo()
    db = get_database()
    await ensure_default_admin(db)
    await ensure_default_settings(db)
    await migrate_lm_studio_endpoints(db)
    try:
        settings = await get_mcp_settings(db)
        await push_config_to_mcp_server(settings)
    except Exception:
        pass
    yield
    await close_mongo_connection()


app = FastAPI(title="NetScaler Copilot API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(auth.router)

protected = [Depends(get_current_user)]

app.include_router(mcp.router, dependencies=protected)
app.include_router(copilot.router, dependencies=protected)
app.include_router(appliance_ops.router, dependencies=protected)
app.include_router(appliances.router, dependencies=protected)
app.include_router(ai_providers.router, dependencies=protected)
