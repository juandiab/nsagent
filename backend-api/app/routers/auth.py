from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.dependencies import get_current_user, get_db
from app.models.user import serialize_user
from app.schemas.auth import LoginRequest, LoginResponse, MessageResponse, UserResponse
from app.schemas.password_reset import (
    AccountRecoveryConfirmResponse,
    AccountRecoveryRequest,
    PasswordResetConfirmRequest,
)
from app.services.auth_lockout_service import (
    clear_login_lockout,
    get_login_lockout_message,
    record_login_failure,
)
from app.services.auth_service import create_access_token, verify_password
from app.services.user_service import get_user_by_username
from app.services.password_reset_service import (
    confirm_reset,
    request_self_service_recovery,
)
from app.services.webauthn_service import count_user_passkeys

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
async def login(payload: LoginRequest, db: AsyncIOMotorDatabase = Depends(get_db)) -> LoginResponse:
    lockout_message = await get_login_lockout_message(db, username=payload.username)
    if lockout_message:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=lockout_message)

    user = await get_user_by_username(db, payload.username)
    hashed = user.get("hashedPassword") if user else None
    if user is None or not hashed or not verify_password(payload.password, hashed):
        lockout_message = await record_login_failure(db, username=payload.username)
        if lockout_message:
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=lockout_message)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    await clear_login_lockout(db, username=payload.username)

    if await count_user_passkeys(db, user["_id"]) > 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account uses passkey sign-in only. Use your passkey or account recovery.",
        )

    return LoginResponse(
        accessToken=create_access_token(user["username"]),
        user=UserResponse(**serialize_user(user)),
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)) -> UserResponse:
    return UserResponse(**serialize_user(current_user))


@router.post("/logout", response_model=MessageResponse)
async def logout(_: dict = Depends(get_current_user)) -> MessageResponse:
    return MessageResponse(message="Logged out successfully")


@router.post("/account-recovery/request", response_model=MessageResponse)
async def account_recovery_request(
    payload: AccountRecoveryRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> MessageResponse:
    message = await request_self_service_recovery(db, username=payload.username)
    return MessageResponse(message=message)


@router.post("/password-reset/confirm", response_model=AccountRecoveryConfirmResponse)
async def password_reset_confirm(
    payload: PasswordResetConfirmRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> AccountRecoveryConfirmResponse:
    try:
        message, recovery_token = await confirm_reset(
            db,
            username=payload.username,
            code=payload.code,
            new_password=payload.newPassword,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return AccountRecoveryConfirmResponse(message=message, recoveryToken=recovery_token)
