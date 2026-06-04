"""
API роутер: реферальные ссылки и промокоды.

Улучшения:
  - Нормализация кода теперь в схеме (PromoApplyRequest.normalize_code)
  - Добавлен простой in-memory rate limiter на применение промокодов
    (предотвращает brute-force перебор кодов)
  - VALID_PROMO_CODES вынесен с комментарием про миграцию в БД
  - ref_code генерируется если отсутствует (защита от пустого поля)

BUG FIX: threading.Lock заменён на asyncio.Lock.
  threading.Lock().acquire() блокирует поток — в asyncio это замораживает event loop,
  что при нагрузке может вызвать таймауты на других запросах.
  asyncio.Lock() корректно освобождает event loop во время ожидания.
"""
import asyncio
import time
from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.core.deps import get_current_active_user
from app.models.user import User
from app.schemas.schemas import PromoApplyRequest, PromoApplyResponse, RefLinkOut

router = APIRouter()

# ── Промокоды ──────────────────────────────────────────────────────────────────
#
# TODO: перенести в таблицу promo_codes(code, discount, expires_at, uses_left)
# Сейчас код → скидка в процентах
VALID_PROMO_CODES: dict[str, int] = {
    "PRIMORYE10": 10,
    "LOTOS20": 20,
    "WELCOME": 5,
}

# ── Простой rate limiter (в памяти) ───────────────────────────────────────────
# BUG FIX: asyncio.Lock вместо threading.Lock (не блокирует event loop)
# В production замените на Redis (например, slowapi + redis-py)
_PROMO_RATE_LIMIT  = 10        # попыток
_PROMO_RATE_WINDOW = 60        # за 60 секунд
_promo_attempts: dict[str, list[float]] = defaultdict(list)
_rate_lock = asyncio.Lock()   # ← asyncio.Lock, не threading.Lock


async def _check_promo_rate_limit(client_key: str) -> None:
    """
    Простой sliding window rate limiter.
    client_key — user_id или IP-адрес клиента.
    BUG FIX: async функция + asyncio.Lock, не блокирует event loop.
    """
    now = time.monotonic()
    async with _rate_lock:
        attempts = _promo_attempts[client_key]
        # Убираем устаревшие записи
        fresh = [t for t in attempts if now - t < _PROMO_RATE_WINDOW]
        _promo_attempts[client_key] = fresh

        if len(fresh) >= _PROMO_RATE_LIMIT:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Слишком много попыток. Повторите через {_PROMO_RATE_WINDOW} секунд.",
                headers={"Retry-After": str(_PROMO_RATE_WINDOW)},
            )

        _promo_attempts[client_key].append(now)


# ── Эндпоинты ──────────────────────────────────────────────────────────────────

@router.get("/ref", response_model=RefLinkOut, summary="Моя реферальная ссылка")
async def get_ref_link(user: User = Depends(get_current_active_user)) -> RefLinkOut:
    """Возвращает реферальную ссылку текущего пользователя."""
    # Используем ref_code или fallback на user{id}
    code = user.ref_code or f"user{user.id}"
    return RefLinkOut(link=f"https://lotos-tour.ru/ref?id={code}")


@router.post(
    "/apply",
    response_model=PromoApplyResponse,
    summary="Применить промокод",
    responses={
        404: {"description": "Промокод не найден"},
        429: {"description": "Слишком много попыток"},
    },
)
async def apply_promo(
    data: PromoApplyRequest,
    request: Request,
    user: User = Depends(get_current_active_user),
) -> PromoApplyResponse:
    """
    Применяет промокод.
    Rate limit: не более 10 попыток в минуту на пользователя.
    BUG FIX: _check_promo_rate_limit теперь async.
    """
    # Rate limiting по user_id (более надёжно, чем по IP за proxy)
    await _check_promo_rate_limit(f"user:{user.id}")

    # Код уже нормализован в схеме (upper + strip)
    discount = VALID_PROMO_CODES.get(data.code)
    if discount is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Промокод не найден или истёк",
        )

    return PromoApplyResponse(
        message=f"Промокод применён! Скидка {discount}% на следующее бронирование.",
        discount=discount,
    )
