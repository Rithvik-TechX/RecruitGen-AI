"""
Application Settings — powered by pydantic-settings.

All environment variables are declared here and validated at startup.
The ``get_settings`` helper uses ``@lru_cache`` so the settings object
is created only once per process.
"""

from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central settings read from environment / .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ─────────────────────────────────────────
    APP_NAME: str = "RecruitmentGen AI"
    APP_ENV: str = "development"  # development | staging | production
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    SECRET_KEY: str = "change-me-in-production"

    # ── PostgreSQL ──────────────────────────────────────────
    POSTGRES_USER: str = "recruitgen"
    POSTGRES_PASSWORD: str = "recruitgen_secret"
    POSTGRES_DB: str = "recruitgen_db"
    POSTGRES_HOST: str = "db"
    POSTGRES_PORT: int = 5432

    # ── API ─────────────────────────────────────────────────
    API_V1_PREFIX: str = "/api/v1"
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8000"]

    # ── JWT / Auth ──────────────────────────────────────────
    JWT_SECRET_KEY: str = "change-me-in-production-use-openssl-rand-hex-64"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── Gemini AI ──────────────────────────────────────────
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"

    # ── Embedding Model ────────────────────────────────────
    EMBEDDING_MODEL: str = "BAAI/bge-small-en-v1.5"

    # ── ChromaDB ───────────────────────────────────────────
    CHROMA_HOST: str = "chromadb"
    CHROMA_PORT: int = 8000
    CHROMA_COLLECTION_CANDIDATES: str = "candidates"
    CHROMA_COLLECTION_JOBS: str = "jobs"

    # ── Derived ─────────────────────────────────────────────
    @property
    def ASYNC_DATABASE_URL(self) -> str:
        """Construct the async database URL from individual components."""
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def SYNC_DATABASE_URL(self) -> str:
        """Construct the sync database URL (used by Alembic)."""
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> list[str]:
        """Accept both JSON string and list."""
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return [origin.strip() for origin in v.split(",")]
        return v


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance (created once per process)."""
    return Settings()
