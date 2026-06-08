from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.dependencies import get_current_user, get_db
from app.schemas.slack_settings import SlackSettingsResponse, SlackSettingsUpdate, SlackTestRequest
from app.schemas.test import TestConnectionResponse
from app.services.slack_notification_service import test_slack_notification
from app.services.slack_settings_service import get_slack_settings, update_slack_settings

router = APIRouter(prefix="/integrations", tags=["integrations"])


@router.get("/slack", response_model=SlackSettingsResponse)
async def read_slack_settings(
    db: AsyncIOMotorDatabase = Depends(get_db),
    _: dict = Depends(get_current_user),
) -> SlackSettingsResponse:
    return await get_slack_settings(db)


@router.put("/slack", response_model=SlackSettingsResponse)
async def save_slack_settings(
    payload: SlackSettingsUpdate,
    db: AsyncIOMotorDatabase = Depends(get_db),
    _: dict = Depends(get_current_user),
) -> SlackSettingsResponse:
    try:
        return await update_slack_settings(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/slack/test", response_model=TestConnectionResponse)
async def test_slack_settings(
    payload: SlackTestRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
    _: dict = Depends(get_current_user),
) -> TestConnectionResponse:
    try:
        success, message = await test_slack_notification(
            db,
            webhook_url=payload.webhookUrl,
            message=payload.message,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return TestConnectionResponse(success=success, message=message)
