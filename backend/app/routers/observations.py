"""Series endpoint.

Every response carries its provenance block. There is no query parameter to turn that off, and
no endpoint that returns bare numbers -- a client physically cannot fetch a value from SHAZA
without also receiving what kind of claim it is.
"""

from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Location, Observation, Provenance, Variable
from app.schemas.common import Envelope, ProvenanceBlock, SourceRef
from app.schemas.location import LocationOut
from app.schemas.observation import Point, Series

router = APIRouter(prefix="/observations", tags=["observations"])

DEFAULT_WINDOW_DAYS = 365
MAX_WINDOW_DAYS = 365 * 30


@router.get("/{slug}", response_model=Envelope[list[Series]])
def get_series(
    slug: str,
    variable: list[Variable] | None = Query(
        default=None, description="Repeat to request several. Omit for all stored variables."
    ),
    start: date | None = Query(default=None, description="Inclusive. Defaults to end - 365d."),
    end: date | None = Query(default=None, description="Inclusive. Defaults to today."),
    db: Session = Depends(get_db),
) -> Envelope[list[Series]]:
    location = db.scalar(select(Location).where(Location.slug == slug))
    if location is None:
        raise HTTPException(status_code=404, detail=f"no location {slug!r}")

    end = end or date.today()
    start = start or end - timedelta(days=DEFAULT_WINDOW_DAYS)
    if start > end:
        raise HTTPException(status_code=422, detail="start is after end")
    if (end - start).days > MAX_WINDOW_DAYS:
        raise HTTPException(
            status_code=422, detail=f"window exceeds {MAX_WINDOW_DAYS} days"
        )

    stmt = (
        select(Observation)
        .where(
            Observation.location_id == location.id,
            Observation.observed_on >= start,
            Observation.observed_on <= end,
        )
        .order_by(Observation.variable, Observation.observed_on)
    )
    if variable:
        stmt = stmt.where(Observation.variable.in_(variable))

    rows = db.scalars(stmt).all()

    # Group by (variable, provenance): two provenances for one variable is a real possibility
    # once forecasts land alongside reanalysis, and they must never be merged into one line.
    grouped: dict[tuple[Variable, Provenance], list[Observation]] = {}
    for row in rows:
        grouped.setdefault((row.variable, row.provenance), []).append(row)

    location_out = LocationOut.model_validate(location)
    series: list[Series] = []

    for (var, provenance), observations in grouped.items():
        first = observations[0]
        source = first.source
        series.append(
            Series(
                location=location_out,
                variable=var,
                label=var.label,
                unit=first.unit,
                provenance=ProvenanceBlock(
                    provenance=provenance,
                    label=provenance.label,
                    is_measurement=provenance.is_measurement,
                    maturity=first.maturity,
                    source=SourceRef(
                        slug=source.slug,
                        name=source.name,
                        kind=source.kind,
                        url=source.url,
                        licence=source.licence,
                        attribution=source.attribution,
                    ),
                    caveat=source.notes,
                ),
                count=len(observations),
                points=[Point.model_validate(o) for o in observations],
            )
        )

    series.sort(key=lambda s: s.variable.value)
    return Envelope(data=series)
