"""Application configuration loaded from environment variables.

Uses pydantic-settings so values can come from a .env file (local dev) or from
real environment variables (Railway / cloud). Never hard-code secrets here.
"""
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- LLM ---
    openai_api_key: str = ""
    openai_model: str = "gpt-4.1-mini"

    # --- Auth ---
    # JWT signing secret. Override in production via env var.
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 480  # 8h working day

    # Shared password for the two challenge users.
    app_password: str = "TechnicalChallengePromtior"

    # --- Persistence ---
    database_url: str = "sqlite:///./booking.db"


settings = Settings()
