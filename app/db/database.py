# app/db/database.py
import logging
import time
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from sqlalchemy.exc import OperationalError
from app.utils.config import settings

logger = logging.getLogger(__name__)

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False,
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()

def init_db(max_retries: int = 10, retry_delay: int = 3) -> None:
    """Create tables. Retries because MySQL container may not be ready at startup."""
    from app.models.model import PokemonAbility

    for attempt in range(1, max_retries + 1):
        try:
            Base.metadata.create_all(bind=engine)
            logger.info("Tables ready (attempt %d)", attempt)
            return
        except OperationalError as e:
            logger.warning(
                "MySQL not ready (attempt %d/%d): %s", attempt, max_retries, e
            )
            if attempt == max_retries:
                logger.error("Exceeded max retries — giving up on DB connection")
                raise
            time.sleep(retry_delay)

@contextmanager
def get_db_session() -> Session:
    """Provide a transactional session scope."""
    session = SessionLocal()
    try:
        yield session
    except Exception:
        logger.exception("DB session error — rolling back")
        session.rollback()
        raise
    finally:
        session.close()

def get_db():
    """FastAPI dependency — yields a DB session per request."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()