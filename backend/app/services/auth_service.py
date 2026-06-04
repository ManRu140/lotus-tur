import secrets

import httpx
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.schemas.schemas import LoginRequest, RegisterRequest, TokenResponse


async def _get_user_by_username(session: AsyncSession, username: str) -> User | None:
    result = await session.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def _get_user_by_email(session: AsyncSession, email: str) -> User | None:
    result = await session.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def _generate_unique_username(session: AsyncSession, base: str) -> str:
    """Добавляет числовой суффикс при коллизии username."""
    username = base
    counter = 1
    while True:
        exists = await session.execute(select(User.id).where(User.username == username))
        if exists.scalar_one_or_none() is None:
            return username
        username = f"{base}{counter}"
        counter += 1


async def register_user(data: RegisterRequest, session: AsyncSession) -> TokenResponse:
    """Два отдельных запроса — каждый бьёт по своему индексу (username, email)."""
    if await _get_user_by_username(session, data.username):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Это имя пользователя уже занято")
    if await _get_user_by_email(session, data.email):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Пользователь с таким email уже зарегистрирован")

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
    return TokenResponse(access_token=token, username=user.username)


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
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Аккаунт деактивирован")

    token = create_access_token(user.id)
    return TokenResponse(access_token=token, username=user.username)


async def google_auth(code: str, session: AsyncSession) -> TokenResponse:
    """
    Google OAuth: code → access_token → userinfo → JWT.
    При первом входе создаёт пользователя, при повторном — обновляет аватар.
    """
    token_data  = await _exchange_google_code(code)
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
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Аккаунт деактивирован")

    token = create_access_token(user.id)
    return TokenResponse(access_token=token, username=user.username)


async def _exchange_google_code(code: str) -> dict:
    """Обменивает authorization code на Google access_token."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": code,
                    "client_id":     settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "redirect_uri":  f"{settings.FRONTEND_URL}/index.html",
                    "grant_type":    "authorization_code",
                },
            )
    except httpx.RequestError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Ошибка соединения с Google: {exc}")

    data = resp.json()
    if "error" in data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Google OAuth ошибка: {data['error']}")
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
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Ошибка получения данных от Google: {exc}")

    data = resp.json()
    if "email" not in data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Не удалось получить email от Google")
    return data
