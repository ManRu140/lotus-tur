"""
Безопасность: хэширование паролей, JWT-токены, валидация паролей.

Изменения по сравнению с оригиналом:
  - Добавлена функция validate_password_strength для проверки сложности пароля
  - create_access_token принимает только int (user_id), а не str | int
  - decode_access_token возвращает Optional[int] вместо str
  - Добавлены константы для конфигурации bcrypt
"""
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# rounds=12 — хороший баланс безопасности и скорости (~300ms/hash)
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,
)

# Минимальные требования к паролю
_MIN_PASSWORD_LEN = 8


def hash_password(password: str) -> str:
    """Хэширует пароль через bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """
    Проверяет пароль против хэша.
    OAuth-пользователи не имеют пароля — возвращаем False.
    """
    if not hashed:
        return False
    return pwd_context.verify(plain, hashed)


def validate_password_strength(password: str) -> str:
    """
    Проверяет сложность пароля.
    Бросает ValueError, если требования не выполнены.
    Возвращает пароль для использования в Pydantic-валидаторах.
    """
    errors: list[str] = []

    if len(password) < _MIN_PASSWORD_LEN:
        errors.append(f"Пароль должен быть не менее {_MIN_PASSWORD_LEN} символов")
    if not any(c.isupper() for c in password):
        errors.append("Добавьте хотя бы одну заглавную букву")
    if not any(c.isdigit() for c in password):
        errors.append("Добавьте хотя бы одну цифру")

    if errors:
        raise ValueError("; ".join(errors))

    return password


def create_access_token(user_id: int) -> str:
    """
    Создаёт JWT access-токен.
    sub хранит строковое представление user_id (стандарт RFC 7519).
    """
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {
        "sub": str(user_id),
        "exp": expire,
        "iat": datetime.now(timezone.utc),  # issued at — для аудита
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> int | None:
    """
    Декодирует JWT и возвращает user_id (int) или None при любой ошибке.
    Тип возврата — int, а не str, что позволяет сразу использовать в запросах.
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        sub = payload.get("sub")
        if sub is None:
            return None
        return int(sub)
    except (JWTError, ValueError):
        return None
