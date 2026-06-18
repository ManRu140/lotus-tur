from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cookies import get_token_from_cookie
from app.core.security import decode_access_token
from app.db.session import get_session
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

_CREDENTIALS_EXC = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Не удалось проверить учётные данные",
    headers={"WWW-Authenticate": "Bearer"},
)
_INACTIVE_EXC  = HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Аккаунт деактивирован")
_FORBIDDEN_EXC = HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав")

async def get_current_user(
    request: Request,
    bearer_token: str | None = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session),
) -> User:
    token = bearer_token or get_token_from_cookie(request)

    if not token:
        raise _CREDENTIALS_EXC

    user_id = decode_access_token(token)
    if user_id is None:
        raise _CREDENTIALS_EXC

    user = await session.get(User, user_id)
    if user is None:
        raise _CREDENTIALS_EXC

    return user

async def get_current_active_user(user: User = Depends(get_current_user)) -> User:
    if not user.is_active:
        raise _INACTIVE_EXC
    return user

async def get_current_user_optional(
    request: Request,
    bearer_token: str | None = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session),
) -> User | None:
    """Same lookup as get_current_user, but returns None instead of
    raising on a missing/invalid session. For endpoints open to both
    logged-in and anonymous visitors (e.g. submitting a review) that
    only want to attach a user_id opportunistically when one exists.
    """
    token = bearer_token or get_token_from_cookie(request)
    if not token:
        return None
    user_id = decode_access_token(token)
    if user_id is None:
        return None
    return await session.get(User, user_id)

async def require_admin(user: User = Depends(get_current_active_user)) -> User:
    if not getattr(user, "is_admin", False):
        raise _FORBIDDEN_EXC
    return user

async def require_staff(user: User = Depends(get_current_active_user)) -> User:
    """Admin OR moderator. Use this for day-to-day operational endpoints
    (bookings, content, tours) that moderators should be able to touch.
    Keep using `require_admin` for sensitive endpoints moderators should
    NOT reach: user role changes, password resets, site settings, and
    reading the full audit log.
    """
    if getattr(user, "role", "user") not in ("admin", "moderator"):
        raise _FORBIDDEN_EXC
    return user
