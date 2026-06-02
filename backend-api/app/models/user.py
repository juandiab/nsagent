from typing import Any


def serialize_user(doc: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(doc["_id"]),
        "username": doc["username"],
        "displayName": doc.get("displayName", doc["username"]),
        "email": doc.get("email"),
        "role": doc.get("role", "user"),
        "createdAt": doc["createdAt"],
    }
