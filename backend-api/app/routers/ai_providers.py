from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ReturnDocument

from app.dependencies import get_db
from app.models.ai_provider import (
    build_ai_provider_document,
    parse_object_id,
    serialize_ai_provider,
    utc_now,
)
from app.schemas.ai_provider import AIProviderCreate, AIProviderResponse, AIProviderUpdate
from app.schemas.ai_provider_ops import (
    AIModelsPreviewRequest,
    AIProviderTestPreview,
    ModelsResponse,
)
from app.schemas.test import TestConnectionResponse
from app.services.ai_provider_service import (
    ENDPOINT_REQUIRED_PROVIDER_TYPES,
    fetch_models,
    normalize_lm_studio_endpoint,
    test_provider,
)
from app.services.encryption_service import decrypt_value, encrypt_value

router = APIRouter(prefix="/ai-providers", tags=["ai-providers"])


def _should_update_api_key(value: str | None) -> bool:
    return value is not None and value != ""


async def _unset_all_defaults(db: AsyncIOMotorDatabase) -> None:
    await db.aiProviders.update_many({}, {"$set": {"isDefault": False, "updatedAt": utc_now()}})


@router.get("/endpoint-hints")
async def get_endpoint_hints() -> dict[str, dict[str, str | bool]]:
    from app.services.ai_provider_service import PROVIDER_DEFAULTS

    return {
        provider: {
            "hint": meta.get("endpoint_hint", ""),
            "example": meta.get("endpoint_example", ""),
            "required": provider in ENDPOINT_REQUIRED_PROVIDER_TYPES,
        }
        for provider, meta in PROVIDER_DEFAULTS.items()
    }


@router.post("/models/preview", response_model=ModelsResponse)
async def preview_models(payload: AIModelsPreviewRequest) -> ModelsResponse:
    try:
        models = await fetch_models(payload.providerType, payload.apiKey, payload.endpoint)
        return ModelsResponse(models=models)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to fetch models: {exc}",
        ) from exc


@router.post("/test/preview", response_model=TestConnectionResponse)
async def test_provider_preview(payload: AIProviderTestPreview) -> TestConnectionResponse:
    success, message = await test_provider(
        payload.providerType,
        payload.apiKey,
        payload.endpoint,
        payload.model,
    )
    return TestConnectionResponse(success=success, message=message)


@router.get("/{provider_id}/models", response_model=ModelsResponse)
async def get_provider_models(
    provider_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> ModelsResponse:
    provider = await _get_provider_or_404(provider_id, db)
    api_key = decrypt_value(provider["encryptedApiKey"])
    try:
        models = await fetch_models(provider["providerType"], api_key, provider.get("endpoint", ""))
        return ModelsResponse(models=models)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to fetch models: {exc}",
        ) from exc


@router.post("/{provider_id}/test", response_model=TestConnectionResponse)
async def test_saved_provider(
    provider_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> TestConnectionResponse:
    provider = await _get_provider_or_404(provider_id, db)
    api_key = decrypt_value(provider["encryptedApiKey"])
    success, message = await test_provider(
        provider["providerType"],
        api_key,
        provider.get("endpoint", ""),
        provider.get("model", ""),
    )
    return TestConnectionResponse(success=success, message=message)


async def _get_provider_or_404(provider_id: str, db: AsyncIOMotorDatabase) -> dict:
    try:
        object_id = parse_object_id(provider_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI provider not found") from exc

    provider = await db.aiProviders.find_one({"_id": object_id})
    if provider is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI provider not found")
    return provider


@router.get("", response_model=list[AIProviderResponse])
async def list_ai_providers(db: AsyncIOMotorDatabase = Depends(get_db)) -> list[dict]:
    providers = await db.aiProviders.find().sort("providerName", 1).to_list(length=None)
    return [serialize_ai_provider(doc) for doc in providers]


@router.get("/{provider_id}", response_model=AIProviderResponse)
async def get_ai_provider(
    provider_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> dict:
    try:
        object_id = parse_object_id(provider_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI provider not found") from exc

    provider = await db.aiProviders.find_one({"_id": object_id})
    if provider is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI provider not found")

    return serialize_ai_provider(provider)


def _normalize_provider_endpoint(provider_type: str, endpoint: str) -> str:
    if provider_type == "LM Studio" and endpoint.strip():
        return normalize_lm_studio_endpoint(endpoint)
    return endpoint


@router.post("", response_model=AIProviderResponse, status_code=status.HTTP_201_CREATED)
async def create_ai_provider(
    payload: AIProviderCreate,
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> dict:
    if payload.isDefault:
        await _unset_all_defaults(db)

    data = payload.model_dump()
    data["endpoint"] = _normalize_provider_endpoint(payload.providerType, payload.endpoint)
    encrypted_api_key = encrypt_value(payload.apiKey)
    document = build_ai_provider_document(data, encrypted_api_key)
    result = await db.aiProviders.insert_one(document)
    created = await db.aiProviders.find_one({"_id": result.inserted_id})
    return serialize_ai_provider(created)


@router.put("/{provider_id}", response_model=AIProviderResponse)
async def update_ai_provider(
    provider_id: str,
    payload: AIProviderUpdate,
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> dict:
    try:
        object_id = parse_object_id(provider_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI provider not found") from exc

    existing = await db.aiProviders.find_one({"_id": object_id})
    if existing is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI provider not found")

    if payload.isDefault:
        await _unset_all_defaults(db)

    update_data: dict = {"updatedAt": utc_now()}

    if payload.providerName is not None:
        update_data["providerName"] = payload.providerName
    if payload.providerType is not None:
        update_data["providerType"] = payload.providerType
    if payload.endpoint is not None:
        provider_type = payload.providerType or existing["providerType"]
        update_data["endpoint"] = _normalize_provider_endpoint(provider_type, payload.endpoint)
    if payload.model is not None:
        update_data["model"] = payload.model
    if payload.enabled is not None:
        update_data["enabled"] = payload.enabled
    if payload.isDefault is not None:
        update_data["isDefault"] = payload.isDefault
    if payload.roles is not None:
        update_data["roles"] = payload.roles

    if _should_update_api_key(payload.apiKey):
        update_data["encryptedApiKey"] = encrypt_value(payload.apiKey)

    await db.aiProviders.update_one({"_id": object_id}, {"$set": update_data})
    updated = await db.aiProviders.find_one({"_id": object_id})
    return serialize_ai_provider(updated)


@router.delete("/{provider_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ai_provider(
    provider_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> None:
    try:
        object_id = parse_object_id(provider_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI provider not found") from exc

    result = await db.aiProviders.delete_one({"_id": object_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI provider not found")


@router.patch("/{provider_id}/set-default", response_model=AIProviderResponse)
async def set_default_ai_provider(
    provider_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> dict:
    try:
        object_id = parse_object_id(provider_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI provider not found") from exc

    existing = await db.aiProviders.find_one({"_id": object_id})
    if existing is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI provider not found")

    await _unset_all_defaults(db)
    result = await db.aiProviders.find_one_and_update(
        {"_id": object_id},
        {"$set": {"isDefault": True, "updatedAt": utc_now()}},
        return_document=ReturnDocument.AFTER,
    )
    return serialize_ai_provider(result)
