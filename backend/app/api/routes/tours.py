"""
API роутер: туры.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.models.tour import Tour
from app.schemas.schemas import TourOut

router = APIRouter()


@router.get("", response_model=list[TourOut])
async def get_tours(session: AsyncSession = Depends(get_session)):
    """Возвращает список всех активных туров."""
    result = await session.execute(select(Tour))
    tours = result.scalars().all()
    return [TourOut.from_orm_tour(t) for t in tours]


@router.get("/{tour_id}", response_model=TourOut)
async def get_tour(tour_id: str, session: AsyncSession = Depends(get_session)):
    """Возвращает один тур по ID."""
    tour = await session.get(Tour, tour_id)
    if not tour:
        raise HTTPException(status_code=404, detail="Тур не найден")
    return TourOut.from_orm_tour(tour)
