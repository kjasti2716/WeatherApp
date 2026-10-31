import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import crud
from app.config import settings
from app.database import get_db
from app.schemas import WeatherResponse
from app.services.weather_service import get_weather

router = APIRouter(prefix="/weather", tags=["weather"])


@router.get("/{location_id}", response_model=WeatherResponse)
async def weather_for_location(
    location_id: int,
    days: int = Query(settings.forecast_days, ge=1, le=16),
    db: Session = Depends(get_db),
) -> WeatherResponse:
    location = crud.get_location(db, location_id)
    if location is None:
        raise HTTPException(status_code=404, detail=f"Location {location_id} not found")
    try:
        return await get_weather(location, days)
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Weather provider error: {exc}") from exc
