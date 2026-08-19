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
    # No defaults: if these are absent from .env / environment the app fails at startup,
    # which is the correct behaviour — secrets must be explicitly provided.
    jwt_secret: str
    app_password: str

    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 480  # 8h working day

    # --- Persistence ---
    database_url: str = "sqlite:///./booking.db"


settings = Settings()
