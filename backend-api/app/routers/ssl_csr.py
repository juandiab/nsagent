from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.dependencies import get_db
from app.models.appliance import parse_object_id
from app.schemas.ssl_csr import GenerateSslRequest, GenerateSslResponse
from app.services.ssl_csr_service import generate_ssl_for_appliance

router = APIRouter(prefix="/ssl", tags=["ssl"])


@router.post("/generate-csr", response_model=GenerateSslResponse)
async def generate_csr(
    payload: GenerateSslRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> GenerateSslResponse:
    try:
        parse_object_id(payload.appliance_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appliance not found") from exc

    try:
        result = await generate_ssl_for_appliance(
            db,
            payload.appliance_id,
            payload.model_dump(exclude={"appliance_id"}),
        )
        return GenerateSslResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
