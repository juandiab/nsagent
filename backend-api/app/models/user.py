from datetime import datetime, timezone
from typing import Any

from bson import ObjectId


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def serialize_user(doc: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(doc["_id"]),
        "username": doc["username"],
        "displayName": doc.get("displayName", doc["username"]),
        "createdAt": doc["createdAt"],
    }
