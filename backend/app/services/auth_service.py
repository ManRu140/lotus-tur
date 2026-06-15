import secrets

import httpx
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.schemas.schemas import LoginRequest, RegisterRequest, TokenResponse

_MAX_USERNAME_SUFFIX = 9999


async def _get_user_by_username(session: AsyncSession, username: str) -> User | None:
    result = await session.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def _get_user_by_email(session: AsyncSession, email: str) -> User | None:
    result = await session.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def _generate_unique_username(session: AsyncSession, base: str) -> str:
    exists = await session.execute(select(User.id).where(User.username == base))
    if exists.scalar_one_or_none() is None:
        return base

    for counter in range(1, _MAX_USERNAME_SUFFIX + 1):
        candidate = f"{base}{counter}"
        exists = await session.execute(select(User.id).where(User.username == candidate))
        if exists.scalar_one_or_none() is None:
            return candidate

    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Не удалось сгенерировать уникальное имя пользователя",
    )


async def register_user(data: RegisterRequest, session: AsyncSession) -> TokenResponse:
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

    return TokenResponse(
        access_token=create_access_token(user.id),
        username=user.username,
        avatar_url=user.avatar_url,
        full_name=user.full_name,
    )


async def login_user(data: LoginRequest, session: AsyncSession) -> TokenResponse:
    user = await _get_user_by_username(session, data.username)

    # Constant-time comparison regardless of whether user exists
    stored_hash = user.hashed_password if user else ""
    password_ok = verify_password(data.password, stored_hash)

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

    return TokenResponse(
        access_token=create_access_token(user.id),
        username=user.username,
        avatar_url=user.avatar_url,
        full_name=user.full_name,
    )


async def google_auth(
    code: str, session: AsyncSession, redirect_uri: str | None = None
) -> TokenResponse:
    token_uri = redirect_uri or f"{settings.FRONTEND_URL}/auth/google/callback"

    async with httpx.AsyncClient(timeout=10) as client:
        try:
            token_resp = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": code,
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "redirect_uri": token_uri,
                    "grant_type": "authorization_code",
                },
            )
            token_resp.raise_for_status()
            access_token = token_resp.json().get("access_token")
            if not access_token:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Не удалось получить токен от Google",
                )

            user_resp = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            user_resp.raise_for_status()
            gdata = user_resp.json()
        except httpx.HTTPStatusError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Ошибка Google OAuth: {exc.response.status_code}",
            ) from exc
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Сервис Google недоступен",
            ) from exc

    email: str = gdata.get("email", "")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google не вернул email",
        )

    user = await _get_user_by_email(session, email)
    if not user:
        base = (gdata.get("name") or email.split("@")[0]).replace(" ", "_")[:50]
        username = await _generate_unique_username(session, base)
        user = User(
            username=username,
            email=email,
            full_name=gdata.get("name"),
            avatar_url=gdata.get("picture"),
            is_oauth=True,
            ref_code=secrets.token_urlsafe(8),
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Аккаунт деактивирован")

    return TokenResponse(
        access_token=create_access_token(user.id),
        username=user.username,
        avatar_url=user.avatar_url,
        full_name=user.full_name,
    )


async def vk_auth(code: str, session: AsyncSession) -> TokenResponse:
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            token_resp = await client.get(
                "https://oauth.vk.com/access_token",
                params={
                    "client_id": settings.VK_CLIENT_ID,
                    "client_secret": settings.VK_CLIENT_SECRET,
                    "redirect_uri": settings.VK_REDIRECT_URI,
                    "code": code,
                },
            )
            token_resp.raise_for_status()
            vk_data = token_resp.json()
        except httpx.HTTPStatusError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Ошибка VK OAuth: {exc.response.status_code}",
            ) from exc
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Сервис VK недоступен",
            ) from exc

    vk_user_id: int | None = vk_data.get("user_id")
    vk_email: str | None = vk_data.get("email")
    if not vk_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="VK не вернул user_id",
        )

    vk_email = vk_email or f"vk_{vk_user_id}@vk.local"
    user = await _get_user_by_email(session, vk_email)

    if not user:
        base_username = f"vk_{vk_user_id}"
        username = await _generate_unique_username(session, base_username)
        user = User(
            username=username,
            email=vk_email,
            is_oauth=True,
            ref_code=secrets.token_urlsafe(8),
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Аккаунт деактивирован")

    return TokenResponse(
        access_token=create_access_token(user.id),
        username=user.username,
        avatar_url=user.avatar_url,
        full_name=user.full_name,
    )
