"""
models/user.py — ИСПРАВЛЕННАЯ ВЕРСИЯ
Изменения:
  [FIX-1] Исправлен отступ в relationship notifications (был неверный)
  [FIX-2] Добавлено поле is_admin (требуется для require_admin в deps.py)
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(256), default="")
    full_name: Mapped[str | None] = mapped_column(String(256), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_oauth: Mapped[bool] = mapped_column(Boolean, default=False)
    # [FIX-2] Добавлено поле — требуется для require_admin guard в deps.py
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    ref_code: Mapped[str | None] = mapped_column(String(32), nullable=True, unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    bookings: Mapped[list["Booking"]] = relationship(  # noqa: F821
        back_populates="user", lazy="select"
    )
    user_achievements: Mapped[list["UserAchievement"]] = relationship(  # noqa: F821
        back_populates="user", lazy="select"
    )
    # [FIX-1] Исправлен отступ: аргументы relationship были на уровне класса
    notifications: Mapped[list["Notification"]] = relationship(  # noqa: F821
        back_populates="user", lazy="select"
    )
