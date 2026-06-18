from functools import lru_cache
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):

    # * Railway sets DATABASE_URL automatically (postgresql+asyncpg)
    DATABASE_URL: str = "sqlite+aiosqlite:///./lotos_tour.db"

    SECRET_KEY: str = Field(
        default="CHANGE_ME_IN_PRODUCTION_use_openssl_rand_hex_32",
        min_length=32,
    )
    ALGORITHM: Literal["HS256", "HS512", "RS256"] = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60 * 24 * 7, gt=0)

    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""

    VK_CLIENT_ID: str = ""
    VK_CLIENT_SECRET: str = ""
    VK_REDIRECT_URI: str = ""

    # First-run admin bootstrap. Set these as env vars on Railway before
    # first deploy. Seed creates the account on first startup if it doesn't
    # exist yet; changing the vars after that has no effect (use the admin
    # panel's "Reset password" to change it).
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = ""  # empty = skip seeding (safe default)

    FRONTEND_URL: str = "https://agile-intuition-production.up.railway.app"

    CORS_ORIGINS: list[str] = [
        "https://agile-intuition-production.up.railway.app",
        "https://lotus-tur-production-23c6.up.railway.app",
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    ALLOWED_HOSTS: list[str] = [
        "lotus-tur-production-23c6.up.railway.app",
    ]

    ENV: Literal["development", "production", "testing"] = "development"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    @model_validator(mode="after")
    def _enforce_production_secret(self) -> "Settings":
        if self.ENV == "production" and "CHANGE_ME_IN_PRODUCTION" in self.SECRET_KEY:
            raise ValueError(
                "SECRET_KEY не изменён — запуск в production запрещён. "
                "Сгенерируйте ключ: openssl rand -hex 32"
            )
        if self.ENV == "development" and "null" not in self.CORS_ORIGINS:
            self.CORS_ORIGINS = list(self.CORS_ORIGINS) + ["null"]
        return self

@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()

settings: Settings = get_settings()
