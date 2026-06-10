"""
auth_service.py — ИСПРАВЛЕННАЯ ВЕРСИЯ
Изменения:
  [FIX-1] vk_auth: добавлена обработка KeyError / ошибок VK API при обмене кода
  [FIX-2] vk_auth: добавлена проверка is_active перед выдачей токена (паритет с google_auth)
  [FIX-3] vk_auth: добавлена обработка httpx.RequestError (паритет с google_auth)
  [FIX-4] _generate_unique_username: ограничение числа итераций для защиты от DoS
"""
import secrets

import httpx
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.schemas.schemas import LoginRequest, RegisterRequest, TokenResponse

_MAX_USERNAME_SUFFIX = 9999  # [FIX-4] предотвращаем бесконечный цикл


async def _get_user_by_username(session: AsyncSession, username: str) -> User | None:
    result = await session.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def _get_user_by_email(session: AsyncSession, email: str) -> User | None:
    result = await session.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def _generate_unique_username(session: AsyncSession, base: str) -> str:
    """Добавляет числовой суффикс при коллизии username.
    [FIX-4] Ограничено _MAX_USERNAME_SUFFIX итерациями — защита от DoS.
    """
    username = base
    # Сначала пробуем без суффикса
    exists = await session.execute(select(User.id).where(User.username == username))
    if exists.scalar_one_or_none() is None:
        return username

    for counter in range(1, _MAX_USERNAME_SUFFIX + 1):
        username = f"{base}{counter}"
        exists = await session.execute(select(User.id).where(User.username == username))
        if exists.scalar_one_or_none() is None:
            return username

    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Не удалось сгенерировать уникальное имя пользователя",
    )


async def register_user(data: RegisterRequest, session: AsyncSession) -> TokenResponse:
    """Два отдельных запроса — каждый бьёт по своему индексу (username, email)."""
    if await _get_user_by_username(session, data.username):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Это имя пользователя уже занято",
        )
    if await _get_user_by_email(session, data.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Пользователь с таким email уже зарегистрирован",
        )

    user = User(
        username=data.username,
        email=data.email,
        hashed_password=hash_password(data.password),
        ref_code=secrets.token_urlsafe(8),
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)

    token = create_access_token(user.id)
    return TokenResponse(
        access_token=token,
        username=user.username,
        avatar_url=user.avatar_url,
        full_name=user.full_name,
    )


async def login_user(data: LoginRequest, session: AsyncSession) -> TokenResponse:
    """Не раскрываем причину ошибки (имя не найдено vs неверный пароль)."""
    user = await _get_user_by_username(session, data.username)

    # verify_password вызывается даже при user=None — защита от timing-атак
    password_ok = verify_password(data.password, user.hashed_password if user else "")

    if not user or not password_ok:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверное имя пользователя или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Аккаунт деактивирован",
        )

    token = create_access_token(user.id)
    return TokenResponse(
        access_token=token,
        username=user.username,
        avatar_url=user.avatar_url,
        full_name=user.full_name,
    )


async def google_auth(
    code: str,
    session: AsyncSession,
    redirect_uri: str | None = None,
) -> TokenResponse:
    """
    Google OAuth: code → access_token → userinfo → JWT.
    При первом входе создаёт пользователя, при повторном — обновляет аватар.

    redirect_uri — URI, который фронтенд передал Google при старте OAuth.
    Google требует, чтобы при обмене code→token был тот же URI.
    Если не передан — используется settings.FRONTEND_URL + '/index.html'.
    """
    token_data  = await _exchange_google_code(code, redirect_uri=redirect_uri)
    google_user = await _fetch_google_userinfo(token_data["access_token"])

    email:      str = google_user["email"]
    full_name:  str = google_user.get("name", "")
    avatar_url: str = google_user.get("picture", "")

    user = await _get_user_by_email(session, email)

    if user is None:
        base_username = email.split("@")[0]
        safe_base = "".join(c for c in base_username if c.isalnum() or c in "_-")[:50] or "user"
        username = await _generate_unique_username(session, safe_base)

        user = User(
            username=username, email=email,
            full_name=full_name, avatar_url=avatar_url,
            is_oauth=True, hashed_password="",
            ref_code=secrets.token_urlsafe(8),
        )
        session.add(user)
    else:
        user.avatar_url = avatar_url
        if full_name and not user.full_name:
            user.full_name = full_name

    await session.commit()
    await session.refresh(user)

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Аккаунт деактивирован",
        )

    token = create_access_token(user.id)
    return TokenResponse(
        access_token=token,
        username=user.username,
        avatar_url=user.avatar_url,
        full_name=user.full_name,
    )


async def _exchange_google_code(
    code: str,
    redirect_uri: str | None = None,
) -> dict:
    """Обменивает authorization code на Google access_token.
    
    redirect_uri должен совпадать с тем, что фронтенд передал Google.
    Если не задан — берём из settings.FRONTEND_URL.
    """
    effective_redirect_uri = redirect_uri or f"{settings.FRONTEND_URL}/index.html"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": code,
                    "client_id":     settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "redirect_uri":  effective_redirect_uri,
                    "grant_type":    "authorization_code",
                },
            )
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Ошибка соединения с Google: {exc}",
        )

    data = resp.json()
    if "error" in data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Google OAuth ошибка: {data['error']}",
        )
    return data


async def _fetch_google_userinfo(access_token: str) -> dict:
    """Получает профиль пользователя из Google."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
            )
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Ошибка получения данных от Google: {exc}",
        )

    data = resp.json()
    if "email" not in data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Не удалось получить email от Google",
        )
    return data


async def vk_auth(code: str, session: AsyncSession) -> TokenResponse:
    """
    VK OAuth: code → access_token → user_info → JWT.
    [FIX-1] Добавлена обработка ошибок VK API (KeyError на access_token).
    [FIX-2] Добавлена проверка is_active (паритет с google_auth).
    [FIX-3] Добавлена обработка httpx.RequestError.
    """
    # Обмен code на токен
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                "https://id.vk.com/oauth2/auth",
                data={
                    "grant_type":    "authorization_code",
                    "code":          code,
                    "client_id":     settings.VK_CLIENT_ID,
                    "client_secret": settings.VK_CLIENT_SECRET,
                    "redirect_uri":  f"{settings.FRONTEND_URL}/index.html",
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
    except httpx.RequestError as exc:
        # [FIX-3] Обработка сетевых ошибок
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Ошибка соединения с VK: {exc}",
        )

    token_data = resp.json()

    # [FIX-1] Проверяем наличие access_token перед использованием
    if "error" in token_data or "access_token" not in token_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"VK OAuth ошибка: {token_data.get('error', 'нет токена доступа')}",
        )

    # Получаем профиль
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                "https://id.vk.com/oauth2/user_info",
                headers={"Authorization": f"Bearer {token_data['access_token']}"},
            )
    except httpx.RequestError as exc:
        # [FIX-3] Обработка сетевых ошибок при получении профиля
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Ошибка получения данных от VK: {exc}",
        )

    user_info = resp.json().get("user", {})

    # Fallback email для VK-пользователей без email
    email = user_info.get("email", f"vk_{user_info.get('user_id', 'unknown')}@vk.local")
    first_name = user_info.get("first_name", "")
    avatar_url = user_info.get("avatar", "")

    # Находим или создаём пользователя (та же логика, что у Google)
    user = await _get_user_by_email(session, email)
    if user is None:
        base = first_name or f"vk_{user_info.get('user_id', 'user')}"
        username = await _generate_unique_username(session, base)
        user = User(
            username=username, email=email,
            avatar_url=avatar_url, is_oauth=True,
            hashed_password="", ref_code=secrets.token_urlsafe(8),
        )
        session.add(user)

    await session.commit()
    await session.refresh(user)

    # [FIX-2] Проверяем is_active ПОСЛЕ commit (паритет с google_auth)
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Аккаунт деактивирован",
        )

    return TokenResponse(
        access_token=create_access_token(user.id),
        username=user.username,
        avatar_url=user.avatar_url,
        full_name=user.full_name,
    )
