"""Appliance inventory helpers."""

from datetime import datetime, timezone
from typing import Any

from bson import ObjectId

from app.services.vendor_registry import is_vendor_copilot_supported


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


DEFAULT_VENDOR = "netscaler"


def normalize_vendor(vendor: str | None) -> str:
    return vendor or DEFAULT_VENDOR


def is_netscaler_appliance(doc: dict[str, Any]) -> bool:
    return normalize_vendor(doc.get("vendor")) == DEFAULT_VENDOR


def is_copilot_eligible_appliance(doc: dict[str, Any]) -> bool:
    return is_vendor_copilot_supported(normalize_vendor(doc.get("vendor")))


def serialize_appliance(doc: dict[str, Any]) -> dict[str, Any]:
    vendor = normalize_vendor(doc.get("vendor"))
    return {
        "id": str(doc["_id"]),
        "name": doc["name"],
        "environment": doc["environment"],
        "enabled": doc["enabled"],
        "notes": doc.get("notes", ""),
        "vendor": vendor,
        "copilotEligible": is_copilot_eligible_appliance(doc),
        "createdAt": doc["createdAt"],
        "updatedAt": doc["updatedAt"],
    }


def build_appliance_document(payload: dict[str, Any], encrypted_fields: dict[str, str]) -> dict[str, Any]:
    now = utc_now()
    vendor = normalize_vendor(payload.get("vendor"))
    enabled = payload.get("enabled", True)
    if not is_vendor_copilot_supported(vendor) and vendor != DEFAULT_VENDOR:
        enabled = False
    return {
        "name": payload["name"],
        "environment": payload["environment"],
        "vendor": vendor,
        "encryptedHost": encrypted_fields["encryptedHost"],
        "encryptedUsername": encrypted_fields["encryptedUsername"],
        "encryptedPassword": encrypted_fields["encryptedPassword"],
        "enabled": enabled,
        "notes": payload.get("notes", ""),
        "createdAt": now,
        "updatedAt": now,
    }


def parse_object_id(appliance_id: str) -> ObjectId:
    if not ObjectId.is_valid(appliance_id):
        raise ValueError("Invalid appliance ID")
    return ObjectId(appliance_id)
