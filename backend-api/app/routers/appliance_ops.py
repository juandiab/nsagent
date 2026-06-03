from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.dependencies import get_db
from app.models.appliance import is_netscaler_appliance, parse_object_id
from app.schemas.test import ApplianceTestPreview, TestConnectionResponse
from app.services.encryption_service import decrypt_value
from app.services.mcp_client import (
    get_system_info_via_mcp,
    list_lb_vservers_via_mcp,
    test_appliance_via_mcp,
)

router = APIRouter(prefix="/appliances", tags=["appliances"])


async def _credentials_from_appliance(db: AsyncIOMotorDatabase, appliance_id: str) -> tuple[str, str, str]:
    try:
        object_id = parse_object_id(appliance_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appliance not found") from exc

    appliance = await db.appliances.find_one({"_id": object_id})
    if appliance is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appliance not found")

    if not is_netscaler_appliance(appliance):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This operation is only available for NetScaler appliances",
        )

    return (
        decrypt_value(appliance["encryptedHost"]),
        decrypt_value(appliance["encryptedUsername"]),
        decrypt_value(appliance["encryptedPassword"]),
    )


@router.post("/test", response_model=TestConnectionResponse)
async def test_appliance_preview(payload: ApplianceTestPreview) -> TestConnectionResponse:
    try:
        result = await test_appliance_via_mcp(payload.host, payload.username, payload.password, db=None)
        return TestConnectionResponse(**result)
    except Exception as exc:
        return TestConnectionResponse(success=False, message=str(exc))


@router.post("/{appliance_id}/test", response_model=TestConnectionResponse)
async def test_appliance(
    appliance_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> TestConnectionResponse:
    host, username, password = await _credentials_from_appliance(db, appliance_id)
    try:
        result = await test_appliance_via_mcp(host, username, password, db=db)
        return TestConnectionResponse(**result)
    except Exception as exc:
        return TestConnectionResponse(success=False, message=str(exc))


@router.post("/{appliance_id}/system-info")
async def appliance_system_info(
    appliance_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> dict:
    host, username, password = await _credentials_from_appliance(db, appliance_id)
    try:
        return await get_system_info_via_mcp(host, username, password, db=db)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc


@router.post("/{appliance_id}/lb-vservers")
async def appliance_lb_vservers(
    appliance_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> dict:
    host, username, password = await _credentials_from_appliance(db, appliance_id)
    try:
        return await list_lb_vservers_via_mcp(host, username, password, db=db)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
