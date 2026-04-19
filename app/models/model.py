# app/models/model.py
from sqlalchemy import Column, Integer, String, Text, JSON, BigInteger, DateTime
from sqlalchemy.sql import func
from app.db.database import Base

class PokemonAbility(Base):
    __tablename__ = "pokemon_abilities"

    id = Column(Integer, primary_key=True, autoincrement=True)
    raw_id = Column(String(13), nullable=False, index=True)
    user_id = Column(BigInteger, nullable=False, index=True)
    pokemon_ability_id = Column(Integer, nullable=False, index=True)
    effect = Column(Text, nullable=True)
    language = Column(Text, nullable=True)
    short_effect = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self) -> str:
        return (
            f"<PokemonAbility id={self.id} raw_id={self.raw_id} "
            f"ability={self.pokemon_ability_id}>"
        )