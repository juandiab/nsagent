import asyncio
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import close_mongo_connection, connect_to_mongo, get_database
from app.dependencies import get_current_user
from app.routers import ai_providers, appliance_ops, appliances, auth, copilot, health, mcp, ssl_csr, system, users, webauthn
from app.services.mcp_client import push_config_to_mcp_server
from app.services.mcp_config_service import ensure_default_settings, get_mcp_settings
from app.services.ai_provider_service import migrate_lm_studio_endpoints
from app.services.password_reset_service import ensure_password_reset_indexes
from app.services.license_scheduler import periodic_license_sync, run_startup_license_sync
from app.services.license_service import ensure_license_collection
from app.services.user_service import ensure_default_admin
from app.services.webauthn_service import ensure_webauthn_indexes


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongo()
    db = get_database()
    await ensure_default_admin(db)
    await ensure_license_collection(db)
    await ensure_webauthn_indexes(db)
    await ensure_password_reset_indexes(db)
    await ensure_default_settings(db)
    await migrate_lm_studio_endpoints(db)
    try:
        mcp_settings = await get_mcp_settings(db)
        await push_config_to_mcp_server(mcp_settings)
    except Exception:
        pass
    await run_startup_license_sync()
    license_sync_stop = asyncio.Event()
    license_sync_task = asyncio.create_task(periodic_license_sync(license_sync_stop))
    yield
    license_sync_stop.set()
    await license_sync_task
    await close_mongo_connection()


app = FastAPI(title="JPilot API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1|\[::1\])(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(webauthn.router)

protected = [Depends(get_current_user)]

app.include_router(users.router, dependencies=protected)

app.include_router(mcp.router, dependencies=protected)
app.include_router(copilot.router, dependencies=protected)
app.include_router(appliance_ops.router, dependencies=protected)
app.include_router(appliances.router, dependencies=protected)
app.include_router(ssl_csr.router, dependencies=protected)
app.include_router(ai_providers.router, dependencies=protected)
app.include_router(system.router, dependencies=protected)
