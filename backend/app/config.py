"""Application configuration via Pydantic Settings."""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Azure OpenAI
    azure_openai_api_key: str = ""
    azure_openai_endpoint: str = "https://neutriai-resource.openai.azure.com/openai/v1"
    azure_openai_deployment: str = "gpt-4.1-mini"
    azure_openai_api_version: str = "2024-12-01-preview"

    # Azure OpenAI Realtime (Voice)
    azure_openai_realtime_deployment: str = "gpt-realtime-2"

    # Database
    database_url: str = "sqlite+aiosqlite:///./data/crm.db"

    # App
    app_env: str = "development"
    app_debug: bool = True
    cors_origins: str = "http://localhost:3000"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
