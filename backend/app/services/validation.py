"""Plausibility checks run before anything is stored.

These are deliberately wide. The job is to catch a broken parse, a unit mix-up or a sentinel
value like -999 that some archives use for "missing" -- not to second-guess the climate. A
value outside these bounds is treated as a defect in the pipeline until proven otherwise.

Ranges are global, not Rwandan: the pipeline should not silently reject valid data the day it
is pointed at Sahel or highland locations.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.models.variable import Variable
from app.services.open_meteo import DailyRecord

# (minimum, maximum) inclusive, in each variable's canonical unit.
PLAUSIBLE_RANGE: dict[Variable, tuple[float, float]] = {
    Variable.TEMPERATURE_MEAN: (-90.0, 60.0),
    Variable.TEMPERATURE_MAX: (-80.0, 60.0),
    Variable.TEMPERATURE_MIN: (-95.0, 50.0),
    Variable.PRECIPITATION_SUM: (0.0, 2000.0),   # daily record is ~1.8 m
    Variable.RELATIVE_HUMIDITY_MEAN: (0.0, 100.0),
}


@dataclass
class ValidationReport:
    accepted: list[DailyRecord] = field(default_factory=list)
    rejected: list[tuple[DailyRecord, str]] = field(default_factory=list)
    # Nulls are not failures -- an archive gap is information. Counted, not dropped silently.
    gaps: int = 0

    @property
    def ok(self) -> bool:
        return not self.rejected

    def summary(self) -> str:
        return (
            f"{len(self.accepted)} accepted, {self.gaps} gaps, "
            f"{len(self.rejected)} rejected"
        )


def validate(records: list[DailyRecord]) -> ValidationReport:
    report = ValidationReport()

    for record in records:
        if record.value is None:
            report.gaps += 1
            report.accepted.append(record)  # stored as a null, so the gap stays visible
            continue

        low, high = PLAUSIBLE_RANGE[record.variable]
        if not low <= record.value <= high:
            report.rejected.append(
                (record, f"{record.value} outside plausible [{low}, {high}] {record.unit}")
            )
            continue

        expected_unit = record.variable.unit
        if record.unit != expected_unit:
            report.rejected.append(
                (record, f"unit {record.unit!r}, expected {expected_unit!r}")
            )
            continue

        report.accepted.append(record)

    return report
