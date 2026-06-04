from datetime import datetime, timezone
from typing import Any

from bson import ObjectId

from app.schemas.ai_provider import ALL_LLM_ROLES


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def provider_roles(doc: dict[str, Any]) -> list[str]:
    roles = doc.get("roles")
    if not roles:
        return list(ALL_LLM_ROLES)
    return list(roles)


def provider_supports_role(doc: dict[str, Any], role: str) -> bool:
    normalized = role.strip().lower()
    return normalized in provider_roles(doc)


def serialize_ai_provider(doc: dict[str, Any]) -> dict[str, Any]:
    endpoint = doc.get("endpoint", "")
    if doc.get("providerType") == "LM Studio" and endpoint.strip():
        from app.services.ai_provider_service import normalize_lm_studio_endpoint

        endpoint = normalize_lm_studio_endpoint(endpoint)

    return {
        "id": str(doc["_id"]),
        "providerName": doc["providerName"],
        "providerType": doc["providerType"],
        "endpoint": endpoint,
        "model": doc["model"],
        "enabled": doc["enabled"],
        "isDefault": doc.get("isDefault", False),
        "roles": provider_roles(doc),
        "createdAt": doc["createdAt"],
        "updatedAt": doc["updatedAt"],
    }


def build_ai_provider_document(payload: dict[str, Any], encrypted_api_key: str) -> dict[str, Any]:
    now = utc_now()
    return {
        "providerName": payload["providerName"],
        "providerType": payload["providerType"],
        "encryptedApiKey": encrypted_api_key,
        "endpoint": payload.get("endpoint", ""),
        "model": payload["model"],
        "enabled": payload.get("enabled", True),
        "isDefault": payload.get("isDefault", False),
        "roles": payload.get("roles") or list(ALL_LLM_ROLES),
        "createdAt": now,
        "updatedAt": now,
    }


def parse_object_id(provider_id: str) -> ObjectId:
    if not ObjectId.is_valid(provider_id):
        raise ValueError("Invalid AI provider ID")
    return ObjectId(provider_id)
