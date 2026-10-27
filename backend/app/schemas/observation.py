from datetime import date

from pydantic import BaseModel, ConfigDict

from app.models.variable import Variable
from app.schemas.common import ProvenanceBlock
from app.schemas.location import LocationOut


class Point(BaseModel):
    """A single day. `value` may be null where the source had a gap -- gaps are data too."""

    model_config = ConfigDict(from_attributes=True)

    observed_on: date
    value: float | None
    uncertainty: float | None = None


class Series(BaseModel):
    """One variable at one location, with its provenance inseparable from its points."""

    location: LocationOut
    variable: Variable
    label: str
    unit: str
    provenance: ProvenanceBlock
    count: int
    points: list[Point]
