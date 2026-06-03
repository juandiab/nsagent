from datetime import datetime

from pydantic import BaseModel, Field


class SMTPSettingsUpdate(BaseModel):
    provider: str = "custom"
    host: str = ""
    port: int = Field(default=587, ge=1, le=65535)
    username: str = ""
    password: str | None = None
    fromAddress: str = ""
    useTls: bool = True
    useSsl: bool = False


class SMTPSettingsResponse(BaseModel):
    provider: str = "custom"
    host: str = ""
    port: int = 587
    username: str = ""
    hasPassword: bool = False
    fromAddress: str = ""
    useTls: bool = True
    useSsl: bool = False
    updatedAt: datetime | None = None


class SMTPTestRequest(SMTPSettingsUpdate):
    testRecipient: str
