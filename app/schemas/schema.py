# app/schemas/schema.py
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator

class AbilityRequest(BaseModel):
    """Input payload matching the spec's example JSON."""
    raw_id: str = Field(..., description="Random string + int, 13 chars")
    user_id: int = Field(..., description="Random 7-digit integer")
    pokemon_ability_id: int = Field(..., description="PokeAPI ability ID")

    @field_validator("raw_id")
    @classmethod
    def validate_raw_id(cls, v: str) -> str:
        if len(v) != 13:
            raise ValueError("raw_id must be exactly 13 characters")
        return v

    @field_validator("user_id", mode="before")
    @classmethod
    def coerce_user_id(cls, v: Any) -> int:
        if isinstance(v, str):
            v = int(v)
        if not (1_000_000 <= v <= 9_999_999):
            raise ValueError("user_id must be a 7-digit integer")
        return v

    @field_validator("pokemon_ability_id", mode="before")
    @classmethod
    def coerce_ability_id(cls, v: Any) -> int:
        if isinstance(v, str):
            v = int(v)
        return v

class EffectEntry(BaseModel):
    effect: Optional[str] = None
    language: Optional[Dict[str, Any]] = None
    short_effect: Optional[str] = None

class AbilityResponse(BaseModel):
    raw_id: str
    user_id: int
    returned_entries: List[EffectEntry]
    pokemon_list: List[str]