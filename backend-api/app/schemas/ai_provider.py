from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


ProviderType = Literal["OpenAI", "Anthropic", "Gemini", "Grok", "DeepSeek", "LM Studio", "OpenAI-Compatible"]
LLMRole = Literal["architect", "operator", "analyst"]
ALL_LLM_ROLES: list[LLMRole] = ["architect", "operator", "analyst"]


def _normalize_llm_roles(roles: list[str] | None) -> list[LLMRole]:
    if not roles:
        return list(ALL_LLM_ROLES)
    normalized = [role.strip().lower() for role in roles if role and role.strip()]
    unique = list(dict.fromkeys(normalized))
    invalid = [role for role in unique if role not in ALL_LLM_ROLES]
    if invalid:
        raise ValueError(f"Invalid LLM role(s): {', '.join(invalid)}")
    if not unique:
        raise ValueError("At least one LLM role is required")
    return unique  # type: ignore[return-value]


class AIProviderCreate(BaseModel):
    providerName: str
    providerType: ProviderType
    apiKey: str
    endpoint: str = ""
    model: str
    enabled: bool = True
    isDefault: bool = False
    roles: list[LLMRole] = Field(default_factory=lambda: list(ALL_LLM_ROLES))

    @field_validator("roles")
    @classmethod
    def validate_roles(cls, roles: list[str]) -> list[LLMRole]:
        return _normalize_llm_roles(roles)


class AIProviderUpdate(BaseModel):
    providerName: str | None = None
    providerType: ProviderType | None = None
    apiKey: str | None = None
    endpoint: str | None = None
    model: str | None = None
    enabled: bool | None = None
    isDefault: bool | None = None
    roles: list[LLMRole] | None = None

    @field_validator("roles")
    @classmethod
    def validate_roles(cls, roles: list[str] | None) -> list[LLMRole] | None:
        if roles is None:
            return None
        return _normalize_llm_roles(roles)


class AIProviderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    providerName: str
    providerType: str
    endpoint: str
    model: str
    enabled: bool
    isDefault: bool
    roles: list[LLMRole]
    createdAt: datetime = Field(alias="createdAt")
    updatedAt: datetime = Field(alias="updatedAt")
