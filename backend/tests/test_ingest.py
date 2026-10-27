"""Re-running ingestion converges instead of duplicating.

The pipeline is meant to run on a schedule and overlap its own window, so this is the property
everything downstream relies on.
"""

from datetime import date, timedelta

from sqlalchemy import func, select

from app.models import Observation, Variable
from app.services import ingest, open_meteo
from tests.conftest import archive, record

START = date(2026, 1, 1)
DAYS = [START + timedelta(days=i) for i in range(3)]


def _count(db) -> int:
    return db.scalar(select(func.count()).select_from(Observation))


def test_second_ingest_of_the_same_window_adds_no_rows(db, kigali, monkeypatch):
    records = [record(Variable.TEMPERATURE_MEAN, d, 20.0 + i) for i, d in enumerate(DAYS)]
    monkeypatch.setattr(open_meteo, "fetch_archive", lambda **_: archive(records))

    ingest.ingest_location(db, kigali, DAYS[0], DAYS[-1], [Variable.TEMPERATURE_MEAN])
    assert _count(db) == 3

    ingest.ingest_location(db, kigali, DAYS[0], DAYS[-1], [Variable.TEMPERATURE_MEAN])
    assert _count(db) == 3


def test_a_revised_value_updates_the_existing_row(db, kigali, monkeypatch):
    # Sources revise. A re-run should leave the newest value, in the same row.
    day = DAYS[0]
    monkeypatch.setattr(
        open_meteo,
        "fetch_archive",
        lambda **_: archive([record(Variable.TEMPERATURE_MEAN, day, 20.0)]),
    )
    ingest.ingest_location(db, kigali, day, day, [Variable.TEMPERATURE_MEAN])

    monkeypatch.setattr(
        open_meteo,
        "fetch_archive",
        lambda **_: archive([record(Variable.TEMPERATURE_MEAN, day, 20.7)]),
    )
    ingest.ingest_location(db, kigali, day, day, [Variable.TEMPERATURE_MEAN])

    db.expire_all()
    rows = db.scalars(select(Observation)).all()
    assert len(rows) == 1
    assert rows[0].value == 20.7


def test_rejected_records_are_not_stored(db, kigali, monkeypatch):
    records = [
        record(Variable.TEMPERATURE_MEAN, DAYS[0], 21.0),
        record(Variable.TEMPERATURE_MEAN, DAYS[1], -999.0),
    ]
    monkeypatch.setattr(open_meteo, "fetch_archive", lambda **_: archive(records))

    result = ingest.ingest_location(db, kigali, DAYS[0], DAYS[1], [Variable.TEMPERATURE_MEAN])

    assert len(result.report.rejected) == 1
    assert _count(db) == 1
