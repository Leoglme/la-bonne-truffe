"""
Collection worker entry point: a separate process that runs the scheduled jobs (APScheduler).

Run with:
    python worker.py
"""

import logging

from apscheduler.schedulers.blocking import BlockingScheduler

from core.database import SessionLocal, engine
from migrations.run_migrations import MigrationRunner
from services.collection_runner import collection_runner
from services.collectors.centrale_canine import CentraleCanineCollector

logger = logging.getLogger("worker")

SCHEDULER_TIMEZONE = "Europe/Paris"


class CollectionWorker:
    """Builds the scheduler with every collection job and runs it until stopped."""

    def build_scheduler(self) -> BlockingScheduler:
        """
        Create the scheduler and register the jobs.

        One job per source runs every hour, a few minutes apart (the Centrale Canine at minute 5);
        the evening digest at the profile's ``digest_hour`` arrives with milestone 2.

        Returns:
            The configured scheduler, not started.
        """
        scheduler = BlockingScheduler(timezone=SCHEDULER_TIMEZONE)
        scheduler.configure(job_defaults={"coalesce": True, "max_instances": 1, "misfire_grace_time": 600})
        scheduler.add_job(self.collect_centrale_canine, "cron", minute=5, id="collect_centrale_canine")
        return scheduler

    def collect_centrale_canine(self) -> None:
        """Hourly Centrale Canine run, with its own session; a failure is recorded on its run line."""
        db = SessionLocal()
        try:
            report = collection_runner.run_centrale_canine(db, CentraleCanineCollector())
            logger.info(
                "Centrale Canine run %s: %d seen, %d new, %d changed",
                report.source_run.status,
                report.source_run.listings_seen,
                report.source_run.listings_new,
                report.source_run.listings_changed,
            )
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
