import base64
import re
from typing import Any, Literal

from pydantic import BaseModel, Field

ChatRole = Literal["architect", "operator", "analyst"]


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


class CopilotRoleResponse(BaseModel):
    id: str
    label: str
    description: str
    requiresAppliance: bool
    suggestedPaneLabel: str
    handoffTarget: str | None = None


class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = []
    attachments: list[ChatAttachment] = []
    settings: CopilotSettings | None = None
    role: ChatRole = "operator"
    applianceName: str | None = None
    providerId: str | None = None
    webSearch: bool = True


class CopilotApplianceItem(BaseModel):
    id: str
    name: str
    environment: str
    enabled: bool
    notes: str = ""
    vendor: str = "netscaler"
    productId: str | None = None
    copilotEligible: bool = True


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


class InputFormField(BaseModel):
    id: str
    label: str
    type: str = "text"
    required: bool = False
    placeholder: str = ""
    hint: str = ""
    default: str | bool | int | float | None = None
    options: list[dict[str, str]] = []


class InputForm(BaseModel):
    title: str
    description: str = ""
    submitLabel: str = "Submit"
    fields: list[InputFormField] = []


class ChatResponse(BaseModel):
    role: str = "assistant"
    content: str
    providerName: str
    providerType: str
    model: str
    toolCalls: list[ToolCallTrace] = []
    inputForm: InputForm | None = None


class CopilotStatusResponse(BaseModel):
    ready: bool
    providerName: str | None = None
    providerType: str | None = None
    model: str | None = None
    message: str = ""
    settings: CopilotSettings = CopilotSettings()
