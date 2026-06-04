from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status

from app.dependencies import get_db
from app.schemas.license import LicenseCodeUpdate, LicenseResponse
from app.schemas.system import LicenseFingerprintResponse, UpdateCheckResponse, VersionResponse
from app.services.license_service import (
    get_or_create_license,
    import_offline_license,
    licensefingerprint,
    remove_license,
    save_license_code,
)
from app.services.license_sync_service import LicenseSyncError
from app.services.update_service import check_for_updates, get_version_info

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/version", response_model=VersionResponse)
async def read_version() -> VersionResponse:
    return get_version_info()


@router.get("/update-check", response_model=UpdateCheckResponse)
async def read_update_check(
    force: bool = Query(default=False, description="Bypass the cached GitHub response"),
) -> UpdateCheckResponse:
    return await check_for_updates(force=force)


@router.get("/license-fingerprint", response_model=LicenseFingerprintResponse)
async def read_license_fingerprint() -> LicenseFingerprintResponse:
    return LicenseFingerprintResponse(**licensefingerprint())


@router.get("/license", response_model=LicenseResponse)
async def read_license(db=Depends(get_db)) -> LicenseResponse:
    return await get_or_create_license(db)


@router.put("/license", response_model=LicenseResponse)
async def put_license(
    payload: LicenseCodeUpdate,
    db=Depends(get_db),
) -> LicenseResponse:
    try:
        return await save_license_code(db, payload)
    except LicenseSyncError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.delete("/license", response_model=LicenseResponse)
async def delete_license(db=Depends(get_db)) -> LicenseResponse:
    return await remove_license(db)


@router.post("/license/import-offline", response_model=LicenseResponse)
async def post_license_import_offline(
    file: UploadFile = File(..., description="Nexxus offline license file (.lic)"),
    db=Depends(get_db),
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
