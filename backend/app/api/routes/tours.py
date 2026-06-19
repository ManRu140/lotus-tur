from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.models.tour import Tour
from app.schemas.schemas import TourOut

router = APIRouter()

@router.get("", response_model=list[TourOut])
async def get_tours(
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
):
    # Pagination added for consistency with every other list endpoint
    # (bookings, users, logs, reviews all take limit/offset) and as a
    # bound against the response growing unbounded as more tours are
    # added — defaults to effectively "all current tours" so existing
    # frontend calls (which don't pass these params) keep working
    # unchanged.
    result = await session.execute(select(Tour).limit(limit).offset(offset))
    tours = result.scalars().all()
    return [TourOut.from_orm_tour(t) for t in tours]

@router.get("/{tour_id}", response_model=TourOut)
async def get_tour(tour_id: str, session: AsyncSession = Depends(get_session)):
    tour = await session.get(Tour, tour_id)
    if not tour:
        raise HTTPException(status_code=404, detail="Тур не найден")
    return TourOut.from_orm_tour(tour)
