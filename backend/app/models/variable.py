"""The environmental variables SHAZA stores, and their canonical units.

Kept deliberately short. A variable is added when a pipeline actually fetches it, not in
anticipation -- charter rule 7.
"""

from enum import StrEnum


class Variable(StrEnum):
    TEMPERATURE_MEAN = "temperature_2m_mean"
    TEMPERATURE_MAX = "temperature_2m_max"
    TEMPERATURE_MIN = "temperature_2m_min"
    PRECIPITATION_SUM = "precipitation_sum"
    RELATIVE_HUMIDITY_MEAN = "relative_humidity_2m_mean"

    @property
    def unit(self) -> str:
        return UNITS[self]

    @property
    def label(self) -> str:
        return LABELS[self]


UNITS: dict[Variable, str] = {
    Variable.TEMPERATURE_MEAN: "degC",
    Variable.TEMPERATURE_MAX: "degC",
    Variable.TEMPERATURE_MIN: "degC",
    Variable.PRECIPITATION_SUM: "mm",
    Variable.RELATIVE_HUMIDITY_MEAN: "percent",
}

LABELS: dict[Variable, str] = {
    Variable.TEMPERATURE_MEAN: "Mean temperature",
    Variable.TEMPERATURE_MAX: "Max temperature",
    Variable.TEMPERATURE_MIN: "Min temperature",
    Variable.PRECIPITATION_SUM: "Precipitation",
    Variable.RELATIVE_HUMIDITY_MEAN: "Mean relative humidity",
}
