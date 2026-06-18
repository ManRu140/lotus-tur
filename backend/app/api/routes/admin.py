import re
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.deps import require_admin, require_staff
from app.core.security import hash_password, validate_password_strength
from app.core.validators import SLUG_PATTERN, validate_http_url
from app.db.session import get_session
from app.models.booking import Booking
from app.models.tour import Tour
from app.models.user import User
from app.services.audit_service import log_admin_action

router = APIRouter()

ALLOWED_SCHEDULE_VALUES = {
    "Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье",
    "Ежедневно", "По запросу",
}


def _validate_schedule_value(v: str) -> str:
    v = (v or "").strip()
    if v not in ALLOWED_SCHEDULE_VALUES:
        raise ValueError(
            f"Расписание должно быть одним из: {', '.join(sorted(ALLOWED_SCHEDULE_VALUES))}"
        )
    return v


_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _validate_date_list(dates: list[str]) -> list[str]:
    if len(dates) > 500:
        raise ValueError("Слишком много дат")
    for d in dates:
        if not _DATE_RE.match(d):
            raise ValueError(f"Некорректный формат даты: {d!r} (ожидается YYYY-MM-DD)")
    return sorted(set(dates))


class AdminUserOut(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str]
    is_active: bool
    is_admin: bool
    role: str
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
    schedule: str
    booked_dates: list[str] = Field(default_factory=list)
    bookings_count: int = 0

    model_config = {"from_attributes": True}


class AdminTourCreate(BaseModel):
    id: str = Field(min_length=1, max_length=64, pattern=SLUG_PATTERN,
                     description="Только латиница/цифры/_/- (как slug)")
    tag: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=128)
    description: str = Field(min_length=1, max_length=4000)
    price: int = Field(ge=0, le=10_000_000)
    img_url: str = Field(max_length=512)
    schedule: str = Field(default="По запросу", max_length=32)
    booked_dates: list[str] = Field(default_factory=list)

    @field_validator("booked_dates")
    @classmethod
    def _validate_booked_dates(cls, v: list[str]) -> list[str]:
        return _validate_date_list(v)

    @field_validator("tag", "name", "description")
    @classmethod
    def _strip(cls, v: str) -> str:
        # Defence in depth against the admin.html injection bug: even
        # though the frontend now escapes attributes correctly, quotes
        # and angle brackets simply have no place in these fields.
        v = v.strip()
        if re.search(r"[\"'<>]", v):
            raise ValueError("Поле не должно содержать символы \" ' < >")
        return v

    @field_validator("schedule")
    @classmethod
    def _validate_schedule(cls, v: str) -> str:
        return _validate_schedule_value(v)

    @field_validator("img_url")
    @classmethod
    def _validate_img_url(cls, v: str) -> str:
        return validate_http_url(v, field_name="img_url")


class AdminTourUpdate(BaseModel):
    tag: Optional[str] = Field(default=None, min_length=1, max_length=64)
    name: Optional[str] = Field(default=None, min_length=1, max_length=128)
    description: Optional[str] = Field(default=None, min_length=1, max_length=4000)
    price: Optional[int] = Field(default=None, ge=0, le=10_000_000)
    img_url: Optional[str] = Field(default=None, max_length=512)
    schedule: Optional[str] = Field(default=None, max_length=32)
    booked_dates: Optional[list[str]] = None

    @field_validator("booked_dates")
    @classmethod
    def _validate_booked_dates(cls, v: Optional[list[str]]) -> Optional[list[str]]:
        if v is None:
            return v
        return _validate_date_list(v)

    @field_validator("tag", "name", "description")
    @classmethod
    def _strip(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        if re.search(r"[\"'<>]", v):
            raise ValueError("Поле не должно содержать символы \" ' < >")
        return v

    @field_validator("schedule")
    @classmethod
    def _validate_schedule(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        return _validate_schedule_value(v)

    @field_validator("img_url")
    @classmethod
    def _validate_img_url(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        return validate_http_url(v, field_name="img_url")


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


VALID_ROLES = {"user", "moderator", "admin"}


class UserRoleUpdateRequest(BaseModel):
    role: str

    @field_validator("role")
    @classmethod
    def _validate_role(cls, v: str) -> str:
        v = (v or "").strip().lower()
        if v not in VALID_ROLES:
            raise ValueError(f"Роль должна быть одной из: {', '.join(sorted(VALID_ROLES))}")
        return v


class AdminPasswordResetRequest(BaseModel):
    new_password: str = Field(min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def _check_strength(cls, v: str) -> str:
        return validate_password_strength(v)


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
        role=getattr(user, "role", "admin" if user.is_admin else "user"),
        is_oauth=user.is_oauth,
        created_at=user.created_at,
        bookings_count=bookings_count,
    )


@router.get("/stats", response_model=AdminStatsOut, summary="Общая статистика")
async def get_stats(
    _: User = Depends(require_staff),
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
    _: User = Depends(require_staff),
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


def _apply_role(user: User, role: str) -> None:
    """Single place where role <-> is_admin are kept in sync.

    Every endpoint that changes a user's privilege level must go through
    this helper rather than setting `is_admin` or `role` directly, or the
    two columns can drift apart and `require_admin` (which still reads
    `is_admin`) could disagree with `require_staff` (which reads `role`).
    """
    user.role = role
    user.is_admin = (role == "admin")


@router.patch(
    "/users/{user_id}/toggle-active",
    response_model=AdminUserOut,
    summary="Активировать / деактивировать пользователя",
)
async def toggle_user_active(
    user_id: int,
    data: UserToggleActiveRequest,
    request: Request,
    admin: User = Depends(require_staff),
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
    await log_admin_action(
        session, admin, action="user.block" if not data.is_active else "user.unblock",
        target_type="user", target_id=user.id,
        details=f"Пользователь «{user.username}»: {'блокирован' if not data.is_active else 'разблокирован'}",
        request=request,
    )
    cnt = (
        await session.execute(select(func.count(Booking.id)).where(Booking.user_id == user.id))
    ).scalar_one()
    return _build_user_out(user, cnt)


@router.patch(
    "/users/{user_id}/toggle-admin",
    response_model=AdminUserOut,
    summary="Выдать / отозвать права администратора (устарело, используйте /role)",
)
async def toggle_user_admin(
    user_id: int,
    data: UserToggleAdminRequest,
    request: Request,
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> AdminUserOut:
    """Kept for backward compatibility with older frontend builds.
    New code should call PATCH /users/{id}/role instead, which supports
    the full user/moderator/admin range.
    """
    if user_id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя изменить собственные права",
        )
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
    _apply_role(user, "admin" if data.is_admin else "user")
    await session.commit()
    await session.refresh(user)
    await log_admin_action(
        session, admin, action="user.role_change", target_type="user", target_id=user.id,
        details=f"Пользователь «{user.username}»: роль → {user.role}", request=request,
    )
    cnt = (
        await session.execute(select(func.count(Booking.id)).where(Booking.user_id == user.id))
    ).scalar_one()
    return _build_user_out(user, cnt)


@router.patch(
    "/users/{user_id}/role",
    response_model=AdminUserOut,
    summary="Изменить роль пользователя (user / moderator / admin)",
)
async def update_user_role(
    user_id: int,
    data: UserRoleUpdateRequest,
    request: Request,
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> AdminUserOut:
    if user_id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя изменить собственную роль",
        )
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")

    old_role = getattr(user, "role", "admin" if user.is_admin else "user")
    _apply_role(user, data.role)
    await session.commit()
    await session.refresh(user)
    await log_admin_action(
        session, admin, action="user.role_change", target_type="user", target_id=user.id,
        details=f"Пользователь «{user.username}»: роль {old_role} → {data.role}", request=request,
    )
    cnt = (
        await session.execute(select(func.count(Booking.id)).where(Booking.user_id == user.id))
    ).scalar_one()
    return _build_user_out(user, cnt)


@router.post(
    "/users/{user_id}/reset-password",
    summary="Сбросить пароль пользователя (admin-only)",
    responses={404: {"description": "Не найден"}},
)
async def reset_user_password(
    user_id: int,
    data: AdminPasswordResetRequest,
    request: Request,
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Sets a new password chosen by the admin and marks the account so a
    future "change your password" UI on the public site could prompt the
    user — that public-facing enforcement is NOT implemented here, only
    the data plumbing for it (`force_password_change`).

    The new password is never logged or echoed back beyond this response;
    relay it to the user out-of-band (phone/email), not via the audit log.
    """
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
    if user.is_oauth:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="У этого пользователя вход только через OAuth — у него нет пароля для сброса",
        )

    user.hashed_password = hash_password(data.new_password)
    user.force_password_change = True
    await session.commit()
    await log_admin_action(
        session, admin, action="user.password_reset", target_type="user", target_id=user.id,
        details=f"Сброшен пароль пользователя «{user.username}»", request=request,
    )
    return {"detail": f"Пароль пользователя «{user.username}» обновлён"}


@router.get("/bookings", response_model=list[AdminBookingOut], summary="Все бронирования")
async def list_bookings(
    status_filter: Optional[str] = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    _: User = Depends(require_staff),
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
    request: Request,
    admin: User = Depends(require_staff),
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

    old_status = booking.status
    booking.status = data.status
    await session.commit()
    await session.refresh(booking)
    await log_admin_action(
        session, admin, action="booking.status_change", target_type="booking",
        target_id=booking.id, details=f"Статус: {old_status} → {data.status}", request=request,
    )
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
    _: User = Depends(require_staff),
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
            schedule=t.schedule,
            booked_dates=t.booked_dates_list,
            bookings_count=cnt,
        )
        for t, cnt in rows
    ]


@router.post("/tours", response_model=AdminTourOut, status_code=201, summary="Создать тур")
async def create_tour(
    data: AdminTourCreate,
    request: Request,
    admin: User = Depends(require_staff),
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
        schedule=data.schedule,
        booked_dates=",".join(data.booked_dates) if data.booked_dates else None,
    )
    session.add(tour)
    await session.commit()
    await session.refresh(tour)
    await log_admin_action(
        session, admin, action="tour.create", target_type="tour",
        target_id=tour.id, details=f"Создан тур «{tour.name}»", request=request,
    )
    return AdminTourOut(
        id=tour.id,
        tag=tour.tag,
        name=tour.name,
        description=tour.description,
        price=tour.price,
        img_url=tour.img_url,
        schedule=tour.schedule,
        booked_dates=tour.booked_dates_list,
        bookings_count=0,
    )


@router.patch("/tours/{tour_id}", response_model=AdminTourOut, summary="Обновить тур")
async def update_tour(
    tour_id: str,
    data: AdminTourUpdate,
    request: Request,
    admin: User = Depends(require_staff),
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
    if data.schedule is not None:
        tour.schedule = data.schedule
    if data.booked_dates is not None:
        tour.booked_dates = ",".join(data.booked_dates) if data.booked_dates else None
    await session.commit()
    await session.refresh(tour)
    await log_admin_action(
        session, admin, action="tour.update", target_type="tour",
        target_id=tour.id, details=f"Обновлён тур «{tour.name}»", request=request,
    )
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
        schedule=tour.schedule,
        booked_dates=tour.booked_dates_list,
        bookings_count=cnt,
    )


@router.delete("/tours/{tour_id}", status_code=204, summary="Удалить тур")
async def delete_tour(
    tour_id: str,
    request: Request,
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> None:
    tour = await session.get(Tour, tour_id)
    if not tour:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Тур не найден")
    tour_name = tour.name
    await session.delete(tour)
    await session.commit()
    await log_admin_action(
        session, admin, action="tour.delete", target_type="tour",
        target_id=tour_id, details=f"Удалён тур «{tour_name}»", request=request,
    )
