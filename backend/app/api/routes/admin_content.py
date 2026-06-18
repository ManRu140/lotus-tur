"""Admin CRUD for site content: text blocks/pages, and banners.

Permission model follows the same pattern as admin.py / admin_media.py:
moderators (require_staff) can create and edit; only full admins
(require_admin) can delete. See app/core/deps.py for the two
dependencies.
"""

import re
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_admin, require_staff
from app.core.validators import validate_http_url
from app.db.session import get_session
from app.models.content import Banner, ContentBlock
from app.models.user import User
from app.services.audit_service import log_admin_action

router = APIRouter()

_KEY_PATTERN = r"^[a-z0-9_\-]+$"
_ALLOWED_BLOCK_TYPES = {"block", "page"}


def _no_unsafe_chars(v: str, field_name: str) -> str:
    # Same defence-in-depth rule as the Tour schemas in admin.py: the
    # admin UI escapes correctly now, but these characters have no
    # legitimate reason to appear in a title, and disallowing them here
    # closes off an entire class of "what if the frontend has a bug"
    # XSS — which matters far more here than for tours, because this
    # content gets rendered on the *public* site for every visitor.
    if re.search(r"[<>]", v):
        raise ValueError(f"{field_name} не должно содержать символы < >")
    return v


# ── Content blocks / pages ──────────────────────────────────────────

class ContentBlockOut(BaseModel):
    id: int
    key: str
    block_type: str
    title: str
    body: str
    is_published: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ContentBlockCreate(BaseModel):
    key: str = Field(min_length=1, max_length=96, pattern=_KEY_PATTERN)
    block_type: str = Field(default="block")
    title: str = Field(min_length=1, max_length=256)
    body: str = Field(default="", max_length=50_000)
    is_published: bool = True

    @field_validator("block_type")
    @classmethod
    def _validate_type(cls, v: str) -> str:
        if v not in _ALLOWED_BLOCK_TYPES:
            raise ValueError(f"block_type должен быть одним из: {', '.join(_ALLOWED_BLOCK_TYPES)}")
        return v

    @field_validator("title")
    @classmethod
    def _validate_title(cls, v: str) -> str:
        return _no_unsafe_chars(v.strip(), "title")


class ContentBlockUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=256)
    body: Optional[str] = Field(default=None, max_length=50_000)
    is_published: Optional[bool] = None

    @field_validator("title")
    @classmethod
    def _validate_title(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        return _no_unsafe_chars(v.strip(), "title")


@router.get("/content", response_model=list[ContentBlockOut], summary="Все блоки/страницы")
async def list_content(
    _: User = Depends(require_staff),
    session: AsyncSession = Depends(get_session),
) -> list[ContentBlockOut]:
    rows = (await session.execute(select(ContentBlock).order_by(ContentBlock.key))).scalars().all()
    return list(rows)


@router.post("/content", response_model=ContentBlockOut, status_code=201, summary="Создать блок/страницу")
async def create_content(
    data: ContentBlockCreate,
    request: Request,
    admin: User = Depends(require_staff),
    session: AsyncSession = Depends(get_session),
) -> ContentBlockOut:
    existing = (
        await session.execute(select(ContentBlock).where(ContentBlock.key == data.key))
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Такой key уже существует")

    block = ContentBlock(
        key=data.key, block_type=data.block_type, title=data.title,
        body=data.body, is_published=data.is_published, updated_by_id=admin.id,
    )
    session.add(block)
    await session.commit()
    await session.refresh(block)
    await log_admin_action(
        session, admin, action="content.create", target_type="content",
        target_id=block.key, details=f"Создан блок «{block.title}»", request=request,
    )
    return block


@router.patch("/content/{key}", response_model=ContentBlockOut, summary="Обновить блок/страницу")
async def update_content(
    key: str,
    data: ContentBlockUpdate,
    request: Request,
    admin: User = Depends(require_staff),
    session: AsyncSession = Depends(get_session),
) -> ContentBlockOut:
    block = (
        await session.execute(select(ContentBlock).where(ContentBlock.key == key))
    ).scalar_one_or_none()
    if not block:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Блок не найден")

    if data.title is not None:
        block.title = data.title
    if data.body is not None:
        block.body = data.body
    if data.is_published is not None:
        block.is_published = data.is_published
    block.updated_by_id = admin.id

    await session.commit()
    await session.refresh(block)
    await log_admin_action(
        session, admin, action="content.update", target_type="content",
        target_id=block.key, details=f"Обновлён блок «{block.title}»", request=request,
    )
    return block


@router.delete("/content/{key}", status_code=204, summary="Удалить блок/страницу")
async def delete_content(
    key: str,
    request: Request,
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> None:
    block = (
        await session.execute(select(ContentBlock).where(ContentBlock.key == key))
    ).scalar_one_or_none()
    if not block:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Блок не найден")
    title = block.title
    await session.delete(block)
    await session.commit()
    await log_admin_action(
        session, admin, action="content.delete", target_type="content",
        target_id=key, details=f"Удалён блок «{title}»", request=request,
    )


# ── Banners ──────────────────────────────────────────────────────────

class BannerOut(BaseModel):
    id: int
    title: str
    subtitle: Optional[str]
    image_url: str
    link_url: Optional[str]
    is_active: bool
    sort_order: int
    starts_at: Optional[datetime]
    ends_at: Optional[datetime]

    model_config = {"from_attributes": True}


class BannerCreate(BaseModel):
    title: str = Field(min_length=1, max_length=256)
    subtitle: Optional[str] = Field(default=None, max_length=512)
    image_url: str = Field(max_length=512)
    link_url: Optional[str] = Field(default=None, max_length=512)
    is_active: bool = True
    sort_order: int = Field(default=0, ge=0, le=10_000)
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None

    @field_validator("title", "subtitle")
    @classmethod
    def _validate_text(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        return _no_unsafe_chars(v.strip(), "Поле")

    @field_validator("image_url")
    @classmethod
    def _validate_image_url(cls, v: str) -> str:
        return validate_http_url(v, field_name="image_url")

    @field_validator("link_url")
    @classmethod
    def _validate_link_url(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v == "":
            return None
        return validate_http_url(v, field_name="link_url")


class BannerUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=256)
    subtitle: Optional[str] = Field(default=None, max_length=512)
    image_url: Optional[str] = Field(default=None, max_length=512)
    link_url: Optional[str] = Field(default=None, max_length=512)
    is_active: Optional[bool] = None
    sort_order: Optional[int] = Field(default=None, ge=0, le=10_000)
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None

    @field_validator("title", "subtitle")
    @classmethod
    def _validate_text(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        return _no_unsafe_chars(v.strip(), "Поле")

    @field_validator("image_url")
    @classmethod
    def _validate_image_url(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        return validate_http_url(v, field_name="image_url")

    @field_validator("link_url")
    @classmethod
    def _validate_link_url(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v == "":
            return v
        return validate_http_url(v, field_name="link_url")


@router.get("/banners", response_model=list[BannerOut], summary="Все баннеры")
async def list_banners(
    _: User = Depends(require_staff),
    session: AsyncSession = Depends(get_session),
) -> list[BannerOut]:
    rows = (
        await session.execute(select(Banner).order_by(Banner.sort_order, Banner.id))
    ).scalars().all()
    return list(rows)


@router.post("/banners", response_model=BannerOut, status_code=201, summary="Создать баннер")
async def create_banner(
    data: BannerCreate,
    request: Request,
    admin: User = Depends(require_staff),
    session: AsyncSession = Depends(get_session),
) -> BannerOut:
    banner = Banner(**data.model_dump())
    session.add(banner)
    await session.commit()
    await session.refresh(banner)
    await log_admin_action(
        session, admin, action="banner.create", target_type="banner",
        target_id=banner.id, details=f"Создан баннер «{banner.title}»", request=request,
    )
    return banner


@router.patch("/banners/{banner_id}", response_model=BannerOut, summary="Обновить баннер")
async def update_banner(
    banner_id: int,
    data: BannerUpdate,
    request: Request,
    admin: User = Depends(require_staff),
    session: AsyncSession = Depends(get_session),
) -> BannerOut:
    banner = await session.get(Banner, banner_id)
    if not banner:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Баннер не найден")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(banner, field, value)
    await session.commit()
    await session.refresh(banner)
    await log_admin_action(
        session, admin, action="banner.update", target_type="banner",
        target_id=banner.id, details=f"Обновлён баннер «{banner.title}»", request=request,
    )
    return banner


@router.delete("/banners/{banner_id}", status_code=204, summary="Удалить баннер")
async def delete_banner(
    banner_id: int,
    request: Request,
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> None:
    banner = await session.get(Banner, banner_id)
    if not banner:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Баннер не найден")
    title = banner.title
    await session.delete(banner)
    await session.commit()
    await log_admin_action(
        session, admin, action="banner.delete", target_type="banner",
        target_id=banner_id, details=f"Удалён баннер «{title}»", request=request,
    )
