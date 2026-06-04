"""
FastAPI Depends: авторизация — поддержка Bearer Token И HttpOnly Cookie.

Стратегия извлечения токена (приоритет):
  1. Authorization: Bearer <token>  — API-клиенты, Swagger, мобильные приложения
  2. HttpOnly Cookie access_token   — браузерные клиенты

Это позволяет использовать оба метода без изменения остального кода.
"""
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cookies import get_token_from_cookie
from app.core.security import decode_access_token
from app.db.session import get_session
from app.models.user import User

# OAuth2 scheme остаётся — нужен для Swagger UI и API-клиентов
# auto_error=False позволяет нам самим обработать отсутствие токена
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


# ── Исключения ─────────────────────────────────────────────────────────────────

_CREDENTIALS_EXC = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Не удалось проверить учётные данные",
    headers={"WWW-Authenticate": "Bearer"},
)

_INACTIVE_EXC = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="Аккаунт деактивирован",
)

_FORBIDDEN_EXC = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="Недостаточно прав",
)


# ── Зависимости ────────────────────────────────────────────────────────────────

async def get_current_user(
    request: Request,
    bearer_token: str | None = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session),
) -> User:
    """
    Извлекает пользователя из JWT.
    Приоритет: Bearer header → HttpOnly Cookie.
    """
    # 1. Bearer Authorization header (API, Swagger)
    token = bearer_token

    # 2. Fallback: HttpOnly Cookie (браузер)
    if not token:
        token = get_token_from_cookie(request)

    if not token:
        raise _CREDENTIALS_EXC

    user_id = decode_access_token(token)
    if user_id is None:
        raise _CREDENTIALS_EXC

    user = await session.get(User, user_id)
    if user is None:
        raise _CREDENTIALS_EXC

    return user


async def get_current_active_user(
    user: User = Depends(get_current_user),
) -> User:
    """Проверяет is_active после извлечения пользователя."""
    if not user.is_active:
        raise _INACTIVE_EXC
    return user


async def require_admin(
    user: User = Depends(get_current_active_user),
) -> User:
    """Guard для admin-эндпоинтов."""
    if not getattr(user, "is_admin", False):
        raise _FORBIDDEN_EXC
    return user
