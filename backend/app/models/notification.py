"""
Модель и сервис уведомлений пользователя.

Типы уведомлений:
  - cookie_consent  — принятие политики Cookie
  - booking         — статус бронирования
  - achievement     — разблокировано достижение
  - promo           — промокод применён / истёк
  - system          — системные сообщения
"""
from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class NotificationType(str, Enum):
    COOKIE_CONSENT = "cookie_consent"
    BOOKING        = "booking"
    ACHIEVEMENT    = "achievement"
    PROMO          = "promo"
    SYSTEM         = "system"


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    type: Mapped[str] = mapped_column(String(32))      # NotificationType value
    title: Mapped[str] = mapped_column(String(256))
    body: Mapped[str] = mapped_column(Text)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    user: Mapped["User"] = relationship(back_populates="notifications")  # noqa: F821
