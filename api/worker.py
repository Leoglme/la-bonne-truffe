"""
Collection worker entry point: a separate process that runs the scheduled jobs (APScheduler).

Run with:
    python worker.py
"""

import logging

from apscheduler.schedulers.blocking import BlockingScheduler

from core.clock import naive_utc_now
from core.database import SessionLocal, engine
from enums.listing_source import ListingSource
from migrations.run_migrations import MigrationRunner
from services.collection_runner import collection_runner
from services.notifier import notifier_service

logger = logging.getLogger("worker")

SCHEDULER_TIMEZONE = "Europe/Paris"

COLLECTION_MINUTES: dict[ListingSource, int] = {
    ListingSource.CENTRALE_CANINE: 5,
    ListingSource.CHIENS_DE_FRANCE: 20,
    ListingSource.CHIOTS_DE_FRANCE: 35,
}


class CollectionWorker:
    """Builds the scheduler with every collection job and runs it until stopped."""

    def build_scheduler(self) -> BlockingScheduler:
        """
        Create the scheduler and register the jobs.

        One job per collected source runs every hour, a few minutes apart (``COLLECTION_MINUTES``). The
        evening digest job wakes at minute 0 of every hour and sends the digests whose ``digest_hour``
        has come.

        Returns:
            The configured scheduler, not started.
        """
        scheduler = BlockingScheduler(timezone=SCHEDULER_TIMEZONE)
        scheduler.configure(job_defaults={"coalesce": True, "max_instances": 1, "misfire_grace_time": 600})
        for source, minute in COLLECTION_MINUTES.items():
            scheduler.add_job(self.collect_source, "cron", minute=minute, args=[source], id=f"collect_{source.value}")
        scheduler.add_job(self.send_evening_digests, "cron", minute=0, id="send_evening_digests")
        return scheduler

    def collect_source(self, source: ListingSource) -> None:
        """
        Hourly run of one source, with its own session; a failure is recorded on its run line.

        Args:
            source: The source to read.
        """
        db = SessionLocal()
        try:
            report = collection_runner.run_source(db, source)
            logger.info(
                "%s run %s: %d seen, %d new, %d changed",
                source.value,
                report.source_run.status,
                report.source_run.listings_seen,
                report.source_run.listings_new,
                report.source_run.listings_changed,
            )
        finally:
            db.close()

    def send_evening_digests(self) -> None:
        """Hourly check: send the digests of the profiles whose digest hour is now."""
        db = SessionLocal()
        try:
            sent_count = notifier_service.send_due_evening_digests(db, naive_utc_now())
            if sent_count:
                logger.info("Evening digest sent to %d user(s)", sent_count)
        finally:
            db.close()

    def run(self) -> None:
        """Bring the schema up to date, then block on the scheduler until interrupted."""
        MigrationRunner(engine).run()
        scheduler = self.build_scheduler()
        logger.info("Worker started with %d job(s)", len(scheduler.get_jobs()))
        try:
            scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            logger.info("Worker stopped")


collection_worker = CollectionWorker()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    collection_worker.run()
