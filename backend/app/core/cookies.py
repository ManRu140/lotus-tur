from fastapi import Request, Response

from app.core.config import settings

COOKIE_ACCESS_TOKEN = "access_token"
COOKIE_CSRF_TOKEN   = "csrf_token"

_IS_PROD     = settings.ENV == "production"
_SAMESITE    = "lax"
_COOKIE_PATH = "/api"
_MAX_AGE     = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60


def set_auth_cookies(response: Response, access_token: str, csrf_token: str) -> None:
    """
    Устанавливает две куки:
    - access_token: HttpOnly (JS не читает) — защита от XSS
    - csrf_token: без HttpOnly (JS вставляет в X-CSRF-Token) — Double Submit Cookie
    """
    response.set_cookie(
        key=COOKIE_ACCESS_TOKEN, value=access_token,
        max_age=_MAX_AGE, path=_COOKIE_PATH,
        httponly=True, secure=_IS_PROD, samesite=_SAMESITE,
    )
    response.set_cookie(
        key=COOKIE_CSRF_TOKEN, value=csrf_token,
        max_age=_MAX_AGE, path="/",
        httponly=False,  # намеренно: JS должен читать этот токен
        secure=_IS_PROD, samesite=_SAMESITE,
    )


def clear_auth_cookies(response: Response) -> None:
    """Удаляет обе куки при выходе."""
    response.delete_cookie(key=COOKIE_ACCESS_TOKEN, path=_COOKIE_PATH)
    response.delete_cookie(key=COOKIE_CSRF_TOKEN,   path="/")


def get_token_from_cookie(request: Request) -> str | None:
    return request.cookies.get(COOKIE_ACCESS_TOKEN)


def get_csrf_from_cookie(request: Request) -> str | None:
    return request.cookies.get(COOKIE_CSRF_TOKEN)
