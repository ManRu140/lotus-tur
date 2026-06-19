import secrets

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.cookies import COOKIE_CSRF_TOKEN
from app.core.security import decode_access_token

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

        # SECURITY: a CSRF attack cannot inject an Authorization header
        # (cross-site requests can't set arbitrary headers without
        # triggering a CORS preflight, which our CORS policy already
        # blocks for unlisted origins). That's *why* Bearer requests can
        # skip the cookie-based check below. But the exemption must only
        # apply to a token that actually verifies — otherwise any caller
        # bypasses CSRF protection entirely just by sending a garbage
        # "Authorization: Bearer x" header, since the previous code only
        # checked the header's mere presence, never its validity.
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.removeprefix("Bearer ").strip()
            if token and decode_access_token(token) is not None:
                return await call_next(request)
            # Invalid/garbage Bearer token: fall through to the
            # cookie-based CSRF check, since the request might still be
            # legitimately cookie-authenticated.

        cookie_token = request.cookies.get(COOKIE_CSRF_TOKEN)

        # No session/CSRF cookie at all means this is a genuinely
        # anonymous request (e.g. the public review-submission form) —
        # there's no ambient session for an attacker to ride along on,
        # so there's nothing for CSRF protection to do here. Any
        # endpoint that actually requires a logged-in user still
        # enforces that separately via its own auth dependency; this
        # middleware only needs to step in once a session cookie exists.
        if not cookie_token:
            return await call_next(request)

        header_token = request.headers.get("X-CSRF-Token")

        if not header_token:
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
