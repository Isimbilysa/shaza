"""Response envelope and the provenance block every data payload carries."""

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

from app.models.provenance import Maturity, Provenance, SourceKind

T = TypeVar("T")


class SourceRef(BaseModel):
    """Who produced this data. Serialised alongside the data, never separately."""

    slug: str
    name: str
    kind: SourceKind
    url: str | None = None
    licence: str | None = None
    attribution: str


class ProvenanceBlock(BaseModel):
    """The honesty header.

    Attached to every series the API returns so a client cannot render a number without also
    having the claim it makes. `is_measurement` is computed here rather than left to the
    frontend, because a frontend that has to derive it is a frontend that will eventually get
    it wrong.
    """

    provenance: Provenance
    label: str
    is_measurement: bool
    maturity: Maturity
    source: SourceRef
    caveat: str | None = Field(
        default=None,
        description="Plain-language limitation the UI must display with the data.",
    )


class Envelope(BaseModel, Generic[T]):
    """`{ ok, data }` -- matches the shape the SHAZA Labs site already uses."""

    ok: bool = True
    data: T
