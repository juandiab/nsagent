from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.dependencies import get_current_user, get_db
from app.models.user import serialize_user
from app.schemas.auth import LoginRequest, LoginResponse, MessageResponse, UserResponse
from app.services.auth_service import create_access_token, verify_password
from app.services.user_service import get_user_by_username

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
async def login(payload: LoginRequest, db: AsyncIOMotorDatabase = Depends(get_db)) -> LoginResponse:
    user = await get_user_by_username(db, payload.username)
    hashed = user.get("hashedPassword") if user else None
    if user is None or not hashed or not verify_password(payload.password, hashed):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
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
