from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.dependencies import get_db, require_admin
from app.schemas.security_settings import SecuritySettingsResponse, SecuritySettingsUpdate
from app.schemas.tls_certificate import (
    TlsCertificateApplyResult,
    TlsCertificateInspection,
    TlsCertificatePayload,
    TlsCertificateStatus,
)
from app.services.security_settings_service import get_security_settings, update_security_settings
from app.services.tls_certificate_service import apply_tls_certificate, get_tls_status, validate_tls_certificate

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


@router.get("/tls/status", response_model=TlsCertificateStatus)
async def read_tls_certificate_status(
    _admin: dict = Depends(require_admin),
) -> TlsCertificateStatus:
    return TlsCertificateStatus(**get_tls_status())


@router.post("/tls/validate", response_model=TlsCertificateInspection)
async def validate_tls_certificate_endpoint(
    payload: TlsCertificatePayload,
    _admin: dict = Depends(require_admin),
) -> TlsCertificateInspection:
    return TlsCertificateInspection(**validate_tls_certificate(
        payload.certificate,
        payload.private_key,
        payload.chain,
    ))


@router.post("/tls/apply", response_model=TlsCertificateApplyResult)
async def apply_tls_certificate_endpoint(
    payload: TlsCertificatePayload,
    _admin: dict = Depends(require_admin),
) -> TlsCertificateApplyResult:
    return TlsCertificateApplyResult(**apply_tls_certificate(
        payload.certificate,
        payload.private_key,
        payload.chain,
    ))
