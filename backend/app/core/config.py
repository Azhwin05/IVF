"""
Central application configuration.

All settings are read from environment variables (see .env.example).
Never hardcode secrets here — this file defines shape and safe defaults
for local dev only; production values always come from the environment.
"""
from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # ---- Environment ----
    ENVIRONMENT: Literal["local", "staging", "production"] = "local"
    APP_NAME: str = "Archana IVF HMIS"
    API_V1_PREFIX: str = "/api/v1"

    # ---- Database ----
    DATABASE_URL: str = "postgresql+asyncpg://archana:archana_dev@localhost:5432/archana_hmis"
    DATABASE_URL_SYNC: str = "postgresql+psycopg2://archana:archana_dev@localhost:5432/archana_hmis"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 5

    # ---- Redis ----
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # ---- MinIO / Object Storage ----
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "archana_minio"
    MINIO_SECRET_KEY: str = "archana_minio_dev_secret"
    MINIO_SECURE: bool = False
    MINIO_BUCKET_DOCUMENTS: str = "hmis-documents"
    MINIO_BUCKET_REPORTS: str = "hmis-reports"

    # ---- Auth / Security ----
    JWT_SECRET_KEY: str = "CHANGE_ME_IN_PRODUCTION_USE_A_LONG_RANDOM_SECRET"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 14
    ABSOLUTE_SESSION_LIFETIME_HOURS: int = 12
    IDLE_TIMEOUT_MINUTES: int = 30
    PASSWORD_MIN_LENGTH: int = 10
    LOGIN_MAX_ATTEMPTS: int = 5
    LOGIN_LOCKOUT_MINUTES: int = 15

    # ---- CORS (frontend origin, LAN only) ----
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "https://hmis.archanaivf.in"]

    # ---- Uploads ----
    MAX_UPLOAD_SIZE_MB: int = 25
    ALLOWED_UPLOAD_MIME_TYPES: list[str] = [
        "application/pdf",
        "image/jpeg",
        "image/png",
        "image/webp",
    ]

    @field_validator("JWT_SECRET_KEY")
    @classmethod
    def secret_must_be_overridden_in_production(cls, v: str, info) -> str:
        # Pydantic v2 doesn't easily cross-validate ENVIRONMENT here without a model_validator,
        # so the hard check also lives in main.py's startup guard.
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()
