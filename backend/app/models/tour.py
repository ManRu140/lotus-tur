from __future__ import annotations

from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

class Tour(Base):
    __tablename__ = "tours"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tag: Mapped[str] = mapped_column(String(64))
    name: Mapped[str] = mapped_column(String(128))
    description: Mapped[str] = mapped_column(Text)
    price: Mapped[int] = mapped_column(Integer)
    img_url: Mapped[str] = mapped_column(String(512))

    # Day of the week this tour normally runs on (e.g. "Понедельник",
    # "Ежедневно", "По запросу"). Previously referenced by the admin UI's
    # weekly-schedule view but never actually persisted — PATCH requests
    # carrying `schedule` were silently dropped because neither this
    # column nor AdminTourUpdate declared the field (audit finding #7).
    schedule: Mapped[str] = mapped_column(String(32), default="По запросу")

    booked_dates: Mapped[str | None] = mapped_column(Text, nullable=True)

    bookings: Mapped[list[Booking]] = relationship(
        "Booking", back_populates="tour", lazy="select"
    )

    @property
    def booked_dates_list(self) -> list[str]:
        if not self.booked_dates:
            return []
        return [d.strip() for d in self.booked_dates.split(",") if d.strip()]
