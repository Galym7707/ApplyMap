from pydantic_settings import BaseSettings
from typing import List
from pathlib import Path


API_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://applymap:applymap@localhost:5432/applymap_db"
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    # AI Chancellor
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"
    GOOGLE_SEARCH_API_KEY: str = ""
    GOOGLE_SEARCH_ENGINE_ID: str = ""

    # S3 / Storage
    S3_BUCKET_NAME: str = ""
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = "us-east-1"

    class Config:
        env_file = (REPO_ROOT / ".env", API_DIR / ".env")
        extra = "ignore"


settings = Settings()
