"""Nightly housekeeping: drops the raw pages and the change history that no screen reads any more."""

from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from models.listing import Listing
from models.listing_change import ListingChange

# The raw page of a listing gone from its source, and every field change, are kept this long.
LISTING_DATA_RETENTION = timedelta(days=90)


@dataclass
class HousekeepingReport:
    """What a housekeeping run removed."""

    raw_pages_cleared: int = 0
    changes_deleted: int = 0


class HousekeepingService:
    """Keeps the database from growing with data nobody reads."""

    @staticmethod
    def purge_old_listing_data(db: Session, now: datetime) -> HousekeepingReport:
        """
        Clear the raw page of the listings gone from their source for ``LISTING_DATA_RETENTION``, and delete
        the field changes older than that. An active listing keeps its raw page: each run overwrites it.

        Args:
            db: Database session; committed.
            now: Current time, naive UTC.

        Returns:
            What was removed.
        """
        kept_since = now - LISTING_DATA_RETENTION
        raw_pages_cleared = (
            db.query(Listing)
            .filter(Listing.is_active.is_(False), Listing.last_seen_at < kept_since, Listing.raw_json.is_not(None))
            .update({Listing.raw_json: None}, synchronize_session=False)
        )
        changes_deleted = (
            db.query(ListingChange).filter(ListingChange.changed_at < kept_since).delete(synchronize_session=False)
        )
        db.commit()
        return HousekeepingReport(raw_pages_cleared=raw_pages_cleared, changes_deleted=changes_deleted)


housekeeping_service = HousekeepingService()
