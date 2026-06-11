from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings

_IS_PROD = settings.ENV == "production"


_CSP_API = "default-src 'none'; frame-ancestors 'none';"


_PERMISSIONS_POLICY = (
    "camera=(), microphone=(), geolocation=(), payment=(), usb=(), interest-cohort=()"
)


_HSTS = "max-age=31536000; includeSubDomains; preload"


class SecurityHeadersMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        response.headers["X-Content-Type-Options"]  = "nosniff"
        response.headers["X-Frame-Options"]         = "DENY"
        response.headers["X-XSS-Protection"]        = "0"
        response.headers["Referrer-Policy"]         = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"]      = _PERMISSIONS_POLICY
        response.headers["Content-Security-Policy"] = _CSP_API

        if request.url.path.startswith("/api"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
            response.headers["Pragma"]        = "no-cache"

        if _IS_PROD:
            response.headers["Strict-Transport-Security"] = _HSTS


        response.headers.pop("server",       None)
        response.headers.pop("x-powered-by", None)

        return response
