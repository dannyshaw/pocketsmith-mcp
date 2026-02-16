"""Configuration management."""

from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    pocketsmith_api_key: SecretStr
    pocketsmith_base_url: str = "https://api.pocketsmith.com/v2"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
