from pydantic import BaseModel

from app.schemas.ai_provider import ProviderType


class AIProviderTestPreview(BaseModel):
    providerType: ProviderType
    apiKey: str = ""
    endpoint: str = ""
    model: str = ""


class AIModelsPreviewRequest(BaseModel):
    providerType: ProviderType
    apiKey: str = ""
    endpoint: str = ""


class ModelsResponse(BaseModel):
    models: list[str]
