from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.dependencies import get_db, require_admin
from app.schemas.security_settings import SecuritySettingsResponse, SecuritySettingsUpdate
from app.services.security_settings_service import get_security_settings, update_security_settings

router = APIRouter(prefix="/security", tags=["security"])


@router.get("/settings", response_model=SecuritySettingsResponse)
async def read_security_settings(
    db: AsyncIOMotorDatabase = Depends(get_db),
    _admin: dict = Depends(require_admin),
) -> SecuritySettingsResponse:
    return await get_security_settings(db)


@router.put("/settings", response_model=SecuritySettingsResponse)
async def save_security_settings(
    payload: SecuritySettingsUpdate,
    db: AsyncIOMotorDatabase = Depends(get_db),
    _admin: dict = Depends(require_admin),
) -> SecuritySettingsResponse:
    return await update_security_settings(db, payload)
