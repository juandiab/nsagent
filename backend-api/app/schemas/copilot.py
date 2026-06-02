import base64
import re
from typing import Any, Literal

from pydantic import BaseModel, Field


class CopilotSettings(BaseModel):
    allowImages: bool = True
    allowConfigFiles: bool = True
    maxAttachments: int = Field(default=5, ge=1, le=10)


class ChatAttachment(BaseModel):
    name: str
    kind: Literal["image", "config"]
    mimeType: str
    data: str


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = []
    attachments: list[ChatAttachment] = []
    settings: CopilotSettings | None = None
    applianceName: str | None = None
    providerId: str | None = None
    webSearch: bool = True


class CopilotApplianceItem(BaseModel):
    id: str
    name: str
    environment: str
    enabled: bool
    notes: str = ""


class CopilotConnectRequest(BaseModel):
    applianceName: str


class CopilotConnectResponse(BaseModel):
    success: bool
    applianceName: str
    environment: str = ""
    message: str
    api: str = "NetScaler Next-Gen API"
    apiPath: str = "/mgmt/api/nextgen/v1"
    loginEndpoint: str = "/mgmt/api/nextgen/v1/login"
    authenticatedUser: str = ""


class ToolCallTrace(BaseModel):
    name: str
    arguments: dict
    result: str


class ChatResponse(BaseModel):
    role: str = "assistant"
    content: str
    providerName: str
    providerType: str
    model: str
    toolCalls: list[ToolCallTrace] = []


class CopilotStatusResponse(BaseModel):
    ready: bool
    providerName: str | None = None
    providerType: str | None = None
    model: str | None = None
    message: str = ""
    settings: CopilotSettings = CopilotSettings()
