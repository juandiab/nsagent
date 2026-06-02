from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.appliance import parse_object_id
from app.services.encryption_service import decrypt_value
from app.services.mcp_client import generate_csr_via_mcp, generate_self_signed_via_mcp


async def _credentials_from_appliance(db: AsyncIOMotorDatabase, appliance_id: str) -> tuple[str, str, str]:
    object_id = parse_object_id(appliance_id)
    appliance = await db.appliances.find_one({"_id": object_id})
    if appliance is None:
        raise ValueError("Appliance not found")
    if not appliance.get("enabled", True):
        raise ValueError("Appliance is disabled")

    return (
        decrypt_value(appliance["encryptedHost"]),
        decrypt_value(appliance["encryptedUsername"]),
        decrypt_value(appliance["encryptedPassword"]),
    )


def _map_ssl_response(data: dict, generation_mode: str) -> dict:
    return {
        "success": True,
        "message": data.get("message", "SSL material generated"),
        "generation_mode": generation_mode,
        "csr": data.get("csr", ""),
        "certificate": data.get("certificate", ""),
        "key_path": data.get("keyPath", ""),
        "csr_path": data.get("csrPath", ""),
        "cert_path": data.get("certPath", ""),
        "req_path": data.get("reqPath", ""),
        "cert_key_name": data.get("certKeyName", ""),
        "key_name": data.get("keyName", ""),
        "common_name": data.get("commonName", ""),
        "cert_type": data.get("certType", ""),
        "key_type": data.get("keyType", ""),
        "validity_days": data.get("validityDays"),
    }


async def generate_ssl_for_appliance(
    db: AsyncIOMotorDatabase,
    appliance_id: str,
    payload: dict,
) -> dict:
    host, username, password = await _credentials_from_appliance(db, appliance_id)
    generation_mode = payload.get("generation_mode", "csr")
    request_payload = {key: value for key, value in payload.items() if key != "generation_mode"}

    if generation_mode == "self_signed":
        result = await generate_self_signed_via_mcp(host, username, password, request_payload, db=db)
        failure_message = "Self-signed certificate generation failed"
    else:
        result = await generate_csr_via_mcp(host, username, password, request_payload, db=db)
        failure_message = "CSR generation failed"

    if not result.get("success"):
        raise ValueError(result.get("message") or failure_message)

    return _map_ssl_response(result.get("data") or {}, generation_mode)


async def generate_csr_for_appliance(
    db: AsyncIOMotorDatabase,
    appliance_id: str,
    payload: dict,
) -> dict:
    payload = {**payload, "generation_mode": "csr"}
    return await generate_ssl_for_appliance(db, appliance_id, payload)
