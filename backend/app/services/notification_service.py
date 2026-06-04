"""
Сервис уведомлений.

Публичные функции:
  notify()              — создать уведомление для пользователя
  get_notifications()   — список уведомлений (с пагинацией)
  mark_read()           — отметить как прочитанное
  mark_all_read()       — отметить все как прочитанные
  record_cookie_consent() — специальный хэлпер для cookie-согласия
"""
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification, NotificationType
from app.models.user import User
from app.schemas.schemas import NotificationOut


async def notify(
    session: AsyncSession,
    user_id: int,
    type: NotificationType,
    title: str,
    body: str,
) -> Notification:
    """Создаёт и сохраняет уведомление."""
    n = Notification(user_id=user_id, type=type.value, title=title, body=body)
    session.add(n)
    await session.flush()
    await session.refresh(n)
    return n


async def get_notifications(
    user: User,
    session: AsyncSession,
    unread_only: bool = False,
    limit: int = 50,
    offset: int = 0,
) -> list[NotificationOut]:
    """Возвращает уведомления пользователя. Можно фильтровать только непрочитанные."""
    q = select(Notification).where(Notification.user_id == user.id)
    if unread_only:
        q = q.where(Notification.is_read == False)  # noqa: E712
    q = q.order_by(Notification.created_at.desc()).limit(limit).offset(offset)

    result = await session.execute(q)
    rows = result.scalars().all()
    return [NotificationOut.model_validate(r) for r in rows]


async def mark_read(
    notification_id: int,
    user: User,
    session: AsyncSession,
) -> NotificationOut:
    """Помечает уведомление прочитанным. Проверяет принадлежность пользователю."""
    n = await session.get(Notification, notification_id)
    if n is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Уведомление не найдено")
    if n.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет доступа")

    n.is_read = True
    await session.commit()
    await session.refresh(n)
    return NotificationOut.model_validate(n)


async def mark_all_read(user: User, session: AsyncSession) -> dict:
    """Массово помечает все уведомления пользователя прочитанными."""
    await session.execute(
        update(Notification)
        .where(Notification.user_id == user.id, Notification.is_read == False)  # noqa: E712
        .values(is_read=True)
    )
    await session.commit()
    return {"detail": "Все уведомления прочитаны"}


async def record_cookie_consent(user: User, session: AsyncSession) -> NotificationOut:
    """
    Создаёт системное уведомление о принятии Cookie-политики.
    Идемпотентно — не создаёт дубликаты.
    """
    # Проверяем, есть ли уже такое уведомление
    existing = await session.execute(
        select(Notification).where(
            Notification.user_id == user.id,
            Notification.type == NotificationType.COOKIE_CONSENT.value,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cookie-согласие уже зафиксировано",
        )

    n = await notify(
        session=session,
        user_id=user.id,
        type=NotificationType.COOKIE_CONSENT,
        title="Политика Cookie принята",
        body=(
            f"Вы приняли политику использования файлов Cookie "
            f"({datetime.now(timezone.utc).strftime('%d.%m.%Y %H:%M UTC')}). "
            "Мы используем только необходимые куки для работы сервиса."
        ),
    )
    await session.commit()
    return NotificationOut.model_validate(n)
