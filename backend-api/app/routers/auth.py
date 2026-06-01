from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.dependencies import get_current_user, get_db
from app.schemas.auth import LoginRequest, LoginResponse, MessageResponse, UserResponse
from app.services.auth_service import create_access_token, verify_password
from app.services.user_service import get_user_by_username

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
async def login(payload: LoginRequest, db: AsyncIOMotorDatabase = Depends(get_db)) -> LoginResponse:
    user = await get_user_by_username(db, payload.username)
    if user is None or not verify_password(payload.password, user["hashedPassword"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    token = create_access_token(user["username"])
    return LoginResponse(
        accessToken=token,
        user=UserResponse(username=user["username"]),
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)) -> UserResponse:
    return UserResponse(username=current_user["username"])


@router.post("/logout", response_model=MessageResponse)
async def logout(_: dict = Depends(get_current_user)) -> MessageResponse:
    return MessageResponse(message="Logged out successfully")
