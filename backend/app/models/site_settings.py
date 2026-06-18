from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

# Fixed primary key for the one-and-only settings row. A real table (with
# explicit, typed columns) rather than a generic key-value store, because
# the set of site-wide settings is small and known ahead of time — this
# keeps the admin form and the API response simple and type-checked,
# instead of an untyped dict that every consumer has to defensively
# `.get()` out of.
SETTINGS_SINGLETON_ID = 1


class SiteSettings(Base):
    __tablename__ = "site_settings"

    id: Mapped[int] = mapped_column(primary_key=True, default=SETTINGS_SINGLETON_ID)

    # SEO
    seo_title: Mapped[str] = mapped_column(String(70), default="Лотос Тур")
    seo_description: Mapped[str] = mapped_column(String(200), default="")

    # Contacts
    contact_phone: Mapped[str] = mapped_column(String(32), default="")
    contact_email: Mapped[str] = mapped_column(String(128), default="")
    contact_address: Mapped[str] = mapped_column(String(256), default="")
    vk_url: Mapped[str] = mapped_column(String(256), default="")
    telegram_url: Mapped[str] = mapped_column(String(256), default="")

    # Branding
    logo_url: Mapped[str] = mapped_column(String(512), default="")

    # Maintenance mode — enforced by app.middleware.maintenance, not just
    # a flag sitting unused: when True, the public API returns 503 to
    # everyone except staff (see that middleware for the exact rules).
    maintenance_mode: Mapped[bool] = mapped_column(Boolean, default=False)
    maintenance_message: Mapped[str] = mapped_column(
        Text, default="Ведутся технические работы. Скоро вернёмся!"
    )

    updated_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    updated_by: Mapped["User"] = relationship(foreign_keys=[updated_by_id])
