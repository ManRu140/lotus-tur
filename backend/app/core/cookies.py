"""
Безопасная работа с Cookie.

Принципы:
  - HttpOnly=True  — JS не может прочитать куки (защита от XSS)
  - Secure=True    — только HTTPS (в production)
  - SameSite=Lax   — защита от CSRF при GET, Strict слишком агрессивен для OAuth
  - Path=/api      — куки не отправляются на статику
  - CSRF-токен хранится в отдельной куке без HttpOnly, чтобы JS мог читать
"""
from fastapi import Request, Response

from app.core.config import settings

# ── Константы ──────────────────────────────────────────────────────────────────

COOKIE_ACCESS_TOKEN = "access_token"
COOKIE_CSRF_TOKEN   = "csrf_token"

_IS_PROD     = settings.ENV == "production"
_SAMESITE    = "lax"          # lax — баланс между удобством и безопасностью
_COOKIE_PATH = "/api"         # отдаём куки только на /api/*
_MAX_AGE     = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60  # в секундах


# ── Установка кук ──────────────────────────────────────────────────────────────

def set_auth_cookies(response: Response, access_token: str, csrf_token: str) -> None:
    """
    Устанавливает две куки:
      1. access_token  — HttpOnly, Secure (в prod), SameSite=Lax
      2. csrf_token    — НЕ HttpOnly (JS читает и вставляет в заголовок X-CSRF-Token)
    """
    # JWT — недоступен JS
    response.set_cookie(
        key=COOKIE_ACCESS_TOKEN,
        value=access_token,
        max_age=_MAX_AGE,
        path=_COOKIE_PATH,
        httponly=True,
        secure=_IS_PROD,
        samesite=_SAMESITE,
    )

    # CSRF-токен — читается JS, вставляется в X-CSRF-Token
    response.set_cookie(
        key=COOKIE_CSRF_TOKEN,
        value=csrf_token,
        max_age=_MAX_AGE,
        path="/",            # доступен на всём сайте, чтобы JS мог прочитать
        httponly=False,      # ← намеренно: JS должен читать этот токен
        secure=_IS_PROD,
        samesite=_SAMESITE,
    )


def clear_auth_cookies(response: Response) -> None:
    """Удаляет обе куки при выходе."""
    response.delete_cookie(key=COOKIE_ACCESS_TOKEN, path=_COOKIE_PATH)
    response.delete_cookie(key=COOKIE_CSRF_TOKEN,   path="/")


# ── Чтение кук ─────────────────────────────────────────────────────────────────

def get_token_from_cookie(request: Request) -> str | None:
    """Извлекает JWT из HttpOnly-куки."""
    return request.cookies.get(COOKIE_ACCESS_TOKEN)


def get_csrf_from_cookie(request: Request) -> str | None:
    """Извлекает CSRF-токен из куки."""
    return request.cookies.get(COOKIE_CSRF_TOKEN)
