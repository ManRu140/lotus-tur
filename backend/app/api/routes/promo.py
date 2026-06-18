from fastapi import APIRouter, Depends, HTTPException, status

from app.core.deps import get_current_active_user
from app.core.rate_limit import InMemoryRateLimiter
from app.models.user import User
from app.schemas.schemas import PromoApplyRequest, PromoApplyResponse, RefLinkOut

router = APIRouter()

VALID_PROMO_CODES: dict[str, int] = {
    "PRIMORYE10": 10,
    "LOTOS20": 20,
    "WELCOME": 5,
}

_promo_limiter = InMemoryRateLimiter(max_attempts=10, window_seconds=60)

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
    user: User = Depends(get_current_active_user),
) -> PromoApplyResponse:

    await _promo_limiter.check(f"user:{user.id}")

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
