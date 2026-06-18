"""Admin endpoints for managing reviews.

Two distinct things land here:
  1. Moderation of visitor-submitted reviews from the public site
     (app/api/routes/reviews.py) — approve (PATCH is_published=true),
     edit, or delete.
  2. Manually-entered testimonials, including text copied by hand from
     the business's 2GIS page (source="2gis", optionally with
     source_url pointing at the original for credibility). There is
     deliberately no automated 2GIS sync — see app/models/review.py's
     docstring for why.

Permission note: unlike content/banners (create+update=staff,
delete=admin), every review action here is require_staff. Moderating
reviews — including deleting spam/abuse — is exactly the kind of
day-to-day work the "moderator" role exists for, not a sensitive
privilege like changing someone's role or resetting a password.
"""

import re
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.deps import require_staff
from app.core.validators import validate_http_url
from app.db.session import get_session
from app.models.review import REVIEW_SOURCES, Review
from app.models.tour import Tour
from app.models.user import User
from app.services.audit_service import log_admin_action

router = APIRouter()


def _no_unsafe_chars(v: str) -> str:
    if re.search(r"[<>]", v):
        raise ValueError("Поле не должно содержать символы < >")
    return v


class AdminReviewOut(BaseModel):
    id: int
    author_name: str
    rating: int
    text: str
    source: str
    source_url: Optional[str]
    tour_id: Optional[str]
    tour_name: Optional[str] = None
    user_id: Optional[int]
    is_published: bool
    created_at: datetime

    model_config = {"from_attributes": True}


def _to_admin_out(review: Review) -> AdminReviewOut:
    return AdminReviewOut(
        id=review.id, author_name=review.author_name, rating=review.rating,
        text=review.text, source=review.source, source_url=review.source_url,
        tour_id=review.tour_id, tour_name=review.tour.name if review.tour else None,
        user_id=review.user_id, is_published=review.is_published, created_at=review.created_at,
    )


@router.get("/reviews", response_model=list[AdminReviewOut], summary="Все отзывы (для модерации)")
async def list_reviews_admin(
    is_published: Optional[bool] = Query(None),
    source: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    _: User = Depends(require_staff),
    session: AsyncSession = Depends(get_session),
) -> list[AdminReviewOut]:
    q = select(Review).options(joinedload(Review.tour)).order_by(Review.created_at.desc())
    if is_published is not None:
        q = q.where(Review.is_published.is_(is_published))
    if source:
        q = q.where(Review.source == source)
    rows = (await session.execute(q.limit(limit).offset(offset))).unique().scalars().all()
    return [_to_admin_out(r) for r in rows]


class AdminReviewCreate(BaseModel):
    author_name: str = Field(min_length=1, max_length=120)
    rating: int = Field(ge=1, le=5)
    text: str = Field(min_length=1, max_length=4000)
    source: str = Field(default="site")
    source_url: Optional[str] = Field(default=None, max_length=512)
    tour_id: Optional[str] = Field(default=None, max_length=64)
    is_published: bool = True

    @field_validator("source")
    @classmethod
    def _validate_source(cls, v: str) -> str:
        if v not in REVIEW_SOURCES:
            raise ValueError(f"source должен быть одним из: {', '.join(sorted(REVIEW_SOURCES))}")
        return v

    @field_validator("author_name", "text")
    @classmethod
    def _strip_and_check(cls, v: str) -> str:
        return _no_unsafe_chars(v.strip())

    @field_validator("source_url")
    @classmethod
    def _validate_source_url(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v == "":
            return None
        return validate_http_url(v, field_name="source_url")


@router.post("/reviews", response_model=AdminReviewOut, status_code=201, summary="Добавить отзыв вручную (или с 2ГИС)")
async def create_review_admin(
    data: AdminReviewCreate,
    request: Request,
    admin: User = Depends(require_staff),
    session: AsyncSession = Depends(get_session),
) -> AdminReviewOut:
    if data.tour_id and not await session.get(Tour, data.tour_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Тур не найден")

    review = Review(
        author_name=data.author_name, rating=data.rating, text=data.text,
        source=data.source, source_url=data.source_url, tour_id=data.tour_id,
        is_published=data.is_published,
    )
    session.add(review)
    await session.commit()
    await session.refresh(review, attribute_names=["tour"])
    await log_admin_action(
        session, admin, action="review.create", target_type="review", target_id=review.id,
        details=f"Добавлен отзыв от «{review.author_name}» ({review.source})", request=request,
    )
    return _to_admin_out(review)


class AdminReviewUpdate(BaseModel):
    author_name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    rating: Optional[int] = Field(default=None, ge=1, le=5)
    text: Optional[str] = Field(default=None, min_length=1, max_length=4000)
    source: Optional[str] = None
    source_url: Optional[str] = Field(default=None, max_length=512)
    tour_id: Optional[str] = Field(default=None, max_length=64)
    is_published: Optional[bool] = None

    @field_validator("source")
    @classmethod
    def _validate_source(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if v not in REVIEW_SOURCES:
            raise ValueError(f"source должен быть одним из: {', '.join(sorted(REVIEW_SOURCES))}")
        return v

    @field_validator("author_name", "text")
    @classmethod
    def _strip_and_check(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        return _no_unsafe_chars(v.strip())

    @field_validator("source_url")
    @classmethod
    def _validate_source_url(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v == "":
            return v
        return validate_http_url(v, field_name="source_url")


@router.patch("/reviews/{review_id}", response_model=AdminReviewOut, summary="Изменить / одобрить / отклонить отзыв")
async def update_review_admin(
    review_id: int,
    data: AdminReviewUpdate,
    request: Request,
    admin: User = Depends(require_staff),
    session: AsyncSession = Depends(get_session),
) -> AdminReviewOut:
    review = await session.get(Review, review_id)
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Отзыв не найден")

    changed = data.model_dump(exclude_unset=True)
    if "tour_id" in changed and changed["tour_id"] and not await session.get(Tour, changed["tour_id"]):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Тур не найден")

    was_published = review.is_published
    for field, value in changed.items():
        setattr(review, field, value)
    await session.commit()
    await session.refresh(review, attribute_names=["tour"])

    if not was_published and review.is_published:
        action, details = "review.approve", f"Одобрен отзыв от «{review.author_name}»"
    else:
        action, details = "review.update", f"Изменён отзыв от «{review.author_name}»"
    await log_admin_action(
        session, admin, action=action, target_type="review", target_id=review.id,
        details=details, request=request,
    )
    return _to_admin_out(review)


@router.delete("/reviews/{review_id}", status_code=204, summary="Удалить отзыв")
async def delete_review_admin(
    review_id: int,
    request: Request,
    admin: User = Depends(require_staff),
    session: AsyncSession = Depends(get_session),
) -> None:
    review = await session.get(Review, review_id)
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Отзыв не найден")
    author = review.author_name
    await session.delete(review)
    await session.commit()
    await log_admin_action(
        session, admin, action="review.delete", target_type="review", target_id=review_id,
        details=f"Удалён отзыв от «{author}»", request=request,
    )
