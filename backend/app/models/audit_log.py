from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AdminAuditLog(Base):
    """Append-only record of administrative actions.

    `admin_username` is denormalised (copied at write time) so the log
    stays readable even if the admin account is later renamed or deleted
    — audit trails must never depend on the current state of the actor.
    """

    __tablename__ = "admin_audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    admin_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True
    )
    admin_username: Mapped[str] = mapped_column(String(64))

    # Dotted action name, e.g. "tour.create", "user.role_change",
    # "settings.update", "content.delete". Keeping this a free string
    # (rather than an enum) means new admin features never require a
    # migration just to log a new action type.
    action: Mapped[str] = mapped_column(String(64), index=True)

    target_type: Mapped[str] = mapped_column(String(32), index=True)
    target_id: Mapped[str] = mapped_column(String(64), index=True)

    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )

    admin: Mapped["User"] = relationship(foreign_keys=[admin_id])
