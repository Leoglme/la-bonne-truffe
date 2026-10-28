"""State of each source for the dashboard."""

from sqlalchemy.orm import Session

from enums.listing_source import ListingSource
from enums.source_run_status import SourceRunStatus
from models.source_run import SourceRun
from schemas.source_status import SourceStatus
from services.notification_texts import SOURCE_NAMES

COLLECTED_SOURCES: frozenset[ListingSource] = frozenset({ListingSource.CENTRALE_CANINE, ListingSource.CHIENS_DE_FRANCE})


class SourceStatusService:
    """Reads the last run of every source."""

    @staticmethod
    def list_statuses(db: Session) -> list[SourceStatus]:
        """
        One status per source, collected or not yet.

        Args:
            db: Database session.

        Returns:
            The statuses.
        """
        statuses: list[SourceStatus] = []
        for source in ListingSource:
            last_run = (
                db.query(SourceRun)
                .filter(SourceRun.source == source)
                .order_by(SourceRun.started_at.desc(), SourceRun.id.desc())
                .first()
            )
            last_success = (
                db.query(SourceRun)
                .filter(SourceRun.source == source, SourceRun.status == SourceRunStatus.OK)
                .order_by(SourceRun.started_at.desc())
                .first()
            )
            statuses.append(
                SourceStatus(
                    source=source,
                    label=SOURCE_NAMES[source].removeprefix("La "),
                    is_collected=source in COLLECTED_SOURCES,
                    last_run_at=(last_run.finished_at or last_run.started_at) if last_run is not None else None,
                    last_status=last_run.status if last_run is not None else None,
                    last_success_at=last_success.finished_at if last_success is not None else None,
                    listings_seen=last_run.listings_seen if last_run is not None else None,
                    error_message=last_run.error_message if last_run is not None else None,
                )
            )
        return statuses
