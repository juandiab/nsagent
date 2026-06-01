from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ReturnDocument

from app.dependencies import get_db
from app.models.appliance import (
    build_appliance_document,
    parse_object_id,
    serialize_appliance,
    utc_now,
)
from app.schemas.appliance import ApplianceCreate, ApplianceResponse, ApplianceUpdate
from app.services.encryption_service import encrypt_value

router = APIRouter(prefix="/appliances", tags=["appliances"])


def _should_update_credential(value: str | None) -> bool:
    return value is not None and value != ""


@router.get("", response_model=list[ApplianceResponse])
async def list_appliances(db: AsyncIOMotorDatabase = Depends(get_db)) -> list[dict]:
    appliances = await db.appliances.find().sort("name", 1).to_list(length=None)
    return [serialize_appliance(doc) for doc in appliances]


@router.get("/{appliance_id}", response_model=ApplianceResponse)
async def get_appliance(
    appliance_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> dict:
    try:
        object_id = parse_object_id(appliance_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appliance not found") from exc

    appliance = await db.appliances.find_one({"_id": object_id})
    if appliance is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appliance not found")

    return serialize_appliance(appliance)


@router.post("", response_model=ApplianceResponse, status_code=status.HTTP_201_CREATED)
async def create_appliance(
    payload: ApplianceCreate,
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> dict:
    encrypted_fields = {
        "encryptedHost": encrypt_value(payload.host),
        "encryptedUsername": encrypt_value(payload.username),
        "encryptedPassword": encrypt_value(payload.password),
    }
    document = build_appliance_document(payload.model_dump(), encrypted_fields)
    result = await db.appliances.insert_one(document)
    created = await db.appliances.find_one({"_id": result.inserted_id})
    return serialize_appliance(created)


@router.put("/{appliance_id}", response_model=ApplianceResponse)
async def update_appliance(
    appliance_id: str,
    payload: ApplianceUpdate,
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> dict:
    try:
        object_id = parse_object_id(appliance_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appliance not found") from exc

    existing = await db.appliances.find_one({"_id": object_id})
    if existing is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appliance not found")

    update_data: dict = {"updatedAt": utc_now()}

    if payload.name is not None:
        update_data["name"] = payload.name
    if payload.environment is not None:
        update_data["environment"] = payload.environment
    if payload.notes is not None:
        update_data["notes"] = payload.notes
    if payload.enabled is not None:
        update_data["enabled"] = payload.enabled

    if _should_update_credential(payload.host):
        update_data["encryptedHost"] = encrypt_value(payload.host)
    if _should_update_credential(payload.username):
        update_data["encryptedUsername"] = encrypt_value(payload.username)
    if _should_update_credential(payload.password):
        update_data["encryptedPassword"] = encrypt_value(payload.password)

    await db.appliances.update_one({"_id": object_id}, {"$set": update_data})
    updated = await db.appliances.find_one({"_id": object_id})
    return serialize_appliance(updated)


@router.delete("/{appliance_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_appliance(
    appliance_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> None:
    try:
        object_id = parse_object_id(appliance_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appliance not found") from exc

    result = await db.appliances.delete_one({"_id": object_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appliance not found")


@router.patch("/{appliance_id}/enable", response_model=ApplianceResponse)
async def enable_appliance(
    appliance_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> dict:
    return await _set_enabled(appliance_id, True, db)


@router.patch("/{appliance_id}/disable", response_model=ApplianceResponse)
async def disable_appliance(
    appliance_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> dict:
    return await _set_enabled(appliance_id, False, db)


async def _set_enabled(
    appliance_id: str,
    enabled: bool,
    db: AsyncIOMotorDatabase,
) -> dict:
    try:
        object_id = parse_object_id(appliance_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appliance not found") from exc

    result = await db.appliances.find_one_and_update(
        {"_id": object_id},
        {"$set": {"enabled": enabled, "updatedAt": utc_now()}},
        return_document=ReturnDocument.AFTER,
    )
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appliance not found")

    return serialize_appliance(result)
