"""Ingestion: source -> validate -> upsert.

Re-running the same fetch must not create duplicate rows, because the pipeline is meant to run
on a schedule and overlap its own window. The natural key
(location, source, variable, observed_on) carries a unique constraint, and this module upserts
against it. That is also what makes "commit only when something meaningful changed" (charter
rule 9) checkable: if an upsert changes nothing, nothing changed.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from app.models import (
    Location,
    Maturity,
    Observation,
    Provenance,
    Source,
    SourceKind,
    Variable,
)
from app.services import open_meteo
from app.services.validation import ValidationReport, validate

logger = logging.getLogger(__name__)

DEFAULT_VARIABLES = [
    Variable.TEMPERATURE_MEAN,
    Variable.TEMPERATURE_MAX,
    Variable.TEMPERATURE_MIN,
    Variable.PRECIPITATION_SUM,
    Variable.RELATIVE_HUMIDITY_MEAN,
]


@dataclass
class IngestResult:
    location_slug: str
    start: date
    end: date
    report: ValidationReport
    rows_written: int
    caveat: str

    def summary(self) -> str:
        return (
            f"{self.location_slug} {self.start}..{self.end}: "
            f"{self.report.summary()}, {self.rows_written} rows upserted"
        )


def ingest_location(
    db: Session,
    location: Location,
    start: date,
    end: date,
    variables: list[Variable] | None = None,
) -> IngestResult:
    """Fetch, validate and store one location's daily history for a date range."""
    variables = variables or DEFAULT_VARIABLES
    source = get_or_create_source(db)

    response = open_meteo.fetch_archive(
        latitude=location.latitude,
        longitude=location.longitude,
        start=start,
        end=end,
        variables=variables,
    )
    caveat = response.caveat(location.latitude, location.longitude)

    report = validate(response.records)
    for record, reason in report.rejected:
        logger.warning(
            "rejected %s %s for %s: %s",
            record.variable.value,
            record.observed_on,
            location.slug,
            reason,
        )

    # Open-Meteo reports the elevation of the cell it used. Worth keeping once.
    if location.elevation_m is None and response.elevation_m is not None:
        location.elevation_m = response.elevation_m

    rows = [
        {
            "location_id": location.id,
            "source_id": source.id,
            "provenance": Provenance.REANALYSIS,
            "maturity": Maturity.IN_PROGRESS,
            "uncertainty": None,  # ERA5 publishes spread, but not through this endpoint
            "variable": record.variable,
            "observed_on": record.observed_on,
            "value": record.value,
            "unit": record.unit,
        }
        for record in report.accepted
    ]

    written = _upsert_observations(db, rows)
    db.commit()

    return IngestResult(
        location_slug=location.slug,
        start=start,
        end=end,
        report=report,
        rows_written=written,
        caveat=caveat,
    )


# SQLite caps a statement at 32766 bound parameters, and a two-year fetch of five variables is
# 3650 rows x 9 columns = 32850 -- just over. Chunking keeps the statement well clear of that,
# and keeps the transaction a reasonable size on Postgres too.
UPSERT_CHUNK_ROWS = 500


def _upsert_observations(db: Session, rows: list[dict]) -> int:
    """Insert rows, updating value/unit/provenance where the natural key already exists."""
    if not rows:
        return 0

    dialect = db.get_bind().dialect.name
    if dialect == "postgresql":
        insert = pg_insert
    elif dialect == "sqlite":
        insert = sqlite_insert
    else:  # pragma: no cover - only these two are supported deliberately
        raise RuntimeError(f"no upsert strategy for dialect {dialect!r}")

    for offset in range(0, len(rows), UPSERT_CHUNK_ROWS):
        chunk = rows[offset : offset + UPSERT_CHUNK_ROWS]
        stmt = insert(Observation).values(chunk)
        stmt = stmt.on_conflict_do_update(
            # Column inference rather than the constraint name: SQLite's ON CONFLICT only
            # accepts index_elements, and these are exactly uq_observation_natural_key.
            index_elements=["location_id", "source_id", "variable", "observed_on"],
            set_={
                "value": stmt.excluded.value,
                "unit": stmt.excluded.unit,
                "provenance": stmt.excluded.provenance,
                "maturity": stmt.excluded.maturity,
                "uncertainty": stmt.excluded.uncertainty,
            },
        )
        db.execute(stmt)

    return len(rows)


def get_or_create_source(db: Session) -> Source:
    """The Open-Meteo / ERA5 source record. Attribution is a licence condition, not a nicety."""
    source = db.scalar(select(Source).where(Source.slug == open_meteo.SOURCE_SLUG))
    if source is not None:
        return source

    source = Source(
        slug=open_meteo.SOURCE_SLUG,
        name="Open-Meteo Historical Weather API (ERA5)",
        kind=SourceKind.EXTERNAL_API,
        url="https://open-meteo.com/en/docs/historical-weather-api",
        licence="CC BY 4.0 (Open-Meteo) / ECMWF ERA5 terms",
        attribution="Weather data by Open-Meteo.com, derived from ECMWF ERA5 reanalysis.",
        notes=(
            "Reanalysis output on a ~9-11 km grid, not station measurements. Retrieved by "
            "SHAZA; not collected by SHAZA."
        ),
    )
    db.add(source)
    db.commit()
    db.refresh(source)
    return source
