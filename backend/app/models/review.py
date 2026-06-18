from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

# Where a review came from. "site" covers both a visitor's own submission
# and an admin typing up a testimonial they received some other way
# (phone/messenger) — the distinction that actually matters for display
# is "2gis" (shows the 2GIS badge + an optional link back to the original
# review) vs everything else.
REVIEW_SOURCES = {"site", "2gis"}


class Review(Base):
    """A testimonial shown on the public site.

    Two ways a row gets here:
      1. A visitor submits it via the public form (`source="site"`,
         `is_published=False` until an admin approves it).
      2. An admin enters it directly in the panel — either an original
         testimonial, or text copied by hand from the business's 2GIS
         page (`source="2gis"`, optionally with `source_url` pointing at
         the real review for credibility). Admin-entered reviews default
         to published since the admin is already vouching for them.

    There's deliberately no automated 2GIS sync here: 2GIS doesn't offer
    a free public API for pulling another business's reviews, and
    scraping their site would violate its terms of use and break on
    every layout change — copy-pasting the text in is the practical,
    durable option for a site this size.
    """

    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    author_name: Mapped[str] = mapped_column(String(120))
    rating: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text)

    source: Mapped[str] = mapped_column(String(16), default="site")
    source_url: Mapped[str | None] = mapped_column(String(512), nullable=True)

    # Optional — a review can be about a specific tour or about the
    # company in general. ON DELETE SET NULL so removing a tour from the
    # catalog doesn't delete the testimonials people left about it; it
    # just becomes a general review.
    tour_id: Mapped[str | None] = mapped_column(
        ForeignKey("tours.id", ondelete="SET NULL"), nullable=True
    )
    # Set when a logged-in visitor submits a review — purely a trust/
    # traceability signal for the admin moderation queue, never required.
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Visitor submissions default to False (held for moderation). Admin-
    # created rows are explicitly set to True by the create endpoint.
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    tour: Mapped["Tour"] = relationship(foreign_keys=[tour_id])
    user: Mapped["User"] = relationship(foreign_keys=[user_id])
