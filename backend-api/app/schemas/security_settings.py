from typing import Literal

from pydantic import BaseModel, Field

PasskeyPolicy = Literal["disabled", "enabled", "enforced"]


class SecuritySettingsResponse(BaseModel):
    passkeyPolicy: PasskeyPolicy = "enabled"


class SecuritySettingsUpdate(BaseModel):
    passkeyPolicy: PasskeyPolicy = Field(default="enabled")
