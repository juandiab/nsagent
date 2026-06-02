from typing import Any

from pydantic import BaseModel, Field


class WebAuthnUsernameRequest(BaseModel):
    username: str = Field(min_length=1, max_length=64)


class WebAuthnRegisterFinishRequest(WebAuthnUsernameRequest):
    credential: dict[str, Any]
    label: str = Field(default="", max_length=128)


class WebAuthnLoginFinishRequest(WebAuthnUsernameRequest):
    credential: dict[str, Any]


class WebAuthnStatusResponse(BaseModel):
    username: str
    exists: bool
    hasPasskey: bool
    canRegister: bool
