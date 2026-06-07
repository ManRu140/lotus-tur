"""
booking_service.py — ИСПРАВЛЕННАЯ ВЕРСИЯ
Изменения:
  [FIX-1] create_booking: убран лишний flush+refresh до commit
  [FIX-2] cancel_booking: при отмене дата удаляется из tour.booked_dates
           если нет других активных бронирований на эту дату
"""
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.booking import Booking
from app.models.tour import Tour
from app.models.user import User
from app.schemas.schemas import BookingCreate, BookingOut


def _booking_to_out(booking: Booking) -> BookingOut:
    return BookingOut(
        id=booking.id,
        tour_id=booking.tour_id,
        tour_name=booking.tour.name if booking.tour else "—",
        tour_date=booking.tour_date,
        people_count=booking.people_count,
        status=booking.status,
        created_at=booking.created_at,
    )


async def create_booking(data: BookingCreate, user: User, session: AsyncSession) -> BookingOut:
    """
    with_for_update() блокирует строку тура на время транзакции —
    предотвращает race condition при одновременных бронированиях одной даты.
    [FIX-1] Убран лишний flush()+refresh() до commit — одна транзакция, один commit.
    """
    result = await session.execute(
        select(Tour).where(Tour.id == data.tour_id).with_for_update()
    )
    tour = result.scalar_one_or_none()

    if not tour:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Тур не найден",
        )

    if data.tour_date in tour.booked_dates_list:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Выбранная дата полностью занята, выберите другую",
        )

    booking = Booking(
        user_id=user.id, tour_id=data.tour_id,
        first_name=data.first_name, phone=data.phone, email=data.email,
        tour_date=data.tour_date, preferred_time=data.preferred_time,
        people_count=data.people_count, comment=data.comment,
        status="booked",
    )
    session.add(booking)

    # Idempotent-обновление занятых дат
    dates = tour.booked_dates_list
    if data.tour_date not in dates:
        dates.append(data.tour_date)
        tour.booked_dates = ",".join(sorted(dates))

    # [FIX-1] Один commit вместо flush+commit+двойной refresh
    await session.commit()
    await session.refresh(booking)

    return _booking_to_out(booking)


async def get_my_bookings(user: User, session: AsyncSession) -> list[BookingOut]:
    """joinedload — один SQL с JOIN вместо N+1 запросов."""
    result = await session.execute(
        select(Booking)
        .where(Booking.user_id == user.id)
        .options(joinedload(Booking.tour))
        .order_by(Booking.created_at.desc())
    )
    bookings = result.unique().scalars().all()
    return [_booking_to_out(b) for b in bookings]


async def get_booking_by_id(booking_id: int, user: User, session: AsyncSession) -> BookingOut:
    result = await session.execute(
        select(Booking).where(Booking.id == booking_id).options(joinedload(Booking.tour))
    )
    booking = result.unique().scalar_one_or_none()

    if booking is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Бронирование не найдено",
        )
    if booking.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет доступа к этому бронированию",
        )

    return _booking_to_out(booking)


async def cancel_booking(booking_id: int, user: User, session: AsyncSession) -> BookingOut:
    """
    Меняет статус на 'cancelled', не удаляет запись.
    [FIX-2] При отмене проверяет, остались ли другие активные бронирования
    на ту же дату. Если нет — удаляет дату из tour.booked_dates,
    освобождая слот для других пользователей.
    """
    result = await session.execute(
        select(Booking).where(Booking.id == booking_id).options(joinedload(Booking.tour))
    )
    booking = result.unique().scalar_one_or_none()

    if booking is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Бронирование не найдено",
        )
    if booking.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет доступа",
        )
    if booking.status == "cancelled":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Бронирование уже отменено",
        )

    booking.status = "cancelled"

    # [FIX-2] Освобождаем дату, если нет других активных бронирований на неё
    other_active = await session.execute(
        select(Booking.id).where(
            Booking.tour_id == booking.tour_id,
            Booking.tour_date == booking.tour_date,
            Booking.status != "cancelled",
            Booking.id != booking.id,
        )
    )
    if other_active.scalar_one_or_none() is None and booking.tour:
        freed_date = booking.tour_date
        remaining_dates = [d for d in booking.tour.booked_dates_list if d != freed_date]
        booking.tour.booked_dates = ",".join(sorted(remaining_dates)) or None

    await session.commit()
    await session.refresh(booking)

    return _booking_to_out(booking)
