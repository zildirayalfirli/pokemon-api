# app/routes/router.py
import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.controllers.controller import process_ability_request
from app.db.database import get_db
from app.schemas.schema import AbilityRequest, AbilityResponse

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/health", tags=["health"])
async def health():
    return {"status": "healthy"}

@router.post(
    "/pokemon/ability",
    response_model=AbilityResponse,
    tags=["pokemon_api"],
    summary="Fetch, normalize, and persist pokemon ability data",
)

async def fetch_and_store_ability(payload: AbilityRequest, db: Session = Depends(get_db)) -> AbilityResponse:
    logger.info(
        "POST /pokemon/ability received for user_id=%d ability_id=%d",
        payload.user_id,
        payload.pokemon_ability_id,
    )
    return await process_ability_request(payload, db)