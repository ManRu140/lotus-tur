"""
CSRF-защита — Middleware.

Алгоритм Double Submit Cookie:
  1. При установке кук генерируем случайный csrf_token.
  2. Сохраняем его в куке без HttpOnly (JS читает его).
  3. JS добавляет токен в заголовок X-CSRF-Token при каждом mutating-запросе.
  4. Middleware сравнивает значение в заголовке со значением в куке.
  5. Если не совпадают — 403 Forbidden.

Безопасные методы (GET, HEAD, OPTIONS) не проверяются.
Эндпоинты OAuth callback и /health исключены из проверки.

Почему Double Submit (а не Synchronizer Token)?
  Не требует хранения состояния на сервере — работает со stateless JWT.
"""
import secrets

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.cookies import COOKIE_CSRF_TOKEN

# ── Настройки ──────────────────────────────────────────────────────────────────

# Методы, требующие CSRF-проверки
_UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

# Пути, освобождённые от CSRF-проверки (OAuth redirect, healthcheck, login/register)
_CSRF_EXEMPT_PATHS: set[str] = {
    "/api/auth/login",
    "/api/auth/register",
    "/api/auth/google/callback",
    "/api/health",
    "/",
}


def generate_csrf_token() -> str:
    """Генерирует криптографически стойкий CSRF-токен (32 байта = 64 hex-символа)."""
    return secrets.token_hex(32)


def _is_exempt(path: str) -> bool:
    """Проверяет, освобождён ли путь от CSRF-валидации."""
    return path in _CSRF_EXEMPT_PATHS


class CSRFMiddleware(BaseHTTPMiddleware):
    """
    Проверяет наличие и корректность X-CSRF-Token для mutating-запросов.
    Использует алгоритм Double Submit Cookie.
    """

    async def dispatch(self, request: Request, call_next):
        # Безопасные методы и исключённые пути пропускаем
        if request.method not in _UNSAFE_METHODS or _is_exempt(request.url.path):
            return await call_next(request)

        # Токен из куки (установлен сервером)
        cookie_token = request.cookies.get(COOKIE_CSRF_TOKEN)
        # Токен из заголовка (вставлен JS)
        header_token = request.headers.get("X-CSRF-Token")

        if not cookie_token or not header_token:
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "CSRF-токен отсутствует"},
            )

        # secrets.compare_digest — защита от timing-атак
        if not secrets.compare_digest(cookie_token, header_token):
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "Недействительный CSRF-токен"},
            )

        return await call_next(request)
