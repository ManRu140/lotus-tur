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
    """
    result = await session.execute(
        select(Tour).where(Tour.id == data.tour_id).with_for_update()
    )
    tour = result.scalar_one_or_none()

    if not tour:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Тур не найден")

    if data.tour_date in tour.booked_dates_list:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Выбранная дата полностью занята, выберите другую")

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

    await session.flush()
    await session.refresh(booking)
    await session.commit()
    await session.refresh(tour)

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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Бронирование не найдено")
    if booking.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет доступа к этому бронированию")

    return _booking_to_out(booking)


async def cancel_booking(booking_id: int, user: User, session: AsyncSession) -> BookingOut:
    """Меняет статус на 'cancelled', не удаляет запись."""
    result = await session.execute(
        select(Booking).where(Booking.id == booking_id).options(joinedload(Booking.tour))
    )
    booking = result.unique().scalar_one_or_none()

    if booking is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Бронирование не найдено")
    if booking.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет доступа")
    if booking.status == "cancelled":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Бронирование уже отменено")

    booking.status = "cancelled"
    await session.commit()
    await session.refresh(booking)

    return _booking_to_out(booking)
