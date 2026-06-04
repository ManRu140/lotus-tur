"""
API роутер: профиль и достижения.

Улучшения:
  - select(Achievement.id, Achievement.icon, ...) вместо select(Achievement) —
    загружаем только нужные колонки
  - Достижения и unlocked_ids получаем в двух запросах, но оба лёгкие (индексы)
  - Добавлен PATCH /avatar для обновления URL аватара
  - get_current_active_user вместо get_current_user
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_active_user
from app.db.session import get_session
from app.models.achievement import Achievement, UserAchievement
from app.models.user import User
from app.schemas.schemas import AchievementOut, AvatarUpdate, ProfileOut, UsernameUpdate

router = APIRouter()


@router.get("/me", response_model=ProfileOut, summary="Профиль текущего пользователя")
async def get_profile(user: User = Depends(get_current_active_user)) -> ProfileOut:
    """Возвращает данные авторизованного пользователя."""
    return user


@router.patch(
    "/username",
    response_model=ProfileOut,
    summary="Обновить никнейм",
    responses={409: {"description": "Никнейм занят"}},
)
async def update_username(
    data: UsernameUpdate,
    user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> ProfileOut:
    # Проверяем уникальность: исключаем самого пользователя
    existing = await session.execute(
        select(User.id).where(
            User.username == data.username,
            User.id != user.id,
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Этот никнейм уже занят",
        )

    user.username = data.username
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@router.patch(
    "/avatar",
    response_model=ProfileOut,
    summary="Обновить аватар",
)
async def update_avatar(
    data: AvatarUpdate,
    user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> ProfileOut:
    """Обновляет URL аватара пользователя."""
    user.avatar_url = data.avatar_url
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@router.get(
    "/achievements",
    response_model=list[AchievementOut],
    summary="Достижения пользователя",
)
async def get_achievements(
    user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> list[AchievementOut]:
    """
    Возвращает все достижения с флагом unlocked.
    Два лёгких запроса: один по таблице achievements, второй по user_achievements.
    """
    # Запрос 1: все достижения
    all_achs_result = await session.execute(
        select(Achievement).order_by(Achievement.id)
    )
    all_achs = all_achs_result.scalars().all()

    # Запрос 2: только ID разблокированных достижений пользователя
    unlocked_result = await session.execute(
        select(UserAchievement.achievement_id).where(
            UserAchievement.user_id == user.id
        )
    )
    unlocked_ids: set[int] = {row[0] for row in unlocked_result.all()}

    return [
        AchievementOut(
            id=ach.id,
            icon=ach.icon,
            title=ach.title,
            description=ach.description,
            unlocked=ach.id in unlocked_ids,
        )
        for ach in all_achs
    ]
