from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status

from app.dependencies import get_current_user, get_db, require_admin
from app.schemas.jpilot_settings import JpilotSettingsResponse, JpilotSettingsUpdate, PortalConfigResponse
from app.schemas.license import LicenseCodeUpdate, LicenseResponse
from app.schemas.system import LicenseFingerprintResponse, UpdateCheckResponse, VersionResponse
from app.services.jpilot_settings_service import get_jpilot_settings, get_portal_config, update_jpilot_settings
from app.services.license_service import (
    get_installation_fingerprint,
    get_or_create_license,
    import_offline_license,
    remove_license,
    save_license_code,
)
from app.services.license_sync_service import LicenseSyncError
from app.services.update_service import check_for_updates, get_version_info

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/version", response_model=VersionResponse)
async def read_version() -> VersionResponse:
    return get_version_info()


@router.get("/portal-config", response_model=PortalConfigResponse)
async def read_portal_config(db=Depends(get_db)) -> PortalConfigResponse:
    return await get_portal_config(db)


@router.get("/jpilot-settings", response_model=JpilotSettingsResponse)
async def read_jpilot_settings(
    db=Depends(get_db),
    _admin: dict = Depends(require_admin),
) -> JpilotSettingsResponse:
    return await get_jpilot_settings(db)


@router.put("/jpilot-settings", response_model=JpilotSettingsResponse)
async def save_jpilot_settings(
    payload: JpilotSettingsUpdate,
    db=Depends(get_db),
    _admin: dict = Depends(require_admin),
) -> JpilotSettingsResponse:
    return await update_jpilot_settings(db, payload)


@router.get("/update-check", response_model=UpdateCheckResponse)
async def read_update_check(
    force: bool = Query(default=False, description="Bypass the cached GitHub response"),
    _user=Depends(get_current_user),
) -> UpdateCheckResponse:
    return await check_for_updates(force=force)


@router.get("/license-fingerprint", response_model=LicenseFingerprintResponse)
async def read_license_fingerprint(
    db=Depends(get_db),
    _user=Depends(get_current_user),
) -> LicenseFingerprintResponse:
    return LicenseFingerprintResponse(**await get_installation_fingerprint(db))


@router.get("/license", response_model=LicenseResponse)
async def read_license(db=Depends(get_db), _user=Depends(get_current_user)) -> LicenseResponse:
    return await get_or_create_license(db)


@router.put("/license", response_model=LicenseResponse)
async def put_license(
    payload: LicenseCodeUpdate,
    db=Depends(get_db),
    _user=Depends(get_current_user),
) -> LicenseResponse:
    try:
        return await save_license_code(db, payload)
    except LicenseSyncError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.delete("/license", response_model=LicenseResponse)
async def delete_license(db=Depends(get_db), _user=Depends(get_current_user)) -> LicenseResponse:
    return await remove_license(db)


@router.post("/license/import-offline", response_model=LicenseResponse)
async def post_license_import_offline(
    file: UploadFile = File(..., description="Nexxus offline license file (.lic)"),
    db=Depends(get_db),
    _user=Depends(get_current_user),
) -> LicenseResponse:
    try:
        content = await file.read()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not read license file.",
        ) from exc
    try:
        return await import_offline_license(db, content=content)
    except LicenseSyncError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
