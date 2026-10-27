"""Validation catches pipeline defects without second-guessing the climate."""

from datetime import date

from app.models import Variable
from app.services.validation import validate
from tests.conftest import record

DAY = date(2026, 1, 15)


def test_accepts_a_plausible_value():
    report = validate([record(Variable.TEMPERATURE_MEAN, DAY, 21.4)])

    assert report.ok
    assert len(report.accepted) == 1


def test_rejects_a_value_outside_the_plausible_range():
    # -999 is the sentinel some archives use for "missing". It must never be stored as a
    # temperature.
    report = validate([record(Variable.TEMPERATURE_MEAN, DAY, -999.0)])

    assert not report.ok
    assert report.accepted == []
    assert "outside plausible" in report.rejected[0][1]


def test_rejects_negative_rainfall():
    report = validate([record(Variable.PRECIPITATION_SUM, DAY, -0.5)])

    assert len(report.rejected) == 1


def test_rejects_the_wrong_unit():
    # 30 passes the range check either way, but 30 degF is about -1 degC. Stored as degC it
    # would be wrong by 31 degrees; only the unit check catches it.
    report = validate([record(Variable.TEMPERATURE_MAX, DAY, 30.0, unit="degF")])

    assert len(report.rejected) == 1
    assert "unit" in report.rejected[0][1]


def test_a_null_is_a_gap_not_a_failure():
    # A null is information about the archive. It is kept, so the gap stays visible, and
    # counted, so it is not silent.
    report = validate([record(Variable.TEMPERATURE_MEAN, DAY, None)])

    assert report.ok
    assert report.gaps == 1
    assert report.accepted[0].value is None
