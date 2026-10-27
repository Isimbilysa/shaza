"""Shared fixtures.

Tests never touch the network or a real database. `backend/.env` may point at a hosted
Postgres, so DATABASE_URL is overridden before anything under `app` is imported -- an
environment variable beats the .env file in pydantic-settings. Each test then gets its own
in-memory SQLite, created from the models.
"""

import os

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from datetime import date  # noqa: E402

import pytest  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

import app.models  # noqa: E402, F401 - registers every table on Base.metadata
from app.core.database import Base  # noqa: E402
from app.models import Location, Variable  # noqa: E402
from app.services.open_meteo import ArchiveResponse, DailyRecord  # noqa: E402


@pytest.fixture
def db():
    # StaticPool keeps one connection, so the in-memory database survives across the
    # sessions and threads a FastAPI TestClient uses.
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    with Session(engine, autoflush=False, expire_on_commit=False) as session:
        yield session
    engine.dispose()


@pytest.fixture
def kigali(db: Session) -> Location:
    location = Location(
        slug="kigali",
        name="Kigali",
        country="RW",
        admin1="Kigali City",
        latitude=-1.9441,
        longitude=30.0619,
    )
    db.add(location)
    db.commit()
    return location


def record(
    variable: Variable, day: date, value: float | None, unit: str | None = None
) -> DailyRecord:
    return DailyRecord(
        variable=variable, observed_on=day, value=value, unit=unit or variable.unit
    )


def archive(records: list[DailyRecord]) -> ArchiveResponse:
    """A canned Open-Meteo response, so ingestion runs without the network."""
    return ArchiveResponse(
        grid_latitude=-1.95,
        grid_longitude=30.05,
        elevation_m=1567.0,
        timezone="Africa/Kigali",
        records=records,
    )
