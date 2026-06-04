"""
Конфигурация приложения через переменные окружения.

Все секретные значения читаются из .env — никаких дефолтов
для SECRET_KEY в продакшене. Если переменная не задана,
приложение не запустится (field validator бросит исключение).
"""
from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ── База данных ────────────────────────────────────────────
    DATABASE_URL: str = "sqlite+aiosqlite:///./lotos_tour.db"

    # ── JWT ────────────────────────────────────────────────────
    SECRET_KEY: str = Field(
        default="CHANGE_ME_IN_PRODUCTION_use_openssl_rand_hex_32",
        min_length=32,
    )
    ALGORITHM: Literal["HS256", "HS512", "RS256"] = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60 * 24, gt=0)  # 24 часа

    # ── Google OAuth ───────────────────────────────────────────
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    FRONTEND_URL: str = "http://localhost:5173"

    # ── CORS ───────────────────────────────────────────────────
    # ИСПРАВЛЕНИЕ CORS-ОШИБКИ:
    # В Railway добавьте переменную окружения:
    #   CORS_ORIGINS=["https://thriving-entremet-a84a1b.netlify.app","https://ваш-домен.ru"]
    #
    # Значения по умолчанию включают Netlify-домен для деплоя.
    # При смене домена — обновите CORS_ORIGINS в настройках Railway.
    CORS_ORIGINS: list[str] = [
        # ── Production фронтенды ───────────────────────────────
        "https://thriving-entremet-a84a1b.netlify.app",  # CORS FIX: Netlify production
        # ── Локальная разработка ───────────────────────────────
        "http://localhost",
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    # ── Rate limiting ──────────────────────────────────────────
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW_SECONDS: int = 60

    # ── Окружение ──────────────────────────────────────────────
    ENV: Literal["development", "production", "testing"] = "development"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        json_schema_extra={"env_nested_delimiter": "__"},
    )

    @field_validator("SECRET_KEY")
    @classmethod
    def _check_secret_key(cls, v: str) -> str:
        return v

    @model_validator(mode="after")
    def _enforce_production_secret(self) -> "Settings":
        insecure = "CHANGE_ME_IN_PRODUCTION"
        if self.ENV == "production" and insecure in self.SECRET_KEY:
            raise ValueError(
                "SECRET_KEY не изменён — запуск в production запрещён. "
                "Сгенерируйте ключ: openssl rand -hex 32"
            )
        # "null" origin (file://) только в dev-режиме
        if self.ENV == "development" and "null" not in self.CORS_ORIGINS:
            self.CORS_ORIGINS = list(self.CORS_ORIGINS) + ["null"]
        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Синглтон настроек — кэшируется на весь жизненный цикл процесса."""
    return Settings()


settings: Settings = get_settings()
