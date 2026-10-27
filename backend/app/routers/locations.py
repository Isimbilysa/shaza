from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Location
from app.schemas.common import Envelope
from app.schemas.location import LocationOut

router = APIRouter(prefix="/locations", tags=["locations"])


@router.get("", response_model=Envelope[list[LocationOut]])
def list_locations(db: Session = Depends(get_db)) -> Envelope[list[LocationOut]]:
    locations = db.scalars(select(Location).order_by(Location.name)).all()
    return Envelope(data=[LocationOut.model_validate(loc) for loc in locations])


@router.get("/{slug}", response_model=Envelope[LocationOut])
def get_location(slug: str, db: Session = Depends(get_db)) -> Envelope[LocationOut]:
    location = db.scalar(select(Location).where(Location.slug == slug))
    if location is None:
        raise HTTPException(status_code=404, detail=f"no location {slug!r}")
    return Envelope(data=LocationOut.model_validate(location))
