from fastapi import APIRouter, Query

from app.schemas.system import UpdateCheckResponse, VersionResponse
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
