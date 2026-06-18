from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ContentBlock(Base):
    """A single editable piece of site copy: a whole page, or a small
    text block (hero text, footer note, an FAQ answer, etc).

    `key` is a stable slug the *frontend* code looks up by — e.g. the
    public site would fetch `GET /api/content/about_page` to render the
    "About us" page, or `GET /api/content/footer_note` for a snippet.
    Using one flexible table for both "pages" and "blocks" (distinguished
    by `block_type`) avoids forcing two near-identical tables/CRUD UIs for
    what is, from a data-modelling point of view, the same thing: a slug,
    a title, a body, and a publish flag.
    """

    __tablename__ = "content_blocks"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    key: Mapped[str] = mapped_column(String(96), unique=True, index=True)

    block_type: Mapped[str] = mapped_column(String(16), default="block")  # "block" | "page"
    title: Mapped[str] = mapped_column(String(256))
    body: Mapped[str] = mapped_column(Text)

    is_published: Mapped[bool] = mapped_column(Boolean, default=True)

    updated_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    updated_by: Mapped["User"] = relationship(foreign_keys=[updated_by_id])


class Banner(Base):
    """A promotional banner/slide shown on the public site (e.g. a
    homepage carousel item or a seasonal announcement strip).
    """

    __tablename__ = "banners"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    title: Mapped[str] = mapped_column(String(256))
    subtitle: Mapped[str | None] = mapped_column(String(512), nullable=True)
    image_url: Mapped[str] = mapped_column(String(512))
    link_url: Mapped[str | None] = mapped_column(String(512), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    # Optional scheduling window — nullable so "always on while active" is
    # the default and admins aren't forced to pick dates for every banner.
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
