from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.dependencies import get_current_user, get_db, get_optional_current_user, require_admin
from app.schemas.auth import MessageResponse
from app.schemas.webauthn import (
    WebAuthnLoginFinishRequest,
    WebAuthnRegisterBeginRequest,
    WebAuthnRegisterFinishRequest,
    WebAuthnStatusResponse,
    WebAuthnUsernameRequest,
)
from app.services.auth_service import create_access_token, decode_recovery_token
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


def _recovery_username(recovery_token: str | None) -> str | None:
    if not recovery_token or not recovery_token.strip():
        return None
    return decode_recovery_token(recovery_token.strip())


def _can_register_passkey(
    user: dict[str, Any],
    passkey_count: int,
    current_user: dict | None,
    recovery_username: str | None,
) -> bool:
    if recovery_username is not None and recovery_username == user["username"]:
        return True
    if current_user is None:
        return False
    if current_user["_id"] == user["_id"]:
        return True
    return current_user.get("role") == "admin"


def _require_email_for_first_passkey(user: dict[str, Any], passkey_count: int) -> None:
    if passkey_count > 0:
        return
    if not (user.get("email") or "").strip():
        raise ValueError(
            "Add an email address to your account before registering a passkey "
            "(required for account recovery)"
        )


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
            passkeyRequired=False,
            canRegister=False,
        )

    passkey_count = await count_user_passkeys(db, user["_id"])
    has_passkey = passkey_count > 0
    return WebAuthnStatusResponse(
        username=user["username"],
        exists=True,
        hasPasskey=has_passkey,
        passkeyRequired=has_passkey,
        canRegister=_can_register_passkey(user, passkey_count, current_user, None),
    )


@router.post("/register/begin")
async def register_begin(
    payload: WebAuthnRegisterBeginRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict | None = Depends(get_optional_current_user),
) -> dict[str, Any]:
    user = await _resolve_user(db, payload.username)
    passkey_count = await count_user_passkeys(db, user["_id"])
    recovery_username = _recovery_username(payload.recoveryToken)
    if not _can_register_passkey(user, passkey_count, current_user, recovery_username):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Passkey registration is not allowed for this user",
        )

    try:
        _require_email_for_first_passkey(user, passkey_count)
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
    recovery_username = _recovery_username(payload.recoveryToken)
    if not _can_register_passkey(user, passkey_count, current_user, recovery_username):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Passkey registration is not allowed for this user",
        )

    try:
        _require_email_for_first_passkey(user, passkey_count)
        await finish_registration(db, user, payload.credential, label=payload.label)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    if recovery_username is not None:
        return _login_response(user)

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
