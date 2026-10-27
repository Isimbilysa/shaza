"""One value, for one variable, at one location, on one day, from one source.

Note the column order: provenance is declared before `value`. That is not decoration -- the
charter's one hard rule is that no number travels through SHAZA without the claim it is making
attached, and the easiest way to keep that true is to make the honest field impossible to skip
when writing a row.
"""

from datetime import date, datetime

from sqlalchemy import (
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.provenance import Maturity, Provenance
from app.models.variable import Variable


class Observation(Base):
    __tablename__ = "observations"
    __table_args__ = (
        # Re-running a pipeline must not duplicate rows. This is the key the upsert uses.
        UniqueConstraint(
            "location_id",
            "source_id",
            "variable",
            "observed_on",
            name="uq_observation_natural_key",
        ),
        # The query the dashboard actually makes: one location, one variable, a date range.
        Index("ix_observation_series", "location_id", "variable", "observed_on"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    location_id: Mapped[int] = mapped_column(
        ForeignKey("locations.id", ondelete="CASCADE"), index=True
    )
    source_id: Mapped[int] = mapped_column(
        ForeignKey("sources.id", ondelete="RESTRICT"), index=True
    )

    # --- what kind of claim this row makes, before the number it carries ---
    provenance: Mapped[Provenance] = mapped_column(Enum(Provenance, native_enum=False))
    maturity: Mapped[Maturity] = mapped_column(
        Enum(Maturity, native_enum=False), default=Maturity.IN_PROGRESS
    )
    # Half-width of the uncertainty interval in `unit`, when the source publishes one.
    # None means "the source did not quantify it", never "there is none".
    uncertainty: Mapped[float | None] = mapped_column(Float)

    # --- the measurement itself ---
    variable: Mapped[Variable] = mapped_column(Enum(Variable, native_enum=False))
    observed_on: Mapped[date] = mapped_column(index=True)
    value: Mapped[float | None] = mapped_column(Float)
    unit: Mapped[str] = mapped_column(String(24))

    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    location: Mapped["Location"] = relationship(back_populates="observations")  # noqa: F821
    source: Mapped["Source"] = relationship(back_populates="observations")  # noqa: F821

    def __repr__(self) -> str:
        return (
            f"<Observation {self.variable} {self.value}{self.unit} "
            f"@{self.observed_on} ({self.provenance})>"
        )
