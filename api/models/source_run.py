"""SourceRun model: one collection run on one source."""

from datetime import datetime

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from core.clock import naive_utc_now
from core.database import Base
from enums.source_run_status import SourceRunStatus


class SourceRun(Base):
    """
    One collection run, written by every collector; the dashboard shows « Relevé il y a 12 min ».

    Attributes:
        id: Primary key.
        source: ``ListingSource`` value.
        started_at: Run start.
        finished_at: Run end, null while running.
        status: ``SourceRunStatus`` value.
        listings_seen: Listings read.
        listings_new: Listings never seen before.
        listings_changed: Listings with at least one changed field.
        error_message: Error that stopped the run.
    """

    __tablename__ = "source_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    source: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    started_at: Mapped[datetime] = mapped_column(default=naive_utc_now, nullable=False, index=True)
    finished_at: Mapped[datetime | None]
    status: Mapped[str] = mapped_column(String(10), default=SourceRunStatus.RUNNING.value, nullable=False)
    listings_seen: Mapped[int] = mapped_column(default=0, nullable=False)
    listings_new: Mapped[int] = mapped_column(default=0, nullable=False)
    listings_changed: Mapped[int] = mapped_column(default=0, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text)

    def __repr__(self) -> str:
        return f"<SourceRun id={self.id} source={self.source} status={self.status}>"
