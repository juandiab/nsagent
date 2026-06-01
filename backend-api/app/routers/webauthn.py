from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.dependencies import get_current_user, get_db, get_optional_current_user, require_admin
from app.schemas.auth import MessageResponse
from app.schemas.webauthn import (
    WebAuthnLoginFinishRequest,
    WebAuthnRegisterFinishRequest,
    WebAuthnStatusResponse,
    WebAuthnUsernameRequest,
)
from app.services.auth_service import create_access_token
from app.services.user_service import get_user_by_username
from app.services.webauthn_service import (
    begin_authentication,
    begin_registration,
    count_user_passkeys,
    finish_authentication,
    finish_registration,
)

router = APIRouter(prefix="/auth/webauthn", tags=["webauthn"])


def _login_response(user: dict[str, Any]) -> dict[str, Any]:
    from app.models.user import serialize_user

    token = create_access_token(user["username"])
    return {
        "accessToken": token,
        "tokenType": "bearer",
        "user": serialize_user(user),
    }


async def _resolve_user(db: AsyncIOMotorDatabase, username: str) -> dict:
    user = await get_user_by_username(db, username)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


def _can_register_passkey(
    user: dict[str, Any],
    passkey_count: int,
    current_user: dict | None,
) -> bool:
    if current_user is None:
        return False
    if current_user["_id"] == user["_id"]:
        return True
    return current_user.get("role") == "admin"


@router.post("/status", response_model=WebAuthnStatusResponse)
async def passkey_status(
    payload: WebAuthnUsernameRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict | None = Depends(get_optional_current_user),
) -> WebAuthnStatusResponse:
    user = await get_user_by_username(db, payload.username)
    if user is None:
        return WebAuthnStatusResponse(
            username=payload.username.strip().lower(),
            exists=False,
            hasPasskey=False,
            canRegister=False,
        )

    passkey_count = await count_user_passkeys(db, user["_id"])
    return WebAuthnStatusResponse(
        username=user["username"],
        exists=True,
        hasPasskey=passkey_count > 0,
        canRegister=_can_register_passkey(user, passkey_count, current_user),
    )


@router.post("/register/begin")
async def register_begin(
    payload: WebAuthnUsernameRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict | None = Depends(get_optional_current_user),
) -> dict[str, Any]:
    user = await _resolve_user(db, payload.username)
    passkey_count = await count_user_passkeys(db, user["_id"])
    if not _can_register_passkey(user, passkey_count, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Passkey registration is not allowed for this user",
        )

    try:
        return await begin_registration(db, user)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/register/finish")
async def register_finish(
    payload: WebAuthnRegisterFinishRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict | None = Depends(get_optional_current_user),
) -> dict[str, Any]:
    user = await _resolve_user(db, payload.username)
    passkey_count = await count_user_passkeys(db, user["_id"])
    if not _can_register_passkey(user, passkey_count, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Passkey registration is not allowed for this user",
        )

    try:
        await finish_registration(db, user, payload.credential, label=payload.label)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return {"success": True, "message": "Passkey registered"}


@router.post("/login/begin")
async def login_begin(
    payload: WebAuthnUsernameRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> dict[str, Any]:
    user = await _resolve_user(db, payload.username)
    try:
        return await begin_authentication(db, user)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/login/finish")
async def login_finish(
    payload: WebAuthnLoginFinishRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> dict[str, Any]:
    user = await _resolve_user(db, payload.username)
    try:
        await finish_authentication(db, user, payload.credential)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    return _login_response(user)
