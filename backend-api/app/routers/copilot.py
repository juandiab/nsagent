from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.dependencies import get_db
from app.schemas.test import TestConnectionResponse
from app.services.brave_search_service import test_brave_search
from app.services.copilot_platform_service import (
    CopilotPlatformSettingsResponse,
    CopilotPlatformSettingsUpdate,
    get_brave_api_key,
    get_platform_settings,
    update_platform_settings,
)
from app.services.copilot_orchestrator import get_default_provider, resolve_chat_provider, run_copilot_chat
from app.services.ai_provider_errors import (
    AiProviderError,
    enrich_ai_provider_error,
    maybe_parse_ai_provider_error,
)
from app.schemas.copilot import (
    ChatRequest,
    ChatResponse,
    CopilotApplianceItem,
    CopilotConnectRequest,
    CopilotConnectResponse,
    CopilotSettings,
    CopilotStatusResponse,
)
from app.schemas.model_usage import ModelUsageDashboardResponse, UsageLimitsUpdate
from app.services.model_usage_service import get_usage_dashboard, update_usage_limits
from app.services.copilot_appliance_service import connect_appliance, list_copilot_appliances

router = APIRouter(prefix="/copilot", tags=["copilot"])

DEFAULT_SETTINGS = CopilotSettings()


@router.get("/settings", response_model=CopilotSettings)
async def get_copilot_settings() -> CopilotSettings:
    return DEFAULT_SETTINGS


@router.get("/platform-settings", response_model=CopilotPlatformSettingsResponse)
async def read_platform_settings(
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> CopilotPlatformSettingsResponse:
    return await get_platform_settings(db)


@router.put("/platform-settings", response_model=CopilotPlatformSettingsResponse)
async def save_platform_settings(
    payload: CopilotPlatformSettingsUpdate,
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> CopilotPlatformSettingsResponse:
    if payload.allowWebSearch and payload.braveSearchApiKey is None:
        existing = await get_platform_settings(db)
        if not existing.hasBraveSearchApiKey:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Brave Search API key is required when web search is enabled",
            )
    return await update_platform_settings(db, payload)


@router.post("/platform-settings/test", response_model=TestConnectionResponse)
async def test_platform_search(
    payload: CopilotPlatformSettingsUpdate,
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> TestConnectionResponse:
    api_key = (payload.braveSearchApiKey or "").strip()
    if not api_key:
        api_key = await get_brave_api_key(db)
    if not api_key:
        return TestConnectionResponse(success=False, message="Brave Search API key is not configured")
    success, message = await test_brave_search(api_key)
    if success:
        from app.services.model_usage_service import record_brave_search_usage

        await record_brave_search_usage(db, queries=1)
    return TestConnectionResponse(success=success, message=message)


@router.get("/usage-dashboard", response_model=ModelUsageDashboardResponse)
async def read_usage_dashboard(
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> ModelUsageDashboardResponse:
    return await get_usage_dashboard(db)


@router.put("/usage-limits", response_model=ModelUsageDashboardResponse)
async def save_usage_limits(
    payload: UsageLimitsUpdate,
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> ModelUsageDashboardResponse:
    await update_usage_limits(db, payload)
    return await get_usage_dashboard(db)


@router.get("/status", response_model=CopilotStatusResponse)
async def copilot_status(db: AsyncIOMotorDatabase = Depends(get_db)) -> CopilotStatusResponse:
    provider = await get_default_provider(db)
    if provider is None:
        return CopilotStatusResponse(
            ready=False,
            message="No enabled AI provider found. Configure one and set it as default.",
            settings=DEFAULT_SETTINGS,
        )

    return CopilotStatusResponse(
        ready=True,
        providerName=provider["providerName"],
        providerType=provider["providerType"],
        model=provider["model"],
        message="Copilot is ready",
        settings=DEFAULT_SETTINGS,
    )


@router.get("/appliances", response_model=list[CopilotApplianceItem])
async def copilot_appliances(
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> list[dict]:
    return await list_copilot_appliances(db)


@router.post("/connect", response_model=CopilotConnectResponse)
async def copilot_connect(
    payload: CopilotConnectRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> dict:
    appliance_name = payload.applianceName.strip()
    if not appliance_name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="applianceName is required")
    try:
        return await connect_appliance(db, appliance_name)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Next-Gen API login failed: {exc}",
        ) from exc


@router.post("/chat", response_model=ChatResponse)
async def copilot_chat(
    payload: ChatRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> ChatResponse:
    settings = payload.settings or DEFAULT_SETTINGS

    if not payload.message.strip() and not payload.attachments:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message or attachments are required",
        )

    appliance_name = (payload.applianceName or "").strip()
    if not appliance_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Select and connect to a NetScaler appliance before chatting",
        )

    provider = await resolve_chat_provider(db, payload.providerId)

    try:
        history = [item.model_dump() for item in payload.history]
        return await run_copilot_chat(
            db,
            payload.message.strip(),
            history,
            attachments=payload.attachments,
            settings=settings,
            appliance_name=appliance_name,
            provider_id=payload.providerId,
            web_search=payload.webSearch,
        )
    except AiProviderError as exc:
        if provider and not exc.provider_name:
            exc.provider_name = provider.get("providerName", "")
        detail = await enrich_ai_provider_error(db, exc, payload.providerId)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
        ) from exc
    except ValueError as exc:
        if isinstance(exc, AiProviderError):
            detail = await enrich_ai_provider_error(db, exc, payload.providerId)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=detail,
            ) from exc
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        provider_type = provider.get("providerType", "") if provider else ""
        model = provider.get("model", "") if provider else ""
        provider_name = provider.get("providerName", "") if provider else ""
        parsed = maybe_parse_ai_provider_error(
            str(exc),
            provider_type=provider_type,
            model=model,
            provider_name=provider_name,
        )
        if parsed is not None:
            detail = await enrich_ai_provider_error(db, parsed, payload.providerId)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=detail,
            ) from exc
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Copilot request failed: {exc}",
        ) from exc
