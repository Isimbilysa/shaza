"""A source of data. Nothing enters `observations` without one."""

from datetime import datetime

from sqlalchemy import DateTime, Enum, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.provenance import SourceKind


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(160))
    kind: Mapped[SourceKind] = mapped_column(Enum(SourceKind, native_enum=False))

    url: Mapped[str | None] = mapped_column(String(500))
    licence: Mapped[str | None] = mapped_column(String(160))
    # Credit line the UI is required to show wherever this source's data appears.
    attribution: Mapped[str] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    observations: Mapped[list["Observation"]] = relationship(back_populates="source")  # noqa: F821

    def __repr__(self) -> str:
        return f"<Source {self.slug} ({self.kind})>"
