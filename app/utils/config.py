# app/utils/config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Database
    DB_USER: str = os.getenv("DB_USER")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD")
    DB_HOST: str = os.getenv("DB_HOST")
    DB_PORT: int = int(os.getenv("DB_PORT", "3306"))
    DB_NAME: str = os.getenv("DB_NAME")

    # External API
    POKEAPI_BASE_URL: str = os.getenv("POKEAPI_BASE_URL")
    POKEAPI_TIMEOUT: float = float(os.getenv("POKEAPI_TIMEOUT", "10.0"))

    # Server
    HOST: str = os.getenv("HOST")
    PORT: int = int(os.getenv("PORT"))
    WORKERS: int = int(os.getenv("WORKERS"))

    @property
    def database_url(self) -> str:
        return (
            f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?charset=utf8mb4"
        )

settings = Settings()
 