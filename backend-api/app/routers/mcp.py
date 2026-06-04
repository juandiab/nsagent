from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.dependencies import get_current_user, get_db
from app.schemas.mcp_config import MCPSettingsResponse, MCPSettingsUpdate, MCPStatusResponse
from app.schemas.smtp_settings import SMTPSettingsResponse, SMTPSettingsUpdate, SMTPTestRequest
from app.schemas.test import TestConnectionResponse
from app.services.mcp_client import get_mcp_health, list_mcp_tools, push_config_to_mcp_server
from app.services.mcp_config_service import ALL_TOOL_NAMES, get_mcp_settings, update_mcp_settings
from app.services.smtp_settings_service import (
    get_smtp_settings,
    test_smtp_settings,
    update_smtp_settings,
)
from app.services.beta_features_catalog import (
    get_beta_feature_options,
    get_beta_features_info,
    get_beta_products,
)
from app.services.nextgen_catalog import get_nextgen_api_info, get_nextgen_options, get_tool_catalog
from app.services.nextgen_api_reference import get_api_categories

router = APIRouter(prefix="/mcp", tags=["mcp"])

TOOL_CATALOG = get_tool_catalog()


@router.get("/tools")
async def get_mcp_tools(
    db: AsyncIOMotorDatabase = Depends(get_db),
    _: dict = Depends(get_current_user),
) -> dict:
    return await list_mcp_tools(db)


@router.get("/config")
async def read_mcp_config(
    db: AsyncIOMotorDatabase = Depends(get_db),
    _: dict = Depends(get_current_user),
) -> dict:
    settings = await get_mcp_settings(db)
    return {
        **settings.model_dump(),
        "availableTools": TOOL_CATALOG,
        "nextGenApi": get_nextgen_api_info(),
        "nextGenOptions": get_nextgen_options(),
        "nextGenApiCategories": get_api_categories(),
        "betaFeatures": get_beta_features_info(),
        "betaProducts": get_beta_products(),
        "betaFeatureOptions": get_beta_feature_options(),
    }


@router.put("/config", response_model=MCPSettingsResponse)
async def save_mcp_config(
    payload: MCPSettingsUpdate,
    db: AsyncIOMotorDatabase = Depends(get_db),
    _: dict = Depends(get_current_user),
) -> MCPSettingsResponse:
    try:
        settings = await update_mcp_settings(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    try:
        await push_config_to_mcp_server(settings)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Settings saved but MCP server sync failed: {exc}",
        ) from exc

    return settings


@router.get("/status", response_model=MCPStatusResponse)
async def get_mcp_status(
    db: AsyncIOMotorDatabase = Depends(get_db),
    _: dict = Depends(get_current_user),
) -> MCPStatusResponse:
    settings = await get_mcp_settings(db)
    try:
        health = await get_mcp_health(db)
        return MCPStatusResponse(
            online=True,
            serverUrl=settings.serverUrl,
            message="MCP server is reachable",
            toolCount=len(ALL_TOOL_NAMES),
            enabledToolCount=health["toolCount"],
        )
    except Exception as exc:
        return MCPStatusResponse(
            online=False,
            serverUrl=settings.serverUrl,
            message=str(exc),
            toolCount=len(ALL_TOOL_NAMES),
            enabledToolCount=len(settings.enabledTools),
        )


@router.get("/smtp", response_model=SMTPSettingsResponse)
async def read_smtp_settings(
    db: AsyncIOMotorDatabase = Depends(get_db),
    _: dict = Depends(get_current_user),
) -> SMTPSettingsResponse:
    return await get_smtp_settings(db)


@router.put("/smtp", response_model=SMTPSettingsResponse)
async def save_smtp_settings(
    payload: SMTPSettingsUpdate,
    db: AsyncIOMotorDatabase = Depends(get_db),
    _: dict = Depends(get_current_user),
) -> SMTPSettingsResponse:
    try:
        return await update_smtp_settings(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/smtp/test", response_model=TestConnectionResponse)
async def test_smtp(
    payload: SMTPTestRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
    _: dict = Depends(get_current_user),
) -> TestConnectionResponse:
    success, message = await test_smtp_settings(db, payload)
    return TestConnectionResponse(success=success, message=message)
