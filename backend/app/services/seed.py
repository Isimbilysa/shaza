"""Seed locations.

Six Rwandan district centres spanning the country's climate range -- the volcanic north, the
Kigali plateau, the wetter south, Lake Kivu's shore, and the drier eastern lowlands. Enough
variety that comparing two locations is actually informative, few enough to stay a stage 1
concern.

Coordinates are district-seat approximations. `elevation_m` is left unset on purpose: it gets
filled from the source's grid cell during ingestion, and is labelled as such, rather than
having a number typed in here and quietly treated as surveyed.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Location

SEED_LOCATIONS: list[dict] = [
    {
        "slug": "kigali",
        "name": "Kigali",
        "country": "RW",
        "admin1": "Kigali City",
        "latitude": -1.9441,
        "longitude": 30.0619,
    },
    {
        "slug": "musanze",
        "name": "Musanze",
        "country": "RW",
        "admin1": "Northern Province",
        "latitude": -1.4997,
        "longitude": 29.6344,
    },
    {
        "slug": "huye",
        "name": "Huye",
        "country": "RW",
        "admin1": "Southern Province",
        "latitude": -2.5967,
        "longitude": 29.7394,
    },
    {
        "slug": "rubavu",
        "name": "Rubavu",
        "country": "RW",
        "admin1": "Western Province",
        "latitude": -1.6777,
        "longitude": 29.2591,
    },
    {
        "slug": "nyagatare",
        "name": "Nyagatare",
        "country": "RW",
        "admin1": "Eastern Province",
        "latitude": -1.2978,
        "longitude": 30.3269,
    },
    {
        "slug": "rwamagana",
        "name": "Rwamagana",
        "country": "RW",
        "admin1": "Eastern Province",
        "latitude": -1.9487,
        "longitude": 30.4347,
    },
]


def seed_locations(db: Session) -> list[Location]:
    """Idempotent: inserts what is missing, returns every seed location."""
    existing = {
        loc.slug: loc
        for loc in db.scalars(
            select(Location).where(
                Location.slug.in_([s["slug"] for s in SEED_LOCATIONS])
            )
        )
    }

    created = False
    for spec in SEED_LOCATIONS:
        if spec["slug"] not in existing:
            location = Location(**spec)
            db.add(location)
            existing[spec["slug"]] = location
            created = True

    if created:
        db.commit()
        for location in existing.values():
            db.refresh(location)

    return [existing[spec["slug"]] for spec in SEED_LOCATIONS]
