"""Admin endpoints for the single site-wide settings row.

GET is also exposed publicly (see app/api/routes/public_content.py) so
the live site can actually read SEO tags / contacts / logo / maintenance
state — a settings panel that nothing reads is not a real feature.
"""

import re
from typing import Optional

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_admin
from app.core.validators import validate_http_url
from app.db.session import get_session
from app.models.site_settings import SETTINGS_SINGLETON_ID, SiteSettings
from app.models.user import User
from app.services.audit_service import log_admin_action

router = APIRouter()


async def get_or_create_settings(session: AsyncSession) -> SiteSettings:
    settings_row = await session.get(SiteSettings, SETTINGS_SINGLETON_ID)
    if settings_row is None:
        settings_row = SiteSettings(id=SETTINGS_SINGLETON_ID)
        session.add(settings_row)
        await session.commit()
        await session.refresh(settings_row)
    return settings_row


class SiteSettingsOut(BaseModel):
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


class SiteSettingsUpdate(BaseModel):
    seo_title: Optional[str] = Field(default=None, max_length=70)
    seo_description: Optional[str] = Field(default=None, max_length=200)
    contact_phone: Optional[str] = Field(default=None, max_length=32)
    contact_email: Optional[str] = Field(default=None, max_length=128)
    contact_address: Optional[str] = Field(default=None, max_length=256)
    vk_url: Optional[str] = Field(default=None, max_length=256)
    telegram_url: Optional[str] = Field(default=None, max_length=256)
    logo_url: Optional[str] = Field(default=None, max_length=512)
    maintenance_mode: Optional[bool] = None
    maintenance_message: Optional[str] = Field(default=None, max_length=2000)

    @field_validator(
        "seo_title", "seo_description", "contact_phone", "contact_email",
        "contact_address", "maintenance_message",
    )
    @classmethod
    def _no_unsafe_chars(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        if re.search(r"[<>]", v):
            raise ValueError("Поле не должно содержать символы < >")
        return v

    @field_validator("vk_url", "telegram_url", "logo_url")
    @classmethod
    def _validate_optional_url(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v == "":
            return v
        return validate_http_url(v, field_name="URL")


@router.get("/settings", response_model=SiteSettingsOut, summary="Текущие настройки сайта")
async def get_settings(
    _: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> SiteSettingsOut:
    return await get_or_create_settings(session)


@router.patch("/settings", response_model=SiteSettingsOut, summary="Обновить настройки сайта")
async def update_settings(
    data: SiteSettingsUpdate,
    request: Request,
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> SiteSettingsOut:
    settings_row = await get_or_create_settings(session)
    changed_fields = data.model_dump(exclude_unset=True)
    for field, value in changed_fields.items():
        setattr(settings_row, field, value)
    settings_row.updated_by_id = admin.id

    await session.commit()
    await session.refresh(settings_row)
    await log_admin_action(
        session, admin, action="settings.update", target_type="settings",
        target_id="site", details=f"Изменены поля: {', '.join(changed_fields.keys())}",
        request=request,
    )
    return settings_row
