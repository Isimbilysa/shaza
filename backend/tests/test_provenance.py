"""The charter's one hard rule, as something a machine checks.

No value is stored without the claim it makes, ERA5 is never labelled a measurement, and no
value leaves the API without its provenance block.
"""

from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.database import get_db
from app.main import app
from app.models import Observation, Provenance, Variable
from app.services import ingest, open_meteo
from tests.conftest import archive, record


def test_the_database_refuses_a_value_without_provenance(db, kigali):
    source = ingest.get_or_create_source(db)
    db.add(
        Observation(
            location_id=kigali.id,
            source_id=source.id,
            provenance=None,
            variable=Variable.TEMPERATURE_MEAN,
            observed_on=date(2026, 1, 1),
            value=21.0,
            unit="degC",
        )
    )

    with pytest.raises(IntegrityError):
        db.flush()


def test_ingested_era5_is_reanalysis_and_not_a_measurement(db, kigali, monkeypatch):
    day = date(2026, 1, 1)
    monkeypatch.setattr(
        open_meteo,
        "fetch_archive",
        lambda **_: archive([record(Variable.TEMPERATURE_MEAN, day, 21.0)]),
    )
    ingest.ingest_location(db, kigali, day, day, [Variable.TEMPERATURE_MEAN])

    rows = db.scalars(select(Observation)).all()
    assert rows
    for row in rows:
        assert row.provenance is Provenance.REANALYSIS
        assert not row.provenance.is_measurement


def test_every_series_from_the_api_carries_its_provenance(db, kigali, monkeypatch):
    # Inside the endpoint's default window, which ends today.
    days = [date.today() - timedelta(days=d) for d in (12, 11, 10)]
    monkeypatch.setattr(
        open_meteo,
        "fetch_archive",
        lambda **_: archive(
            [record(Variable.TEMPERATURE_MEAN, d, 21.0) for d in days]
            + [record(Variable.PRECIPITATION_SUM, d, 3.2) for d in days]
        ),
    )
    ingest.ingest_location(
        db, kigali, days[0], days[-1], [Variable.TEMPERATURE_MEAN, Variable.PRECIPITATION_SUM]
    )

    app.dependency_overrides[get_db] = lambda: db
    try:
        response = TestClient(app).get("/api/v1/observations/kigali")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    series = response.json()["data"]
    assert len(series) == 2
    for s in series:
        block = s["provenance"]
        assert block["provenance"] == "reanalysis"
        assert block["is_measurement"] is False
        assert block["source"]["slug"] == "open-meteo-era5"
        assert block["source"]["attribution"]
