from functools import lru_cache
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    DATABASE_URL: str = "sqlite+aiosqlite:///./lotos_tour.db"


    SECRET_KEY: str = Field(
        default="CHANGE_ME_IN_PRODUCTION_use_openssl_rand_hex_32",
        min_length=32,
    )
    ALGORITHM: Literal["HS256", "HS512", "RS256"] = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60 * 24, gt=0)


    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""


    VK_CLIENT_ID: str = ""
    VK_CLIENT_SECRET: str = ""
    VK_REDIRECT_URI: str = ""


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


    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW_SECONDS: int = 60


    ENV: Literal["development", "production", "testing"] = "development"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    @model_validator(mode="after")
    def _enforce_production_secret(self) -> "Settings":
        insecure = "CHANGE_ME_IN_PRODUCTION"
        if self.ENV == "production" and insecure in self.SECRET_KEY:
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
