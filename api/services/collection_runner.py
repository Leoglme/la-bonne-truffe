"""Runs one collection on one source and writes its ``source_runs`` line."""

import logging
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from core.clock import naive_utc_now
from enums.listing_source import ListingSource
from enums.source_run_status import SourceRunStatus
from models.source_run import SourceRun
from services.collection_planner import CollectionPlanner
from services.collectors.centrale_canine import (
    CentraleCanineCollection,
    CentraleCanineCollectionPlan,
    CentraleCanineCollector,
    CentraleCanineError,
)
from services.listing_ingestion import IngestionSummary, listing_ingestion_service

logger = logging.getLogger(__name__)


@dataclass
class CentraleCanineRunReport:
    """Everything a Centrale Canine run did, for the command line and the worker log."""

    source_run: SourceRun
    plan: CentraleCanineCollectionPlan
    collection: CentraleCanineCollection = field(default_factory=CentraleCanineCollection)
    summary: IngestionSummary = field(default_factory=IngestionSummary)


class CollectionRunner:
    """Plans, collects and stores a run; an error on a source is recorded, never raised further."""

    def run_centrale_canine(self, db: Session, collector: CentraleCanineCollector) -> CentraleCanineRunReport:
        """
        Read the Centrale Canine for the active profiles and store what was found.

        Args:
            db: Database session.
            collector: Collector to read with (a real one, or one on a fake transport in the tests).

        Returns:
            The run report; ``source_run.status`` tells whether it succeeded.
        """
        source_run = SourceRun(source=ListingSource.CENTRALE_CANINE.value, started_at=naive_utc_now())
        db.add(source_run)
        db.commit()

        plan = CollectionPlanner.build_centrale_canine_plan(db)
        report = CentraleCanineRunReport(source_run=source_run, plan=plan)
        if plan.departments_without_term_id:
            logger.warning(
                "Centrale Canine: departments without t_ID, not read (run `python cli.py scc-sync`): %s",
                ", ".join(plan.departments_without_term_id),
            )

        try:
            if not plan.breeds or not plan.departments:
                raise CentraleCanineError("Rien à relever : aucun profil actif avec une race et un département connus")
            report.collection = collector.collect(plan)
            report.summary = listing_ingestion_service.ingest(
                db,
                ListingSource.CENTRALE_CANINE.value,
                report.collection.listings,
                {department.code for department in plan.departments},
                naive_utc_now(),
            )
            source_run.status = SourceRunStatus.OK.value
            source_run.listings_seen = report.summary.seen_count
            source_run.listings_new = len(report.summary.new_listing_ids)
            source_run.listings_changed = len(report.summary.changed_listing_ids)
        except Exception as error:
            # A failing source must never stop the others: the error goes to the run line.
            db.rollback()
            source_run.status = SourceRunStatus.ERROR.value
            source_run.error_message = str(error)[:2000]
            if isinstance(error, CentraleCanineError):
                logger.error("Centrale Canine run failed: %s", error)
            else:
                logger.exception("Centrale Canine run crashed")
        finally:
            source_run.finished_at = naive_utc_now()
            db.commit()
        return report


collection_runner = CollectionRunner()
