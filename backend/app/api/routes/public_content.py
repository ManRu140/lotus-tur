"""Public, unauthenticated read endpoints.

These are what make the admin panel's content/banner/settings management
actually *do* something on the live site, rather than being admin-only
CRUD that nothing else ever reads. No auth required — this is exactly
the data a page's `<head>`/footer/homepage would fetch on every visit.
"""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.models.content import Banner, ContentBlock
from app.models.site_settings import SETTINGS_SINGLETON_ID, SiteSettings

router = APIRouter()


class PublicContentOut(BaseModel):
    key: str
    title: str
    body: str

    model_config = {"from_attributes": True}


@router.get("/content/{key}", response_model=PublicContentOut, summary="Опубликованный блок/страница")
async def get_public_content(key: str, session: AsyncSession = Depends(get_session)) -> PublicContentOut:
    block = (
        await session.execute(
            select(ContentBlock).where(ContentBlock.key == key, ContentBlock.is_published.is_(True))
        )
    ).scalar_one_or_none()
    if not block:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Не найдено")
    return block


class PublicBannerOut(BaseModel):
    id: int
    title: str
    subtitle: Optional[str]
    image_url: str
    link_url: Optional[str]

    model_config = {"from_attributes": True}


@router.get("/banners", response_model=list[PublicBannerOut], summary="Активные баннеры")
async def get_public_banners(session: AsyncSession = Depends(get_session)) -> list[PublicBannerOut]:
    now = datetime.now(timezone.utc)
    rows = (
        await session.execute(
            select(Banner)
            .where(
                Banner.is_active.is_(True),
                or_(Banner.starts_at.is_(None), Banner.starts_at <= now),
                or_(Banner.ends_at.is_(None), Banner.ends_at >= now),
            )
            .order_by(Banner.sort_order, Banner.id)
        )
    ).scalars().all()
    return list(rows)


class PublicSettingsOut(BaseModel):
    seo_title: str
    seo_description: str
    contact_phone: str
    contact_email: str
    contact_address: str
    vk_url: str
    telegram_url: str
    logo_url: str
    maintenance_mode: bool
    maintenance_message: str

    model_config = {"from_attributes": True}


@router.get("/settings", response_model=PublicSettingsOut, summary="Публичные настройки сайта")
async def get_public_settings(session: AsyncSession = Depends(get_session)) -> PublicSettingsOut:
    settings_row = await session.get(SiteSettings, SETTINGS_SINGLETON_ID)
    if settings_row is None:
        # No admin has saved settings yet — return safe defaults rather
        # than a 404, since the public frontend always needs *something*
        # to render in <title>/footer.
        settings_row = SiteSettings(id=SETTINGS_SINGLETON_ID)
    return settings_row
