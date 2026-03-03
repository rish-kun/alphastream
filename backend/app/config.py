from __future__ import annotations

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="../.env",
        env_file_encoding="utf-8",
        extra="ignore",
        enable_decoding=False,
    )

    # Database
    DATABASE_URL: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/alphastream"
    )

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # OAuth - Google
    GOOGLE_CLIENT_ID: str | None = None
    GOOGLE_CLIENT_SECRET: str | None = None

    # OAuth - GitHub
    GITHUB_CLIENT_ID: str | None = None
    GITHUB_CLIENT_SECRET: str | None = None

    # AI API Keys
    GEMINI_API_KEYS: list[str] = []
    OPENROUTER_API_KEYS: list[str] = []

    @field_validator("GEMINI_API_KEYS", "OPENROUTER_API_KEYS", mode="before")
    @classmethod
    def parse_api_keys(cls, v):
        if isinstance(v, str):
            if not v.strip():
                return []
            import json

            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return [k.strip() for k in v.split(",") if k.strip()]
        return v

    # Extensive Research
    FIRECRAWL_API_KEY: str = ""
    BROWSEAI_API_KEY: str = ""
    THUNDERBIT_API_KEY: str = ""

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]


settings = Settings()
