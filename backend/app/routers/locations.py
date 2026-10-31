from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import crud
from app.database import get_db
from app.models import Location
from app.routers.geocode import geocode_or_raise
from app.schemas import LocationCreate, LocationRead, LocationUpdate

router = APIRouter(prefix="/locations", tags=["locations"])


def _get_or_404(db: Session, location_id: int) -> Location:
    location = crud.get_location(db, location_id)
    if location is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Location {location_id} not found")
    return location


def _duplicate(db: Session) -> HTTPException:
    db.rollback()
    return HTTPException(status.HTTP_409_CONFLICT, "A location with this country, city and area name already exists")


@router.get("", response_model=list[LocationRead])
def list_locations(db: Session = Depends(get_db)):
    return crud.list_locations(db)


@router.get("/{location_id}", response_model=LocationRead)
def get_location(location_id: int, db: Session = Depends(get_db)):
    return _get_or_404(db, location_id)


@router.post("", response_model=LocationRead, status_code=status.HTTP_201_CREATED)
def create_location(data: LocationCreate, db: Session = Depends(get_db)):
    if data.latitude is None:
        point = geocode_or_raise(data)
        data = data.model_copy(update={"latitude": point.latitude, "longitude": point.longitude})
    try:
        return crud.create_location(db, data)
    except IntegrityError as exc:
        raise _duplicate(db) from exc


@router.patch("/{location_id}", response_model=LocationRead)
def update_location(location_id: int, data: LocationUpdate, db: Session = Depends(get_db)):
    location = _get_or_404(db, location_id)
    try:
        return crud.update_location(db, location, data)
    except IntegrityError as exc:
        raise _duplicate(db) from exc


@router.delete("/{location_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_location(location_id: int, db: Session = Depends(get_db)):
    crud.delete_location(db, _get_or_404(db, location_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)
