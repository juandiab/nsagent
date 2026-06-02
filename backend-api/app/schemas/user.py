from datetime import datetime

from pydantic import BaseModel, Field


class UserCreateRequest(BaseModel):
    username: str = Field(min_length=2, max_length=64, pattern=r"^[a-zA-Z0-9._-]+$")
    displayName: str = Field(min_length=1, max_length=128)
    password: str = Field(min_length=8, max_length=128)
    role: str = Field(default="user", pattern=r"^(admin|user)$")


class UserUpdateRequest(BaseModel):
    displayName: str | None = Field(default=None, min_length=1, max_length=128)
    role: str | None = Field(default=None, pattern=r"^(admin|user)$")


class PasskeySummary(BaseModel):
    id: str
    label: str
    createdAt: datetime
    lastUsedAt: datetime | None = None


class UserListItem(BaseModel):
    id: str
    username: str
    displayName: str
    role: str
    passkeyCount: int
    createdAt: datetime


class UserDetailResponse(UserListItem):
    passkeys: list[PasskeySummary]
