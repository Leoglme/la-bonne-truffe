"""
Runs a source asked by hand in the background (docs/05, « Relevés en direct »): the request answers at once, the
run goes on after it, and every device sees it in progress until its run line is closed.
"""

import logging
import threading
from datetime import datetime, timedelta

from sqlalchemy.orm import Session, sessionmaker

from enums.listing_source import ListingSource
from enums.source_run_status import SourceRunStatus
from models.source_run import SourceRun
from services.collection_runner import collection_runner

logger = logging.getLogger(__name__)

# A run line still « running » after that long belongs to a process that stopped: it no longer shows in progress.
RUN_IN_PROGRESS_LIMIT = timedelta(hours=2)


class SourceRunLauncher:
    """Claims a source before its run starts in the background, and frees it once the run is over."""

    def __init__(self) -> None:
        """Start with no run asked by hand."""
        self.launched_sources: set[ListingSource] = set()
        self._lock = threading.Lock()

    def running_sources(self, db: Session, now: datetime) -> list[ListingSource]:
        """
        The sources the server reads now: a run line still open (the worker, or a run asked by hand), or a run
        asked a moment ago whose line is not written yet.

        Args:
            db: Database session.
            now: Current time, naive UTC.

        Returns:
            The sources, in the order of ``ListingSource``.
        """
        open_sources = {
            source
            for (source,) in db.query(SourceRun.source).filter(
                SourceRun.status == SourceRunStatus.RUNNING, SourceRun.started_at > now - RUN_IN_PROGRESS_LIMIT
            )
        }
        with self._lock:
            running = open_sources | self.launched_sources
        return [source for source in ListingSource if source in running]

    def claim(self, db: Session, source: ListingSource, now: datetime) -> bool:
        """
        Claim a source for a run asked by hand, unless it runs already: asked from another device, or read by
        the worker.

        Args:
            db: Database session.
            source: The source to run.
            now: Current time, naive UTC.

        Returns:
            Whether the run is to start; the caller then hands it to ``run``.
        """
        if source in self.running_sources(db, now):
            return False
        with self._lock:
            if source in self.launched_sources:
                return False
            self.launched_sources.add(source)
        return True

    def run(self, session_factory: sessionmaker[Session], source: ListingSource) -> None:
        """
        Run a claimed source with its own session, then free it; the runner records a failure on its run line.

        Args:
            session_factory: Opens a session on the database of the request.
            source: The claimed source.
        """
        db = session_factory()
        try:
            collection_runner.run_source(db, source)
        except Exception:
            logger.exception("%s run asked by hand crashed", source)
        finally:
            db.close()
            with self._lock:
                self.launched_sources.discard(source)


source_run_launcher = SourceRunLauncher()
