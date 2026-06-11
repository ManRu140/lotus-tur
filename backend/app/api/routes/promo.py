import asyncio
import time
from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.core.deps import get_current_active_user
from app.models.user import User
from app.schemas.schemas import PromoApplyRequest, PromoApplyResponse, RefLinkOut

router = APIRouter()


VALID_PROMO_CODES: dict[str, int] = {
    "PRIMORYE10": 10,
    "LOTOS20": 20,
    "WELCOME": 5,
}


_PROMO_RATE_LIMIT  = 10
_PROMO_RATE_WINDOW = 60
_promo_attempts: dict[str, list[float]] = defaultdict(list)
_rate_lock = asyncio.Lock()


async def _check_promo_rate_limit(client_key: str) -> None:
    now = time.monotonic()
    async with _rate_lock:
        attempts = _promo_attempts[client_key]

        fresh = [t for t in attempts if now - t < _PROMO_RATE_WINDOW]
        _promo_attempts[client_key] = fresh

        if len(fresh) >= _PROMO_RATE_LIMIT:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Слишком много попыток. Повторите через {_PROMO_RATE_WINDOW} секунд.",
                headers={"Retry-After": str(_PROMO_RATE_WINDOW)},
            )

        _promo_attempts[client_key].append(now)


@router.get("/ref", response_model=RefLinkOut, summary="Моя реферальная ссылка")
async def get_ref_link(user: User = Depends(get_current_active_user)) -> RefLinkOut:

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

    await _check_promo_rate_limit(f"user:{user.id}")


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
