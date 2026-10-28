"""Source status schema: « Relevé il y a 12 min » and the green or red dot."""

from datetime import datetime

from pydantic import BaseModel

from enums.listing_source import ListingSource
from enums.source_run_status import SourceRunStatus


class SourceStatus(BaseModel):
    """Last run of a source."""

    source: ListingSource
    label: str
    is_collected: bool
    last_run_at: datetime | None
    last_status: SourceRunStatus | None
    last_success_at: datetime | None
    listings_seen: int | None
    error_message: str | None
