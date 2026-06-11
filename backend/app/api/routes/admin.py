from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import func, select, update
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


@router.get("/stats", response_model=AdminStatsOut, summary="Общая статистика")
async def get_stats(
    _: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> AdminStatsOut:
    total_users = (await session.execute(select(func.count(User.id)))).scalar_one()
    active_users = (await session.execute(select(func.count(User.id)).where(User.is_active == True))).scalar_one()
    total_bookings = (await session.execute(select(func.count(Booking.id)))).scalar_one()
    active_bookings = (await session.execute(
        select(func.count(Booking.id)).where(Booking.status == "booked")
    )).scalar_one()
    cancelled_bookings = (await session.execute(
        select(func.count(Booking.id)).where(Booking.status == "cancelled")
    )).scalar_one()
    total_tours = (await session.execute(select(func.count(Tour.id)))).scalar_one()


    revenue_result = await session.execute(
        select(func.sum(Tour.price * Booking.people_count))
        .join(Booking, Tour.id == Booking.tour_id)
        .where(Booking.status != "cancelled")
    )
    revenue = revenue_result.scalar_one() or 0

    return AdminStatsOut(
        total_users=total_users,
        active_users=active_users,
        total_bookings=total_bookings,
        active_bookings=active_bookings,
        cancelled_bookings=cancelled_bookings,
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
    q = select(User)
    if search:
        term = f"%{search}%"
        q = q.where(User.username.ilike(term) | User.email.ilike(term))
    q = q.order_by(User.created_at.desc()).limit(limit).offset(offset)
    result = await session.execute(q)
    users = result.scalars().all()

    out = []
    for u in users:
        count_result = await session.execute(
            select(func.count(Booking.id)).where(Booking.user_id == u.id)
        )
        bookings_count = count_result.scalar_one()
        out.append(AdminUserOut(
            id=u.id, username=u.username, email=u.email,
            full_name=u.full_name, is_active=u.is_active,
            is_admin=u.is_admin, is_oauth=u.is_oauth,
            created_at=u.created_at, bookings_count=bookings_count,
        ))
    return out


@router.patch("/users/{user_id}/toggle-active", response_model=AdminUserOut, summary="Активировать / деактивировать пользователя")
async def toggle_user_active(
    user_id: int,
    data: UserToggleActiveRequest,
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> AdminUserOut:
    if user_id == admin.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Нельзя деактивировать себя")
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
    user.is_active = data.is_active
    await session.commit()
    await session.refresh(user)
    count_result = await session.execute(select(func.count(Booking.id)).where(Booking.user_id == user.id))
    return AdminUserOut(
        id=user.id, username=user.username, email=user.email,
        full_name=user.full_name, is_active=user.is_active,
        is_admin=user.is_admin, is_oauth=user.is_oauth,
        created_at=user.created_at, bookings_count=count_result.scalar_one(),
    )


@router.patch("/users/{user_id}/toggle-admin", response_model=AdminUserOut, summary="Выдать / отозвать права администратора")
async def toggle_user_admin(
    user_id: int,
    data: UserToggleAdminRequest,
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> AdminUserOut:
    if user_id == admin.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Нельзя изменить собственные права")
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
    user.is_admin = data.is_admin
    await session.commit()
    await session.refresh(user)
    count_result = await session.execute(select(func.count(Booking.id)).where(Booking.user_id == user.id))
    return AdminUserOut(
        id=user.id, username=user.username, email=user.email,
        full_name=user.full_name, is_active=user.is_active,
        is_admin=user.is_admin, is_oauth=user.is_oauth,
        created_at=user.created_at, bookings_count=count_result.scalar_one(),
    )


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
    result = await session.execute(q)
    bookings = result.unique().scalars().all()

    return [
        AdminBookingOut(
            id=b.id, user_id=b.user_id,
            username=b.user.username if b.user else "—",
            tour_id=b.tour_id,
            tour_name=b.tour.name if b.tour else "—",
            first_name=b.first_name, phone=b.phone, email=b.email,
            tour_date=b.tour_date, people_count=b.people_count,
            status=b.status, created_at=b.created_at,
        )
        for b in bookings
    ]


@router.patch("/bookings/{booking_id}/status", response_model=AdminBookingOut, summary="Изменить статус бронирования")
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
            detail=f"Допустимые статусы: {', '.join(allowed)}"
        )
    result = await session.execute(
        select(Booking).where(Booking.id == booking_id)
        .options(joinedload(Booking.tour), joinedload(Booking.user))
    )
    booking = result.unique().scalar_one_or_none()
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Бронирование не найдено")
    booking.status = data.status
    await session.commit()
    await session.refresh(booking)
    return AdminBookingOut(
        id=booking.id, user_id=booking.user_id,
        username=booking.user.username if booking.user else "—",
        tour_id=booking.tour_id,
        tour_name=booking.tour.name if booking.tour else "—",
        first_name=booking.first_name, phone=booking.phone, email=booking.email,
        tour_date=booking.tour_date, people_count=booking.people_count,
        status=booking.status, created_at=booking.created_at,
    )


@router.get("/tours", response_model=list[AdminTourOut], summary="Все туры (с кол-вом бронирований)")
async def list_tours_admin(
    _: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> list[AdminTourOut]:
    result = await session.execute(select(Tour))
    tours = result.scalars().all()
    out = []
    for t in tours:
        count_result = await session.execute(
            select(func.count(Booking.id)).where(Booking.tour_id == t.id, Booking.status != "cancelled")
        )
        out.append(AdminTourOut(
            id=t.id, tag=t.tag, name=t.name, description=t.description,
            price=t.price, img_url=t.img_url, bookings_count=count_result.scalar_one(),
        ))
    return out


@router.post("/tours", response_model=AdminTourOut, status_code=201, summary="Создать тур")
async def create_tour(
    data: AdminTourCreate,
    _: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> AdminTourOut:
    existing = await session.get(Tour, data.id)
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Тур с таким ID уже существует")
    tour = Tour(
        id=data.id, tag=data.tag, name=data.name,
        description=data.description, price=data.price, img_url=data.img_url,
    )
    session.add(tour)
    await session.commit()
    await session.refresh(tour)
    return AdminTourOut(id=tour.id, tag=tour.tag, name=tour.name,
                        description=tour.description, price=tour.price,
                        img_url=tour.img_url, bookings_count=0)


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
    if data.tag is not None: tour.tag = data.tag
    if data.name is not None: tour.name = data.name
    if data.description is not None: tour.description = data.description
    if data.price is not None: tour.price = data.price
    if data.img_url is not None: tour.img_url = data.img_url
    await session.commit()
    await session.refresh(tour)
    count_result = await session.execute(
        select(func.count(Booking.id)).where(Booking.tour_id == tour.id, Booking.status != "cancelled")
    )
    return AdminTourOut(id=tour.id, tag=tour.tag, name=tour.name,
                        description=tour.description, price=tour.price,
                        img_url=tour.img_url, bookings_count=count_result.scalar_one())


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
