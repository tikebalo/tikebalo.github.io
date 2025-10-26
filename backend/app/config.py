from functools import lru_cache
from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    app_name: str = "Anycast Control Panel"
    api_v1_prefix: str = "/api"
    secret_key: str = Field(..., env="ANYCAST_SECRET_KEY")
    access_token_expire_minutes: int = 30
    refresh_token_expire_minutes: int = 60 * 24 * 7
    postgres_dsn: str = Field(..., env="ANYCAST_DATABASE_URL")
    redis_url: str = Field(..., env="ANYCAST_REDIS_URL")
    smtp_host: str | None = Field(default=None, env="ANYCAST_SMTP_HOST")
    smtp_user: str | None = Field(default=None, env="ANYCAST_SMTP_USER")
    smtp_password: str | None = Field(default=None, env="ANYCAST_SMTP_PASSWORD")
    smtp_from: str | None = Field(default=None, env="ANYCAST_SMTP_FROM")

    class Config:
        case_sensitive = False
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()
