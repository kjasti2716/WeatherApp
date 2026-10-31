"""Database access for locations."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Location
from app.schemas import LocationCreate, LocationUpdate


def list_locations(db: Session) -> list[Location]:
    return list(db.scalars(select(Location).order_by(Location.country, Location.city, Location.area_name)))


def get_location(db: Session, location_id: int) -> Location | None:
    return db.get(Location, location_id)


def create_location(db: Session, data: LocationCreate) -> Location:
    location = Location(**data.model_dump())
    db.add(location)
    db.commit()
    db.refresh(location)
    return location


def update_location(db: Session, location: Location, data: LocationUpdate) -> Location:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(location, field, value)
    db.commit()
    db.refresh(location)
    return location


def delete_location(db: Session, location: Location) -> None:
    db.delete(location)
    db.commit()
