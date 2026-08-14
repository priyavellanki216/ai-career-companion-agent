"""Application configuration with a safe deterministic demo default."""
from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Career Companion"
    database_url: str = "sqlite:///./career_companion.db"
    llm_api_key: str | None = None
    llm_api_url: str | None = None
    llm_model: str = "gpt-4o-mini"
    llm_provider: str = "fallback"
    max_upload_mb: int = 5
    cors_origins: str = "http://localhost:8501,http://localhost:3000"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def upload_limit_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024

    @property
    def project_root(self) -> Path:
        return Path(__file__).resolve().parents[1]


@lru_cache
def get_settings() -> Settings:
    return Settings()
