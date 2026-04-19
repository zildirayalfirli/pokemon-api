# app/main.py
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.utils.logger import setup_logging
from app.utils.config import settings

setup_logging(level="INFO")
logger = logging.getLogger(__name__)

from app.db.database import init_db
from app.routes.router import router
 
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application startup — initializing database")
    init_db()
    logger.info("Startup complete — ready to accept requests")
    yield
    logger.info("Application shutdown")
 
app = FastAPI(
    description="Fetch, normalize, and store Pokemon ability data from PokeAPI",
    lifespan=lifespan,
)

app.include_router(router)
 
if __name__ == "__main__":
    import uvicorn
 
    logger.info("Starting FastAPI server via uvicorn on port 4400")
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        workers=settings.WORKERS,
        reload=False,
    )