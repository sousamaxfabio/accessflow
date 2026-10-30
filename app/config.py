from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="ACCESSFLOW_",
        extra="ignore",
    )

    database_url: str = "sqlite:///./accessflow.db"
    log_level: str = "INFO"
    approval_api_key: str = "local-development-only"

    github_api_url: str = "https://api.github.com"
    github_api_version: str = "2026-03-10"
    github_token: SecretStr | None = None
    github_timeout_seconds: float = Field(default=5.0, gt=0, le=30)
    github_max_retries: int = Field(default=2, ge=0, le=5)
    github_retry_base_seconds: float = Field(
        default=0.25,
        ge=0,
        le=10,
    )
    github_max_pages: int = Field(default=5, ge=1, le=10)


@lru_cache
def get_settings() -> Settings:
    return Settings()
