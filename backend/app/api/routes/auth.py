"""
API роутер: авторизация с поддержкой HttpOnly Cookie.

Изменения по сравнению с оригиналом:
  - Все auth-эндпоинты возвращают токен ОДНОВРЕМЕННО:
      a) в теле JSON (для мобильных клиентов / Swagger)
      b) в HttpOnly Cookie (для браузерных клиентов)
  - Добавлен POST /logout — очищает куки
  - CSRF-токен генерируется при каждом входе/регистрации
  - GET /me — возвращает текущего пользователя (для проверки сессии)
"""
import secrets

from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cookies import clear_auth_cookies, set_auth_cookies
from app.core.deps import get_current_active_user
from app.db.session import get_session
from app.models.user import User
from app.core.config import settings
from app.schemas.schemas import LoginRequest, ProfileOut, RegisterRequest, TokenResponse
from app.services.auth_service import google_auth, login_user, register_user

router = APIRouter()


def _set_session_cookies(response: Response, token_response: TokenResponse) -> None:
    """Хэлпер: генерирует CSRF и устанавливает обе куки."""
    csrf_token = secrets.token_hex(32)
    set_auth_cookies(response, token_response.access_token, csrf_token)


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
    response: Response,
    session: AsyncSession = Depends(get_session),
) -> TokenResponse:
    result = await login_user(data, session)
    _set_session_cookies(response, result)
    return result


@router.get(
    "/google/callback",
    response_model=TokenResponse,
    summary="Google OAuth callback",
)
async def google_callback(
    code: str,
    response: Response,
    session: AsyncSession = Depends(get_session),
) -> TokenResponse:
    """Принимает code от Google, возвращает JWT токен и устанавливает куки."""
    result = await google_auth(code, session)
    _set_session_cookies(response, result)
    return result


@router.post("/logout", summary="Выход из системы")
async def logout(response: Response) -> dict:
    """
    Очищает куки сессии.
    Клиент также должен удалить JWT из localStorage (если хранится там).
    """
    clear_auth_cookies(response)
    return {"detail": "Вы вышли из системы"}


@router.get("/me", response_model=ProfileOut, summary="Текущий пользователь")
async def get_me(user: User = Depends(get_current_active_user)) -> ProfileOut:
    """Проверка сессии — возвращает профиль текущего пользователя."""
    return user


@router.get(
    "/google/client-id",
    summary="Публичный Google Client ID для OAuth",
    include_in_schema=True,
)
async def google_client_id() -> dict:
    """
    BUG FIX: возвращает Google Client ID для фронтенда.
    Это НЕ секрет — client_id публичен по стандарту OAuth.
    Выносим его с фронтенда на бэкенд для централизованной конфигурации.
    """
    if not settings.GOOGLE_CLIENT_ID:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google OAuth не настроен",
        )
    return {"client_id": settings.GOOGLE_CLIENT_ID}
