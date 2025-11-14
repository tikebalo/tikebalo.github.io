from functools import lru_cache
from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    app_name: str = "Anycast Control Panel"
    api_v1_prefix: str = "/api"
    secret_key: str = Field("change-me", env="ANYCAST_SECRET_KEY")
    access_token_expire_minutes: int = Field(60 * 24, ge=1)
    database_url: str = Field("sqlite:///./anycast.db", env="ANYCAST_DATABASE_URL")
    cors_origins: list[str] = Field(default_factory=lambda: ["*"])

    class Config:
        case_sensitive = False
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()
