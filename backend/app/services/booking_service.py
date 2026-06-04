"""
Сервис бронирований.

Улучшения:
  - Атомарная проверка занятости даты + добавление — всё в одной транзакции
  - selectinload заменён на joinedload там, где нужна одна JOIN-SQL (1 запрос вместо N+1)
  - Добавлена функция get_booking_by_id с проверкой принадлежности пользователю
  - Добавлена cancel_booking — отмена бронирования
  - tour.booked_dates обновляется только если дата реально новая (idempotent)

BUG FIX (race condition):
  - Добавлен SELECT ... WITH FOR UPDATE через with_for_update() для PostgreSQL
    чтобы предотвратить двойное бронирование одной даты при конкурентных запросах.
  - Для SQLite это не критично (однопоточный движок), но безопасно включать везде.
"""
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.booking import Booking
from app.models.tour import Tour
from app.models.user import User
from app.schemas.schemas import BookingCreate, BookingOut


# ── Фабрика DTO ────────────────────────────────────────────────────────────────

def _booking_to_out(booking: Booking) -> BookingOut:
    """Конвертирует ORM-объект в схему ответа."""
    return BookingOut(
        id=booking.id,
        tour_id=booking.tour_id,
        tour_name=booking.tour.name if booking.tour else "—",
        tour_date=booking.tour_date,
        people_count=booking.people_count,
        status=booking.status,
        created_at=booking.created_at,
    )


# ── Публичные функции ──────────────────────────────────────────────────────────

async def create_booking(
    data: BookingCreate, user: User, session: AsyncSession
) -> BookingOut:
    """
    Создаёт бронирование.
    Проверяет существование тура и доступность даты.
    Обновляет список занятых дат атомарно внутри одной транзакции.

    BUG FIX: with_for_update() блокирует строку тура на время транзакции,
    предотвращая race condition при одновременных бронированиях одной даты.
    """
    # BUG FIX: with_for_update() — исключаем race condition
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
        user_id=user.id,
        tour_id=data.tour_id,
        first_name=data.first_name,
        phone=data.phone,
        email=data.email,
        tour_date=data.tour_date,
        preferred_time=data.preferred_time,
        people_count=data.people_count,
        comment=data.comment,
        status="booked",
    )
    session.add(booking)

    # Idempotent-обновление занятых дат
    dates = tour.booked_dates_list
    if data.tour_date not in dates:
        dates.append(data.tour_date)
        tour.booked_dates = ",".join(sorted(dates))

    # flush присваивает booking.id до commit — нужен для refresh
    await session.flush()
    await session.refresh(booking)
    await session.commit()

    # Подгружаем tour для имени (уже в identity map — нет доп. запроса)
    await session.refresh(tour)

    return _booking_to_out(booking)


async def get_my_bookings(user: User, session: AsyncSession) -> list[BookingOut]:
    """
    Возвращает все бронирования пользователя.
    joinedload — один SQL с JOIN вместо N+1 запросов к tours.
    """
    result = await session.execute(
        select(Booking)
        .where(Booking.user_id == user.id)
        .options(joinedload(Booking.tour))  # ← один JOIN-запрос
        .order_by(Booking.created_at.desc())
    )
    # unique() нужен при joinedload для корректной дедупликации строк
    bookings = result.unique().scalars().all()

    return [_booking_to_out(b) for b in bookings]


async def get_booking_by_id(
    booking_id: int, user: User, session: AsyncSession
) -> BookingOut:
    """
    Возвращает конкретное бронирование.
    Проверяет, что оно принадлежит текущему пользователю.
    """
    result = await session.execute(
        select(Booking)
        .where(Booking.id == booking_id)
        .options(joinedload(Booking.tour))
    )
    booking = result.unique().scalar_one_or_none()

    if booking is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Бронирование не найдено")

    if booking.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет доступа к этому бронированию",
        )

    return _booking_to_out(booking)


async def cancel_booking(
    booking_id: int, user: User, session: AsyncSession
) -> BookingOut:
    """
    Отменяет бронирование (status → 'cancelled').
    Не удаляет запись — сохраняем историю.
    """
    result = await session.execute(
        select(Booking)
        .where(Booking.id == booking_id)
        .options(joinedload(Booking.tour))
    )
    booking = result.unique().scalar_one_or_none()

    if booking is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Бронирование не найдено")

    if booking.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет доступа")

    if booking.status == "cancelled":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Бронирование уже отменено",
        )

    booking.status = "cancelled"
    await session.commit()
    await session.refresh(booking)

    return _booking_to_out(booking)
