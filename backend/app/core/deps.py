from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cookies import get_token_from_cookie
from app.core.security import decode_access_token
from app.db.session import get_session
from app.models.user import User

# auto_error=False — обрабатываем отсутствие токена сами
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
    """Приоритет: Bearer header → HttpOnly Cookie."""
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


async def require_admin(user: User = Depends(get_current_active_user)) -> User:
    """Guard для admin-эндпоинтов."""
    if not getattr(user, "is_admin", False):
        raise _FORBIDDEN_EXC
    return user
