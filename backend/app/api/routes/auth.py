import secrets

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cookies import clear_auth_cookies, set_auth_cookies
from app.core.deps import get_current_active_user
from app.core.rate_limit import InMemoryRateLimiter
from app.db.session import get_session
from app.models.user import User
from app.core.config import settings
from app.schemas.schemas import LoginRequest, ProfileOut, RegisterRequest, TokenResponse
from app.services.auth_service import google_auth, login_user, register_user, vk_auth

router = APIRouter()

# Brute-force / credential-stuffing protection on login (audit finding
# #4 — previously only /api/promo/apply had any rate limiting at all).
# Two limiters: a tight one per (ip, username) pair catches someone
# hammering a single account; a looser one per IP alone catches someone
# spraying many usernames from the same source.
_login_limiter_per_pair = InMemoryRateLimiter(max_attempts=5, window_seconds=300)
_login_limiter_per_ip = InMemoryRateLimiter(max_attempts=20, window_seconds=300)

# Allow-list for the optional `redirect_uri` query param on the Google
# callback. Add additional values here (e.g. a staging frontend URL) as
# needed — never accept an arbitrary caller-supplied value.
_ALLOWED_OAUTH_REDIRECTS = {f"{settings.FRONTEND_URL}/auth/google/callback"}


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _set_session_cookies(response: Response, token_response: TokenResponse) -> None:
    csrf_token = secrets.token_hex(32)
    set_auth_cookies(response, token_response.access_token, csrf_token)

@router.get("/vk/callback")
async def vk_callback(
    code: str,
    response: Response,
    session: AsyncSession = Depends(get_session),
) -> TokenResponse:
    result = await vk_auth(code, session)
    _set_session_cookies(response, result)
    return result

@router.get("/vk/client-id", summary="Публичный VK Client ID для OAuth")
async def vk_client_id() -> dict:
    if not settings.VK_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="VK OAuth не настроен",
        )
    return {"client_id": settings.VK_CLIENT_ID}

@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(
    data: RegisterRequest,
    response: Response,
    session: AsyncSession = Depends(get_session),
) -> TokenResponse:
    result = await register_user(data, session)
    _set_session_cookies(response, result)
    return result

@router.post("/login", response_model=TokenResponse)
async def login(
    data: LoginRequest,
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_session),
) -> TokenResponse:
    ip = _client_ip(request)
    await _login_limiter_per_ip.check(ip)
    await _login_limiter_per_pair.check(f"{ip}:{data.username.lower()}")

    result = await login_user(data, session)
    _set_session_cookies(response, result)
    return result

@router.get("/google/callback", response_model=TokenResponse, summary="Google OAuth callback")
async def google_callback(
    code: str,
    response: Response,
    session: AsyncSession = Depends(get_session),
    redirect_uri: str | None = None,
) -> TokenResponse:
    # SECURITY: don't forward an arbitrary caller-supplied redirect_uri to
    # Google unchecked. Google itself rejects mismatched redirect_uris for
    # the registered client, which already prevents this from leaking a
    # token elsewhere — but validating against our own allow-list first
    # means a misconfigured/typo'd value fails fast with a clear error
    # instead of a confusing 502 from Google, and we never depend solely
    # on a third party's enforcement for something we can check ourselves.
    if redirect_uri is not None and redirect_uri not in _ALLOWED_OAUTH_REDIRECTS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Недопустимый redirect_uri",
        )
    result = await google_auth(code, session, redirect_uri=redirect_uri)
    _set_session_cookies(response, result)
    return result

@router.post("/logout", summary="Выход из системы")
async def logout(response: Response) -> dict:
    clear_auth_cookies(response)
    return {"detail": "Вы вышли из системы"}

@router.get("/me", response_model=ProfileOut, summary="Текущий пользователь")
async def get_me(user: User = Depends(get_current_active_user)) -> ProfileOut:
    return user

@router.get("/google/client-id", summary="Публичный Google Client ID для OAuth")
async def google_client_id() -> dict:
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google OAuth не настроен",
        )
    return {"client_id": settings.GOOGLE_CLIENT_ID}
