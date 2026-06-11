from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_active_user
from app.db.session import get_session
from app.models.user import User
from app.schemas.schemas import NotificationOut
from app.services.notification_service import (
    get_notifications,
    mark_all_read,
    mark_read,
    record_cookie_consent,
)

router = APIRouter()


@router.get(
    "",
    response_model=list[NotificationOut],
    summary="Мои уведомления",
)
async def list_notifications(
    unread_only: bool = Query(False, description="Только непрочитанные"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> list[NotificationOut]:
    return await get_notifications(user, session, unread_only=unread_only, limit=limit, offset=offset)


@router.post(
    "/{notification_id}/read",
    response_model=NotificationOut,
    summary="Прочитать уведомление",
)
async def read_notification(
    notification_id: int,
    user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> NotificationOut:
    return await mark_read(notification_id, user, session)


@router.post(
    "/read-all",
    summary="Прочитать все уведомления",
)
async def read_all(
    user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    return await mark_all_read(user, session)


@router.post(
    "/cookie-consent",
    response_model=NotificationOut,
    status_code=201,
    summary="Зафиксировать принятие Cookie-политики",
    responses={409: {"description": "Согласие уже зафиксировано"}},
)
async def cookie_consent(
    user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> NotificationOut:
    return await record_cookie_consent(user, session)
