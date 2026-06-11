import secrets

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.cookies import COOKIE_CSRF_TOKEN


_UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


_CSRF_EXEMPT_PATHS: set[str] = {
    "/api/auth/login",
    "/api/auth/register",
    "/api/auth/google/callback",
    "/api/auth/vk/callback",
    "/api/health",
    "/",
}


def generate_csrf_token() -> str:
    return secrets.token_hex(32)


def _is_exempt(path: str) -> bool:
    return path in _CSRF_EXEMPT_PATHS


class CSRFMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):
        if request.method not in _UNSAFE_METHODS or _is_exempt(request.url.path):
            return await call_next(request)

        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            return await call_next(request)

        cookie_token = request.cookies.get(COOKIE_CSRF_TOKEN)
        header_token = request.headers.get("X-CSRF-Token")

        if not cookie_token or not header_token:
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "CSRF-токен отсутствует"},
            )


        if not secrets.compare_digest(cookie_token, header_token):
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "Недействительный CSRF-токен"},
            )

        return await call_next(request)
