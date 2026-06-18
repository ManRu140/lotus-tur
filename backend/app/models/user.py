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

    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)

    # Three-tier role system (Stage 2). `is_admin` above is kept as a
    # backward-compatible derived flag — every code path that *sets* role
    # also keeps is_admin in sync, so the original `require_admin` check
    # (`getattr(user, "is_admin", False)`) keeps working untouched.
    # "moderator" sits between "user" and "admin": see require_staff()
    # in app/core/deps.py for which endpoints it can reach.
    role: Mapped[str] = mapped_column(String(16), default="user")

    # Set by an admin-initiated password reset (see admin.py). Not yet
    # enforced anywhere on the public site — the column/flag exists so a
    # future "you must change your password" UI on the public frontend
    # has something to read; building that flow was out of scope here.
    force_password_change: Mapped[bool] = mapped_column(Boolean, default=False)

    ref_code: Mapped[str | None] = mapped_column(String(32), nullable=True, unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    bookings: Mapped[list["Booking"]] = relationship(
        back_populates="user", lazy="select"
    )
    user_achievements: Mapped[list["UserAchievement"]] = relationship(
        back_populates="user", lazy="select"
    )

    notifications: Mapped[list["Notification"]] = relationship(
        back_populates="user", lazy="select"
    )
