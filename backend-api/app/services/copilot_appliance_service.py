from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.appliance import is_netscaler_appliance, serialize_appliance
from app.services.copilot_service import resolve_appliance_credentials
from app.services.mcp_client import test_appliance_via_mcp

NEXTGEN_LOGIN_PATH = "/mgmt/api/nextgen/v1/login"


async def list_copilot_appliances(db: AsyncIOMotorDatabase) -> list[dict]:
    query = {
        "$or": [{"vendor": "netscaler"}, {"vendor": {"$exists": False}}],
    }
    appliances = await db.appliances.find({**query, "enabled": True}).sort("name", 1).to_list(length=None)
    if not appliances:
        appliances = await db.appliances.find(query).sort("name", 1).to_list(length=None)
    return [serialize_appliance(doc) for doc in appliances if is_netscaler_appliance(doc)]


async def connect_appliance(db: AsyncIOMotorDatabase, appliance_name: str) -> dict:
    appliance = await db.appliances.find_one({"name": appliance_name})
    if appliance is None:
        raise ValueError(f"Appliance '{appliance_name}' not found in inventory")

    if not is_netscaler_appliance(appliance):
        raise ValueError(
            f"Appliance '{appliance_name}' is not a NetScaler. JPilot chat supports NetScaler appliances only."
        )

    if not appliance.get("enabled", True):
        raise ValueError(f"Appliance '{appliance_name}' is disabled in inventory")

    host, username, password = await resolve_appliance_credentials(db, appliance_name)
    result = await test_appliance_via_mcp(host, username, password, db=db)

    if not result.get("success"):
        raise ValueError(result.get("message") or "Next-Gen API login failed")

    return {
        "success": True,
        "applianceName": appliance_name,
        "environment": appliance.get("environment", ""),
        "message": result.get("message", "Connected"),
        "api": "NetScaler Next-Gen API",
        "apiPath": "/mgmt/api/nextgen/v1",
        "loginEndpoint": NEXTGEN_LOGIN_PATH,
        "authenticatedUser": username,
    }
