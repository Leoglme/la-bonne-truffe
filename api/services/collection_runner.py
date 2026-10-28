"""Runs one collection on one source and writes its ``source_runs`` line."""

import logging
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from core.clock import naive_utc_now
from enums.listing_source import ListingSource
from enums.source_run_status import SourceRunStatus
from models.breed import Breed
from models.source_run import SourceRun
from services.collection_planner import CollectionPlanner
from services.collectors.centrale_canine import (
    CentraleCanineCollection,
    CentraleCanineCollectionPlan,
    CentraleCanineCollector,
    CentraleCanineError,
)
from services.listing_ingestion import IngestionSummary, listing_ingestion_service
from services.litter_grouping import GroupingResult, litter_grouping_service
from services.matching.match_refresh import RefreshSummary, match_refresh_service
from services.notifier import notifier_service
from services.scc_reference_sync import scc_reference_sync

logger = logging.getLogger(__name__)


@dataclass
class CentraleCanineRunReport:
    """Everything a Centrale Canine run did, for the command line and the worker log."""

    source_run: SourceRun
    plan: CentraleCanineCollectionPlan
    collection: CentraleCanineCollection = field(default_factory=CentraleCanineCollection)
    summary: IngestionSummary = field(default_factory=IngestionSummary)
    grouping: GroupingResult = field(default_factory=GroupingResult)
    refresh: RefreshSummary = field(default_factory=RefreshSummary)


class CollectionRunner:
    """
    Plans, collects and stores a run, then groups the litters, scores them and notifies.

    An error on a source is recorded on its run line, never raised further; three failed runs in a
    row send the « source en panne » alert.
    """

    def run_centrale_canine(self, db: Session, collector: CentraleCanineCollector) -> CentraleCanineRunReport:
        """
        Read the Centrale Canine for the active profiles, store what was found, then regroup, score
        and notify.

        Args:
            db: Database session.
            collector: Collector to read with (a real one, or one on a fake transport in the tests).

        Returns:
            The run report; ``source_run.status`` tells whether it succeeded.
        """
        source_run = SourceRun(source=ListingSource.CENTRALE_CANINE, started_at=naive_utc_now())
        db.add(source_run)
        db.commit()

        plan = CollectionPlanner.build_centrale_canine_plan(db)
        if plan.departments_without_term_id:
            self._sync_department_identifiers(db, collector, plan)
            plan = CollectionPlanner.build_centrale_canine_plan(db)
        report = CentraleCanineRunReport(source_run=source_run, plan=plan)
        if plan.departments_without_term_id:
            logger.info(
                "Centrale Canine: no litter of the breed in %s at the moment, departments not read",
                ", ".join(plan.departments_without_term_id),
            )

        try:
            if not plan.breeds or not plan.departments:
                raise CentraleCanineError("Rien à relever : aucun profil actif avec une race et un département connus")
            report.collection = collector.collect(plan)
            report.summary = listing_ingestion_service.ingest(
                db,
                ListingSource.CENTRALE_CANINE,
                report.collection.listings,
                {department.code for department in plan.departments},
                naive_utc_now(),
            )
            source_run.status = SourceRunStatus.OK
            source_run.listings_seen = report.summary.seen_count
            source_run.listings_new = len(report.summary.new_listing_ids)
            source_run.listings_changed = len(report.summary.changed_listing_ids)
        except Exception as error:
            # A failing source must never stop the others: the error goes to the run line.
            db.rollback()
            source_run.status = SourceRunStatus.ERROR
            source_run.error_message = str(error)[:2000]
            if isinstance(error, CentraleCanineError):
                logger.error("Centrale Canine run failed: %s", error)
            else:
                logger.exception("Centrale Canine run crashed")
        finally:
            source_run.finished_at = naive_utc_now()
            db.commit()

        if source_run.status == SourceRunStatus.OK:
            now = naive_utc_now()
            report.grouping = litter_grouping_service.regroup(db, now)
            report.refresh = match_refresh_service.refresh(db, now, set(report.grouping.born_group_ids))
        else:
            notifier_service.alert_if_source_down(db, ListingSource.CENTRALE_CANINE, naive_utc_now())
        return report

    @staticmethod
    def _sync_department_identifiers(
        db: Session, collector: CentraleCanineCollector, plan: CentraleCanineCollectionPlan
    ) -> None:
        """
        Read the department ``t_ID`` the Centrale Canine lists for each breed of the plan, when a profile
        department has none yet. One request per breed; a failure leaves the plan as it is.

        Args:
            db: Database session.
            collector: Collector to read with.
            plan: The plan whose departments lack an identifier.
        """
        for breed_target in plan.breeds:
            breed = db.get(Breed, breed_target.breed_id)
            if breed is None:
                continue
            try:
                payload = collector.fetch_first_page_of_all_departments(breed_target.scc_slug)
            except CentraleCanineError as error:
                logger.warning("Centrale Canine: department identifiers not read: %s", error)
                return
            scc_reference_sync.sync(db, breed, collector.page_filters(payload))


collection_runner = CollectionRunner()
