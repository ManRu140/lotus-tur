"""
Security Headers Middleware — защитные HTTP-заголовки.

Реализует рекомендации OWASP Secure Headers Project:
  https://owasp.org/www-project-secure-headers/

Добавляемые заголовки:
  X-Content-Type-Options      — запрет MIME-sniffing (защита от XSS через тип контента)
  X-Frame-Options             — защита от Clickjacking
  X-XSS-Protection            — устаревший, но полезен для IE/Edge (отключаем встроенный)
  Referrer-Policy             — ограничение утечки URL в Referer
  Permissions-Policy          — отключаем ненужные браузерные API
  Content-Security-Policy     — главная защита от XSS
  Strict-Transport-Security   — принудительный HTTPS (только в production)
  Cache-Control               — отключаем кэш для API-ответов
"""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings

_IS_PROD = settings.ENV == "production"


# ── Значения заголовков ────────────────────────────────────────────────────────

# CSP для REST API — запрещаем всё (браузер не должен рендерить API-ответы как HTML)
_CSP_API = (
    "default-src 'none'; "
    "frame-ancestors 'none';"
)

# Permissions-Policy — отзываем ненужные браузерные возможности
_PERMISSIONS_POLICY = (
    "camera=(), "
    "microphone=(), "
    "geolocation=(), "
    "payment=(), "
    "usb=(), "
    "interest-cohort=()"   # FLoC opt-out
)

# HSTS: 1 год, включая поддомены
_HSTS = "max-age=31536000; includeSubDomains; preload"


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Добавляет защитные заголовки к каждому HTTP-ответу.
    Не блокирует запросы — только обогащает ответы.
    """

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # ── Базовые заголовки (всегда) ────────────────────────────────────────

        # Запрет MIME-type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Защита от Clickjacking (через iframe)
        response.headers["X-Frame-Options"] = "DENY"

        # Устаревший XSS-фильтр — явно отключаем встроенный фильтр браузера,
        # CSP справляется лучше
        response.headers["X-XSS-Protection"] = "0"

        # Не передаём Referer при переходе на другой домен
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Отзываем ненужные браузерные API
        response.headers["Permissions-Policy"] = _PERMISSIONS_POLICY

        # CSP для API (блокируем всё — ответы не рендерятся браузером как HTML)
        response.headers["Content-Security-Policy"] = _CSP_API

        # Отключаем кэш для всех API-ответов
        # (чувствительные данные не должны кэшироваться в прокси/браузере)
        if request.url.path.startswith("/api"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
            response.headers["Pragma"] = "no-cache"

        # ── Production-only ───────────────────────────────────────────────────

        if _IS_PROD:
            # HSTS — только по HTTPS, с preload
            response.headers["Strict-Transport-Security"] = _HSTS

        if "server" in response.headers:
            del response.headers["server"]
        if "x-powered-by" in response.headers:
            del response.headers["x-powered-by"]

        return response
