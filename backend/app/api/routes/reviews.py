"""Public-facing review endpoints.

Two operations, open to anyone (no login required):
  - GET  /api/reviews  — published reviews + aggregate rating, optionally
    filtered to one tour. This is what the public site renders.
  - POST /api/reviews  — a visitor submits a new review. It is always
    created with `is_published=False`; nothing posted here appears on
    the site until an admin/moderator approves it from the panel (see
    app/api/routes/admin_reviews.py).

Submission is rate-limited per IP (not per-account) since it's open to
anonymous visitors — see InMemoryRateLimiter's docstring for the
single-instance caveat that already applies to login/promo.
"""

import re
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.deps import get_current_user_optional
from app.core.rate_limit import InMemoryRateLimiter
from app.db.session import get_session
from app.models.review import Review
from app.models.tour import Tour
from app.models.user import User

router = APIRouter()

# 5 submissions/hour/IP is generous for a real visitor (nobody leaves 5
# genuine reviews an hour) while still bounding how fast a spam bot can
# fill the moderation queue.
_review_submit_limiter = InMemoryRateLimiter(max_attempts=5, window_seconds=3600)


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


class ReviewOut(BaseModel):
    id: int
    author_name: str
    rating: int
    text: str
    source: str
    source_url: Optional[str]
    tour_id: Optional[str]
    tour_name: Optional[str] = None
    is_published: bool
    created_at: datetime

    model_config = {"from_attributes": True}


def _to_review_out(review: Review) -> ReviewOut:
    out = ReviewOut.model_validate(review)
    out.tour_name = review.tour.name if review.tour else None
    return out


class ReviewStatsOut(BaseModel):
    average_rating: float
    total_count: int


class ReviewListOut(BaseModel):
    reviews: list[ReviewOut]
    stats: ReviewStatsOut


@router.get("/reviews", response_model=ReviewListOut, summary="Опубликованные отзывы")
async def list_reviews(
    tour_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> ReviewListOut:
    q = select(Review).options(joinedload(Review.tour)).where(Review.is_published.is_(True))
    if tour_id:
        q = q.where(Review.tour_id == tour_id)
    rows = (
        await session.execute(q.order_by(Review.created_at.desc()).limit(limit).offset(offset))
    ).unique().scalars().all()

    stats_q = select(func.avg(Review.rating), func.count(Review.id)).where(Review.is_published.is_(True))
    if tour_id:
        stats_q = stats_q.where(Review.tour_id == tour_id)
    avg_rating, total = (await session.execute(stats_q)).one()

    return ReviewListOut(
        reviews=[_to_review_out(r) for r in rows],
        stats=ReviewStatsOut(
            average_rating=round(float(avg_rating), 1) if avg_rating else 0.0,
            total_count=total or 0,
        ),
    )


class ReviewCreate(BaseModel):
    author_name: str = Field(min_length=1, max_length=120)
    rating: int = Field(ge=1, le=5)
    text: str = Field(min_length=1, max_length=4000)
    tour_id: Optional[str] = Field(default=None, max_length=64)

    @field_validator("author_name", "text")
    @classmethod
    def _no_unsafe_chars(cls, v: str) -> str:
        v = v.strip()
        if re.search(r"[<>]", v):
            raise ValueError("Поле не должно содержать символы < >")
        return v


@router.post(
    "/reviews",
    response_model=ReviewOut,
    status_code=201,
    summary="Оставить отзыв (отправляется на проверку модератору)",
)
async def submit_review(
    data: ReviewCreate,
    request: Request,
    user: Optional[User] = Depends(get_current_user_optional),
    session: AsyncSession = Depends(get_session),
) -> ReviewOut:
    await _review_submit_limiter.check(_client_ip(request))

    if data.tour_id and not await session.get(Tour, data.tour_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Тур не найден")

    review = Review(
        author_name=data.author_name,
        rating=data.rating,
        text=data.text,
        tour_id=data.tour_id,
        user_id=user.id if user else None,
        source="site",
        is_published=False,
    )
    session.add(review)
    await session.commit()
    await session.refresh(review, attribute_names=["tour"])
    return _to_review_out(review)
