from datetime import datetime, timezone
from typing import Any

from bson import ObjectId


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def serialize_appliance(doc: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(doc["_id"]),
        "name": doc["name"],
        "environment": doc["environment"],
        "enabled": doc["enabled"],
        "notes": doc.get("notes", ""),
        "createdAt": doc["createdAt"],
        "updatedAt": doc["updatedAt"],
    }


def build_appliance_document(payload: dict[str, Any], encrypted_fields: dict[str, str]) -> dict[str, Any]:
    now = utc_now()
    return {
        "name": payload["name"],
        "environment": payload["environment"],
        "encryptedHost": encrypted_fields["encryptedHost"],
        "encryptedUsername": encrypted_fields["encryptedUsername"],
        "encryptedPassword": encrypted_fields["encryptedPassword"],
        "enabled": payload.get("enabled", True),
        "notes": payload.get("notes", ""),
        "createdAt": now,
        "updatedAt": now,
    }


def parse_object_id(appliance_id: str) -> ObjectId:
    if not ObjectId.is_valid(appliance_id):
        raise ValueError("Invalid appliance ID")
    return ObjectId(appliance_id)
