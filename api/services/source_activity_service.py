"""What runs now, on the server and on the computers: the Sources page of every device polls it (docs/05)."""

from datetime import datetime

from sqlalchemy.orm import Session

from schemas.source_activity import SourceActivity
from services.centrale_canine_relay import CentraleCanineRelay
from services.source_run_launcher import source_run_launcher


class SourceActivityService:
    """Gathers the runs of the server and the relay of the computers in one answer."""

    @staticmethod
    def read(db: Session, relay: CentraleCanineRelay | None, now: datetime) -> SourceActivity:
        """
        What runs now.

        Args:
            db: Database session.
            relay: The relay of the desktop app, None when the server reads the Centrale Canine itself.
            now: Current time, naive UTC.

        Returns:
            The sources the server reads, and where the relay stands.
        """
        return SourceActivity(
            running_sources=source_run_launcher.running_sources(db, now),
            relay=relay.activity(now) if relay is not None else None,
        )
