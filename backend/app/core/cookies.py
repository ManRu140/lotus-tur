from fastapi import Request, Response

from app.core.config import settings

COOKIE_ACCESS_TOKEN = "access_token"
COOKIE_CSRF_TOKEN   = "csrf_token"

# Frontend (agile-intuition-*.railway.app) and backend
# (lotus-tur-*.railway.app) are on different subdomains — this is a
# cross-site request. Browsers block cookies with SameSite=Lax on
# cross-site requests, which is why /api/admin/stats returned 401
# immediately after a successful /api/auth/login: the access_token
# cookie was set but never sent back on the next request.
#
# Fix: SameSite=None tells the browser to send the cookie on cross-site
# requests. SameSite=None REQUIRES Secure=True (browsers reject the
# combination otherwise). Railway always serves HTTPS so Secure=True
# is safe unconditionally here.
_SAMESITE    = "none"
_SECURE      = True          # required by browsers when SameSite=None
_COOKIE_PATH = "/api"
_MAX_AGE     = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60

def set_auth_cookies(response: Response, access_token: str, csrf_token: str) -> None:
    response.set_cookie(
        key=COOKIE_ACCESS_TOKEN, value=access_token,
        max_age=_MAX_AGE, path=_COOKIE_PATH,
        httponly=True, secure=_SECURE, samesite=_SAMESITE,
    )
    response.set_cookie(
        key=COOKIE_CSRF_TOKEN, value=csrf_token,
        max_age=_MAX_AGE, path="/",
        httponly=False,
        secure=_SECURE, samesite=_SAMESITE,
    )

def clear_auth_cookies(response: Response) -> None:
    response.delete_cookie(
        key=COOKIE_ACCESS_TOKEN, path=_COOKIE_PATH,
        secure=_SECURE, samesite=_SAMESITE,
    )
    response.delete_cookie(
        key=COOKIE_CSRF_TOKEN, path="/",
        secure=_SECURE, samesite=_SAMESITE,
    )

def get_token_from_cookie(request: Request) -> str | None:
    return request.cookies.get(COOKIE_ACCESS_TOKEN)

def get_csrf_from_cookie(request: Request) -> str | None:
    return request.cookies.get(COOKIE_CSRF_TOKEN)
