from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.deps import require_admin
from app.db.session import get_session
from app.models.booking import Booking
from app.models.tour import Tour
from app.models.user import User

router = APIRouter()


class AdminUserOut(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str]
    is_active: bool
    is_admin: bool
    is_oauth: bool
    created_at: datetime
    bookings_count: int = 0

    model_config = {"from_attributes": True}


class AdminBookingOut(BaseModel):
    id: int
    user_id: int
    username: str
    tour_id: str
    tour_name: str
    first_name: str
    phone: str
    email: str
    tour_date: str
    people_count: int
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class AdminTourOut(BaseModel):
    id: str
    tag: str
    name: str
    description: str
    price: int
    img_url: str
    bookings_count: int = 0

    model_config = {"from_attributes": True}


class AdminTourCreate(BaseModel):
    id: str
    tag: str
    name: str
    description: str
    price: int
    img_url: str


class AdminTourUpdate(BaseModel):
    tag: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[int] = None
    img_url: Optional[str] = None


class AdminStatsOut(BaseModel):
    total_users: int
    active_users: int
    total_bookings: int
    active_bookings: int
    cancelled_bookings: int
    total_tours: int
    revenue_estimate: int


class UserToggleAdminRequest(BaseModel):
    is_admin: bool


class UserToggleActiveRequest(BaseModel):
    is_active: bool


class BookingStatusUpdate(BaseModel):
    status: str


def _build_user_out(user: User, bookings_count: int) -> AdminUserOut:
    return AdminUserOut(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        is_admin=user.is_admin,
        is_oauth=user.is_oauth,
        created_at=user.created_at,
        bookings_count=bookings_count,
    )


@router.get("/stats", response_model=AdminStatsOut, summary="Общая статистика")
async def get_stats(
    _: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> AdminStatsOut:
    """Возвращает ключевые метрики одним составным запросом."""
    user_stats = await session.execute(
        select(
            func.count(User.id).label("total"),
            func.sum(case((User.is_active == True, 1), else_=0)).label("active"),
        )
    )
    u = user_stats.one()

    booking_stats = await session.execute(
        select(
            func.count(Booking.id).label("total"),
            func.sum(case((Booking.status == "booked", 1), else_=0)).label("active"),
            func.sum(case((Booking.status == "cancelled", 1), else_=0)).label("cancelled"),
        )
    )
    b = booking_stats.one()

    total_tours = (await session.execute(select(func.count(Tour.id)))).scalar_one()

    revenue_result = await session.execute(
        select(func.sum(Tour.price * Booking.people_count))
        .join(Booking, Tour.id == Booking.tour_id)
        .where(Booking.status != "cancelled")
    )
    revenue = revenue_result.scalar_one() or 0

    return AdminStatsOut(
        total_users=u.total or 0,
        active_users=u.active or 0,
        total_bookings=b.total or 0,
        active_bookings=b.active or 0,
        cancelled_bookings=b.cancelled or 0,
        total_tours=total_tours,
        revenue_estimate=revenue,
    )


@router.get("/users", response_model=list[AdminUserOut], summary="Список пользователей")
async def list_users(
    search: Optional[str] = Query(None, description="Поиск по имени или email"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    _: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> list[AdminUserOut]:
    """Список пользователей с числом бронирований — без N+1 запросов."""
    counts_sq = (
        select(Booking.user_id, func.count(Booking.id).label("cnt"))
        .group_by(Booking.user_id)
        .subquery()
    )

    q = select(User, func.coalesce(counts_sq.c.cnt, 0).label("bookings_count")).outerjoin(
        counts_sq, User.id == counts_sq.c.user_id
    )

    if search:
        term = f"%{search}%"
        q = q.where(User.username.ilike(term) | User.email.ilike(term))

    q = q.order_by(User.created_at.desc()).limit(limit).offset(offset)
    rows = (await session.execute(q)).all()

    return [_build_user_out(user, cnt) for user, cnt in rows]


@router.patch(
    "/users/{user_id}/toggle-active",
    response_model=AdminUserOut,
    summary="Активировать / деактивировать пользователя",
)
async def toggle_user_active(
    user_id: int,
    data: UserToggleActiveRequest,
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> AdminUserOut:
    if user_id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя деактивировать себя",
        )
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
    user.is_active = data.is_active
    await session.commit()
    await session.refresh(user)
    cnt = (
        await session.execute(select(func.count(Booking.id)).where(Booking.user_id == user.id))
    ).scalar_one()
    return _build_user_out(user, cnt)


@router.patch(
    "/users/{user_id}/toggle-admin",
    response_model=AdminUserOut,
    summary="Выдать / отозвать права администратора",
)
async def toggle_user_admin(
    user_id: int,
    data: UserToggleAdminRequest,
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> AdminUserOut:
    if user_id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя изменить собственные права",
        )
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
    user.is_admin = data.is_admin
    await session.commit()
    await session.refresh(user)
    cnt = (
        await session.execute(select(func.count(Booking.id)).where(Booking.user_id == user.id))
    ).scalar_one()
    return _build_user_out(user, cnt)


@router.get("/bookings", response_model=list[AdminBookingOut], summary="Все бронирования")
async def list_bookings(
    status_filter: Optional[str] = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    _: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> list[AdminBookingOut]:
    q = (
        select(Booking)
        .options(joinedload(Booking.tour), joinedload(Booking.user))
        .order_by(Booking.created_at.desc())
    )
    if status_filter:
        q = q.where(Booking.status == status_filter)
    q = q.limit(limit).offset(offset)
    bookings = (await session.execute(q)).unique().scalars().all()

    return [
        AdminBookingOut(
            id=b.id,
            user_id=b.user_id,
            username=b.user.username if b.user else "—",
            tour_id=b.tour_id,
            tour_name=b.tour.name if b.tour else "—",
            first_name=b.first_name,
            phone=b.phone,
            email=b.email,
            tour_date=b.tour_date,
            people_count=b.people_count,
            status=b.status,
            created_at=b.created_at,
        )
        for b in bookings
    ]


@router.patch(
    "/bookings/{booking_id}/status",
    response_model=AdminBookingOut,
    summary="Изменить статус бронирования",
)
async def update_booking_status(
    booking_id: int,
    data: BookingStatusUpdate,
    _: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> AdminBookingOut:
    allowed = {"booked", "started", "completed", "cancelled"}
    if data.status not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Допустимые статусы: {', '.join(sorted(allowed))}",
        )
    result = await session.execute(
        select(Booking)
        .where(Booking.id == booking_id)
        .options(joinedload(Booking.tour), joinedload(Booking.user))
    )
    booking = result.unique().scalar_one_or_none()
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Бронирование не найдено")

    booking.status = data.status
    await session.commit()
    await session.refresh(booking)
    return AdminBookingOut(
        id=booking.id,
        user_id=booking.user_id,
        username=booking.user.username if booking.user else "—",
        tour_id=booking.tour_id,
        tour_name=booking.tour.name if booking.tour else "—",
        first_name=booking.first_name,
        phone=booking.phone,
        email=booking.email,
        tour_date=booking.tour_date,
        people_count=booking.people_count,
        status=booking.status,
        created_at=booking.created_at,
    )


@router.get("/tours", response_model=list[AdminTourOut], summary="Все туры (с кол-вом бронирований)")
async def list_tours_admin(
    _: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> list[AdminTourOut]:
    """Туры с агрегированным счётчиком активных броней — без N+1 запросов."""
    counts_sq = (
        select(Booking.tour_id, func.count(Booking.id).label("cnt"))
        .where(Booking.status != "cancelled")
        .group_by(Booking.tour_id)
        .subquery()
    )
    rows = (
        await session.execute(
            select(Tour, func.coalesce(counts_sq.c.cnt, 0).label("bookings_count")).outerjoin(
                counts_sq, Tour.id == counts_sq.c.tour_id
            )
        )
    ).all()

    return [
        AdminTourOut(
            id=t.id,
            tag=t.tag,
            name=t.name,
            description=t.description,
            price=t.price,
            img_url=t.img_url,
            bookings_count=cnt,
        )
        for t, cnt in rows
    ]


@router.post("/tours", response_model=AdminTourOut, status_code=201, summary="Создать тур")
async def create_tour(
    data: AdminTourCreate,
    _: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> AdminTourOut:
    if await session.get(Tour, data.id):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Тур с таким ID уже существует")
    tour = Tour(
        id=data.id,
        tag=data.tag,
        name=data.name,
        description=data.description,
        price=data.price,
        img_url=data.img_url,
    )
    session.add(tour)
    await session.commit()
    await session.refresh(tour)
    return AdminTourOut(
        id=tour.id,
        tag=tour.tag,
        name=tour.name,
        description=tour.description,
        price=tour.price,
        img_url=tour.img_url,
        bookings_count=0,
    )


@router.patch("/tours/{tour_id}", response_model=AdminTourOut, summary="Обновить тур")
async def update_tour(
    tour_id: str,
    data: AdminTourUpdate,
    _: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> AdminTourOut:
    tour = await session.get(Tour, tour_id)
    if not tour:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Тур не найден")
    if data.tag is not None:
        tour.tag = data.tag
    if data.name is not None:
        tour.name = data.name
    if data.description is not None:
        tour.description = data.description
    if data.price is not None:
        tour.price = data.price
    if data.img_url is not None:
        tour.img_url = data.img_url
    await session.commit()
    await session.refresh(tour)
    cnt = (
        await session.execute(
            select(func.count(Booking.id)).where(
                Booking.tour_id == tour.id, Booking.status != "cancelled"
            )
        )
    ).scalar_one()
    return AdminTourOut(
        id=tour.id,
        tag=tour.tag,
        name=tour.name,
        description=tour.description,
        price=tour.price,
        img_url=tour.img_url,
        bookings_count=cnt,
    )


@router.delete("/tours/{tour_id}", status_code=204, summary="Удалить тур")
async def delete_tour(
    tour_id: str,
    _: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> None:
    tour = await session.get(Tour, tour_id)
    if not tour:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Тур не найден")
    await session.delete(tour)
    await session.commit()
