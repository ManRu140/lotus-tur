import re
from datetime import datetime

from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    field_validator,
    model_validator,
)

from app.core.security import validate_password_strength


def _strip(v: str) -> str:
    return v.strip()


class RegisterRequest(BaseModel):
    username: str = Field(
        min_length=3,
        max_length=64,
        pattern=r"^[a-zA-Zа-яА-ЯёЁ0-9_\-]+$",
        description="Только буквы, цифры, _ и -",
    )
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    @field_validator("username")
    @classmethod
    def normalize_username(cls, v: str) -> str:
        return v.strip()

    @field_validator("password")
    @classmethod
    def check_password_strength(cls, v: str) -> str:
        return validate_password_strength(v)


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=128)

    @field_validator("username", "password")
    @classmethod
    def no_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Поле не может быть пустым")
        return v


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str
    avatar_url: str | None = None
    full_name: str | None = None


class TourOut(BaseModel):
    id: str
    tag: str
    name: str
    description: str
    price: int
    img_url: str
    booked_dates: list[str]

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_tour(cls, tour: object) -> "TourOut":
        return cls(
            id=tour.id,
            tag=tour.tag,
            name=tour.name,
            description=tour.description,
            price=tour.price,
            img_url=tour.img_url,
            booked_dates=tour.booked_dates_list,
        )


_ALLOWED_TIMES = {"09:00", "14:00", "19:00"}

class BookingCreate(BaseModel):
    tour_id: str = Field(min_length=1, max_length=64)
    first_name: str = Field(min_length=2, max_length=128)
    phone: str = Field(
        min_length=6,
        max_length=32,
        description="Телефон в любом формате, цифры и +-()",
    )
    email: EmailStr
    tour_date: str = Field(
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="Дата в формате YYYY-MM-DD",
    )
    preferred_time: str | None = None
    people_count: int = Field(default=1, ge=1, le=20)
    comment: str | None = Field(default=None, max_length=1000)

    @field_validator("first_name", "tour_id")
    @classmethod
    def strip_str(cls, v: str) -> str:
        return v.strip()

    @field_validator("phone")
    @classmethod
    def normalize_phone(cls, v: str) -> str:
        v = v.strip()
        allowed = re.compile(r"[^\d\+\-\(\) ]")
        if allowed.search(v):
            raise ValueError("Телефон содержит недопустимые символы")

        digits = re.sub(r"\D", "", v)
        if len(digits) < 6:
            raise ValueError("Введите корректный номер телефона")
        return v

    @field_validator("preferred_time")
    @classmethod
    def validate_time(cls, v: str | None) -> str | None:
        if v is not None and v not in _ALLOWED_TIMES:
            raise ValueError(f"Время должно быть одним из: {', '.join(_ALLOWED_TIMES)}")
        return v

    @field_validator("comment")
    @classmethod
    def sanitize_comment(cls, v: str | None) -> str | None:
        if v is None:
            return v
        return v.strip().replace("\x00", "")

    @field_validator("tour_date")
    @classmethod
    def validate_date_not_past(cls, v: str) -> str:
        from datetime import date
        try:
            d = date.fromisoformat(v)
        except ValueError:
            raise ValueError("Некорректная дата")
        if d < date.today():
            raise ValueError("Нельзя бронировать прошедшую дату")
        return v


class BookingOut(BaseModel):
    id: int
    tour_id: str
    tour_name: str
    tour_date: str
    people_count: int
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class UsernameUpdate(BaseModel):
    username: str = Field(
        min_length=3,
        max_length=64,
        pattern=r"^[a-zA-Zа-яА-ЯёЁ0-9_\-]+$",
    )

    @field_validator("username")
    @classmethod
    def strip_username(cls, v: str) -> str:
        return v.strip()


class AvatarUpdate(BaseModel):
    avatar_url: str = Field(max_length=512)

    @field_validator("avatar_url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        v = v.strip()
        if not v.startswith(("https://", "http://")):
            raise ValueError("avatar_url должен быть валидным HTTP(S) URL")
        return v


class ProfileOut(BaseModel):
    id: int
    username: str
    email: str
    full_name: str | None
    avatar_url: str | None
    is_oauth: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class AchievementOut(BaseModel):
    id: int
    icon: str
    title: str
    description: str
    unlocked: bool

    model_config = {"from_attributes": True}


class RefLinkOut(BaseModel):
    link: str


class PromoApplyRequest(BaseModel):
    code: str = Field(min_length=3, max_length=32)

    @field_validator("code")
    @classmethod
    def normalize_code(cls, v: str) -> str:
        return v.strip().upper()


class PromoApplyResponse(BaseModel):
    message: str
    discount: int


class ErrorDetail(BaseModel):
    detail: str

class NotificationOut(BaseModel):
    id: int
    type: str
    title: str
    body: str
    is_read: bool
    created_at: datetime

    model_config = {"from_attributes": True}
