"""Enforces SiteSettings.maintenance_mode so the admin toggle is a real
feature rather than a flag nobody reads.

Design choices, deliberately kept simple:
  - `/api/admin/*` is always exempt: once maintenance mode is on, admins
    still need their own panel to work (e.g. to turn it back off).
  - `/api/auth/*`, `/api/health`, `/api/settings`, `/static/*`, and the
    docs routes are exempt so login and the maintenance banner itself
    keep working.
  - Everything else under `/api/*` (tours, bookings, profile, promo,
    notifications, public content/banners) returns 503 while the flag is
    on — this is what actually makes "technical works" mean something
    for ordinary visitors.
  - The flag is cached in-process for a few seconds so we aren't hitting
    the database on every single request; toggling maintenance mode may
    take a few seconds to take effect across all requests, which is an
    acceptable trade-off for a flag that changes a few times a year.
"""

import time

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

_EXEMPT_PREFIXES = (
    "/api/admin",
    "/api/auth",
    "/api/health",
    "/api/settings",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/static",
)

_CACHE_TTL_SECONDS = 5
_cache: dict = {"checked_at": 0.0, "is_on": False, "message": ""}


async def _refresh_cache() -> None:
    # Imported lazily to avoid a circular import at module load time
    # (db.session is set up after the app's settings, and this module
    # is imported by main.py before the engine necessarily exists).
    from app.db.session import AsyncSessionLocal
    from app.models.site_settings import SETTINGS_SINGLETON_ID, SiteSettings

    async with AsyncSessionLocal() as session:
        row = await session.get(SiteSettings, SETTINGS_SINGLETON_ID)
        _cache["is_on"] = bool(row.maintenance_mode) if row else False
        _cache["message"] = row.maintenance_message if row else ""
        _cache["checked_at"] = time.monotonic()


class MaintenanceModeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if not path.startswith("/api") or any(path.startswith(p) for p in _EXEMPT_PREFIXES):
            return await call_next(request)

        if time.monotonic() - _cache["checked_at"] > _CACHE_TTL_SECONDS:
            try:
                await _refresh_cache()
            except Exception:
                # If the DB is briefly unreachable, fail OPEN (serve the
                # site) rather than locking everyone out on a transient
                # error — maintenance mode is a deliberate admin choice,
                # not something a DB hiccup should accidentally trigger.
                return await call_next(request)

        if not _cache["is_on"]:
            return await call_next(request)

        return JSONResponse(
            status_code=503,
            content={"detail": _cache["message"] or "Ведутся технические работы"},
            headers={"Retry-After": "120"},
        )
