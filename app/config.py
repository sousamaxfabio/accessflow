from functools import lru_cache

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


@lru_cache
def get_settings() -> Settings:
    return Settings()
