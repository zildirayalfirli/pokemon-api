# app/controllers/controller.py
import json
import logging
import httpx
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models.model import PokemonAbility
from app.schemas.schema import AbilityRequest, AbilityResponse, EffectEntry
from app.utils.config import settings

logger = logging.getLogger(__name__)

def _serialize_language(lang: dict | None) -> str | None:
    if not lang:
        return None
    ordered = {"name": lang.get("name"), "url": lang.get("url")}
    return json.dumps(ordered, ensure_ascii=False)

async def fetch_ability_from_pokeapi(ability_id: int) -> dict:
    """Call PokeAPI and return the raw JSON. Raises HTTPException on failure."""
    url = f"{settings.POKEAPI_BASE_URL}/ability/{ability_id}"
    logger.info("Fetching ability from PokeAPI: %s", url)

    async with httpx.AsyncClient(timeout=settings.POKEAPI_TIMEOUT) as client:
        try:
            response = await client.get(url)
            response.raise_for_status()
            logger.info(
                "PokeAPI responded %d for ability_id=%d",
                response.status_code,
                ability_id,
            )
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.warning(
                "PokeAPI HTTP error for ability_id=%d: status=%d",
                ability_id,
                e.response.status_code,
            )
            if e.response.status_code == 404:
                raise HTTPException(
                    status_code=404,
                    detail=f"Pokemon ability id {ability_id} not found",
                )
            raise HTTPException(
                status_code=502,
                detail=f"PokeAPI error: {e.response.status_code}",
            )
        except httpx.RequestError as e:
            logger.error("Failed to reach PokeAPI: %s", e)
            raise HTTPException(
                status_code=502, detail=f"Failed to reach PokeAPI: {str(e)}"
            )

def persist_effect_entries(db: Session, payload: AbilityRequest, effect_entries: list[dict]) -> list[dict]:
    """Normalize and insert one row per effect_entry. Returns the stored entries."""
    logger.info(
        "Persisting %d effect entries for raw_id=%s user_id=%d ability_id=%d",
        len(effect_entries),
        payload.raw_id,
        payload.user_id,
        payload.pokemon_ability_id,
    )

    stored = []
    try:
        for entry in effect_entries:
            language_dict = entry.get("language")
            language_str = _serialize_language(language_dict)

            record = PokemonAbility(
                raw_id=payload.raw_id,
                user_id=payload.user_id,
                pokemon_ability_id=payload.pokemon_ability_id,
                effect=entry.get("effect"),
                language=language_str,
                short_effect=entry.get("short_effect"),
            )
            db.add(record)

            stored.append(
                {
                    "effect": entry.get("effect"),
                    "language": (
                        {"name": language_dict.get("name"), "url": language_dict.get("url")}
                        if language_dict
                        else None
                    ),
                    "short_effect": entry.get("short_effect"),
                }
            )
        db.commit()
        logger.info("Committed %d rows to pokemon_ability", len(stored))
    except Exception:
        db.rollback()
        logger.exception("Failed to persist effect entries — rolled back")
        raise HTTPException(status_code=500, detail="Database persistence error")

    return stored

def extract_pokemon_names(pokemon_field: list[dict]) -> list[str]:
    """Extract pokemon names from PokeAPI's nested 'pokemon' field."""
    names = [p["pokemon"]["name"] for p in pokemon_field if p.get("pokemon")]
    logger.debug("Extracted %d pokemon names", len(names))
    return names

async def process_ability_request(payload: AbilityRequest, db: Session) -> AbilityResponse:
    """Main controller — orchestrates the full request lifecycle."""
    logger.info(
        "Processing ability request: raw_id=%s user_id=%d ability_id=%d",
        payload.raw_id,
        payload.user_id,
        payload.pokemon_ability_id,
    )

    data = await fetch_ability_from_pokeapi(payload.pokemon_ability_id)

    effect_entries = data.get("effect_entries", [])
    if not effect_entries:
        logger.warning(
            "No effect_entries in PokeAPI response for ability_id=%d",
            payload.pokemon_ability_id,
        )
        raise HTTPException(
            status_code=404,
            detail=f"No effect_entries found for ability id {payload.pokemon_ability_id}",
        )

    stored_entries = persist_effect_entries(db, payload, effect_entries)
    pokemon_list = extract_pokemon_names(data.get("pokemon", []))

    logger.info(
        "Request complete: returned %d entries and %d pokemon names",
        len(stored_entries),
        len(pokemon_list),
    )

    return AbilityResponse(
        raw_id=payload.raw_id,
        user_id=payload.user_id,
        returned_entries=[EffectEntry(**e) for e in stored_entries],
        pokemon_list=pokemon_list,
    )