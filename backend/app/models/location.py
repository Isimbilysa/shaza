"""A point SHAZA collects data about.

Plain latitude/longitude columns for now. PostGIS and real geometry arrive with stage 2, when
there is something to do with them beyond storing a pair of floats.
"""

from datetime import datetime

from sqlalchemy import DateTime, Float, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Location(Base):
    __tablename__ = "locations"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(160))

    country: Mapped[str] = mapped_column(String(2))       # ISO 3166-1 alpha-2
    admin1: Mapped[str | None] = mapped_column(String(120))  # province / region

    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    elevation_m: Mapped[float | None] = mapped_column(Float)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    observations: Mapped[list["Observation"]] = relationship(  # noqa: F821
        back_populates="location"
    )

    def __repr__(self) -> str:
        return f"<Location {self.slug} ({self.latitude}, {self.longitude})>"
