"""
API роутер: бронирования (защищённые эндпоинты).

Новые эндпоинты:
  - GET  /my/{booking_id}       — детали одного бронирования
  - POST /my/{booking_id}/cancel — отмена бронирования
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_active_user
from app.db.session import get_session
from app.models.user import User
from app.schemas.schemas import BookingCreate, BookingOut
from app.services.booking_service import (
    cancel_booking,
    create_booking,
    get_booking_by_id,
    get_my_bookings,
)

router = APIRouter()


@router.post(
    "",
    response_model=BookingOut,
    status_code=201,
    summary="Создать бронирование",
    responses={
        409: {"description": "Дата занята"},
        404: {"description": "Тур не найден"},
    },
)
async def book_tour(
    data: BookingCreate,
    user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> BookingOut:
    return await create_booking(data, user, session)


@router.get(
    "/my",
    response_model=list[BookingOut],
    summary="Мои бронирования",
)
async def my_bookings(
    user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> list[BookingOut]:
    return await get_my_bookings(user, session)


@router.get(
    "/my/{booking_id}",
    response_model=BookingOut,
    summary="Детали бронирования",
    responses={
        403: {"description": "Нет доступа"},
        404: {"description": "Не найдено"},
    },
)
async def get_booking(
    booking_id: int,
    user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> BookingOut:
    return await get_booking_by_id(booking_id, user, session)


@router.post(
    "/my/{booking_id}/cancel",
    response_model=BookingOut,
    summary="Отменить бронирование",
    responses={
        403: {"description": "Нет доступа"},
        404: {"description": "Не найдено"},
        409: {"description": "Уже отменено"},
    },
)
async def cancel_booking_route(
    booking_id: int,
    user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> BookingOut:
    return await cancel_booking(booking_id, user, session)
