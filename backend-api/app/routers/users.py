from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.dependencies import get_current_user, get_db, require_admin
from app.schemas.auth import MessageResponse
from app.schemas.user import UserCreateRequest, UserDetailResponse, UserListItem, UserUpdateRequest
from app.services.user_service import (
    count_admins,
    create_user,
    delete_user,
    get_user_by_id,
    list_users,
    update_user,
)
from app.services.password_reset_service import send_reset_code
from app.services.webauthn_service import delete_passkey, list_user_passkeys

router = APIRouter(prefix="/users", tags=["users"])


def _serialize_passkeys(passkeys: list[dict]) -> list[dict]:
    return [
        {
            "id": str(item["_id"]),
            "label": item.get("label") or "Passkey",
            "createdAt": item["createdAt"],
            "lastUsedAt": item.get("lastUsedAt"),
        }
        for item in passkeys
    ]


@router.get("", response_model=list[UserListItem])
async def get_users(
    db=Depends(get_db),
    _: dict = Depends(require_admin),
) -> list[UserListItem]:
    return [UserListItem(**row) for row in await list_users(db)]


@router.post("", response_model=UserListItem, status_code=status.HTTP_201_CREATED)
async def post_user(
    payload: UserCreateRequest,
    db=Depends(get_db),
    _: dict = Depends(require_admin),
) -> UserListItem:
    try:
        row = await create_user(
            db,
            username=payload.username,
            display_name=payload.displayName,
            email=payload.email,
            password=payload.password,
            role=payload.role,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return UserListItem(**row)


@router.get("/{user_id}", response_model=UserDetailResponse)
async def get_user(
    user_id: str,
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> UserDetailResponse:
    if current_user.get("role") != "admin" and str(current_user["_id"]) != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    user = await get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    from app.models.user import serialize_user

    row = serialize_user(user)
    passkeys = await list_user_passkeys(db, user["_id"])
    row["passkeyCount"] = len(passkeys)
    row["passkeys"] = _serialize_passkeys(passkeys)
    return UserDetailResponse(**row)


@router.put("/{user_id}", response_model=UserListItem)
async def put_user(
    user_id: str,
    payload: UserUpdateRequest,
    db=Depends(get_db),
    current_user: dict = Depends(require_admin),
) -> UserListItem:
    if payload.role == "user" and current_user.get("role") == "admin":
        target = await get_user_by_id(db, user_id)
        if target and target.get("role") == "admin" and await count_admins(db) <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot demote the last admin user",
            )

    try:
        updated = await update_user(
            db,
            user_id,
            display_name=payload.displayName,
            email=payload.email,
            role=payload.role,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    if updated is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserListItem(**updated)


@router.delete("/{user_id}", response_model=MessageResponse)
async def remove_user(
    user_id: str,
    db=Depends(get_db),
    current_user: dict = Depends(require_admin),
) -> MessageResponse:
    if str(current_user["_id"]) == user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot delete your own account")

    target = await get_user_by_id(db, user_id)
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if target.get("role") == "admin" and await count_admins(db) <= 1:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete the last admin user")

    await delete_user(db, user_id)
    return MessageResponse(message="User deleted")


@router.delete("/{user_id}/passkeys/{passkey_id}", response_model=MessageResponse)
async def remove_passkey(
    user_id: str,
    passkey_id: str,
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> MessageResponse:
    if current_user.get("role") != "admin" and str(current_user["_id"]) != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    user = await get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    try:
        oid = ObjectId(passkey_id)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid passkey id") from exc

    passkeys = await list_user_passkeys(db, user["_id"])
    owned = next((item for item in passkeys if item["_id"] == oid), None)
    if owned is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Passkey not found")

    if len(passkeys) <= 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove the last passkey — register a replacement first",
        )

    await delete_passkey(db, oid)
    return MessageResponse(message="Passkey removed")


@router.post("/{user_id}/reset-password", response_model=MessageResponse)
async def request_user_password_reset(
    user_id: str,
    db=Depends(get_db),
    current_user: dict = Depends(require_admin),
) -> MessageResponse:
    user = await get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    try:
        masked_email = await send_reset_code(db, user=user, initiated_by=current_user["username"])
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc

    return MessageResponse(message=f"Account recovery code sent to {masked_email}")
