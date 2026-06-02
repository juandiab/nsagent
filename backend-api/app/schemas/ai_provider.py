from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


ProviderType = Literal["OpenAI", "Anthropic", "Gemini", "Grok", "DeepSeek", "LM Studio", "OpenAI-Compatible"]


class AIProviderCreate(BaseModel):
    providerName: str
    providerType: ProviderType
    apiKey: str
    endpoint: str = ""
    model: str
    enabled: bool = True
    isDefault: bool = False


class AIProviderUpdate(BaseModel):
    providerName: str | None = None
    providerType: ProviderType | None = None
    apiKey: str | None = None
    endpoint: str | None = None
    model: str | None = None
    enabled: bool | None = None
    isDefault: bool | None = None


class AIProviderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    providerName: str
    providerType: str
    endpoint: str
    model: str
    enabled: bool
    isDefault: bool
    createdAt: datetime = Field(alias="createdAt")
    updatedAt: datetime = Field(alias="updatedAt")
