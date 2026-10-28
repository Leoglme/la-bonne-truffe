"""
Collection worker entry point: a separate process that runs the scheduled jobs (APScheduler).

Run with:
    python worker.py
"""

import logging

from apscheduler.schedulers.blocking import BlockingScheduler

from core.database import engine
from migrations.run_migrations import MigrationRunner

logger = logging.getLogger("worker")

SCHEDULER_TIMEZONE = "Europe/Paris"


class CollectionWorker:
    """Builds the scheduler with every collection job and runs it until stopped."""

    def build_scheduler(self) -> BlockingScheduler:
        """
        Create the scheduler and register the jobs.

        One job per source runs every hour, a few minutes apart; the evening digest runs at the
        profile's ``digest_hour``. No job is registered yet: they arrive with milestones 1 and 2.

        Returns:
            The configured scheduler, not started.
        """
        scheduler = BlockingScheduler(timezone=SCHEDULER_TIMEZONE)
        scheduler.configure(job_defaults={"coalesce": True, "max_instances": 1, "misfire_grace_time": 600})
        return scheduler

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
