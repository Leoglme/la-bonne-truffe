"""Runs one collection on one source and writes its ``source_runs`` line."""

import logging
from collections.abc import Callable
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
from services.collectors.chiens_de_france import ChiensDeFranceCollector
from services.collectors.html_source import HtmlCollection, HtmlCollectionPlan, HtmlSourceCollector
from services.collectors.polite_http_client import SourceReadError
from services.listing_ingestion import IngestionSummary, listing_ingestion_service
from services.litter_grouping import GroupingResult, litter_grouping_service
from services.matching.match_refresh import RefreshSummary, match_refresh_service
from services.notifier import notifier_service
from services.scc_reference_sync import scc_reference_sync

logger = logging.getLogger(__name__)

NOTHING_TO_COLLECT_MESSAGE = "Rien à relever : aucun profil actif avec une race et un département connus"


@dataclass
class CentraleCanineRunReport:
    """Everything a Centrale Canine run did, for the command line and the worker log."""

    source_run: SourceRun
    plan: CentraleCanineCollectionPlan
    collection: CentraleCanineCollection = field(default_factory=CentraleCanineCollection)
    summary: IngestionSummary = field(default_factory=IngestionSummary)
    grouping: GroupingResult = field(default_factory=GroupingResult)
    refresh: RefreshSummary = field(default_factory=RefreshSummary)


@dataclass
class HtmlRunReport:
    """Everything a run of an HTML source did, for the command line and the worker log."""

    source_run: SourceRun
    plan: HtmlCollectionPlan
    collection: HtmlCollection = field(default_factory=HtmlCollection)
    summary: IngestionSummary = field(default_factory=IngestionSummary)
    grouping: GroupingResult = field(default_factory=GroupingResult)
    refresh: RefreshSummary = field(default_factory=RefreshSummary)


class CollectionRunner:
    """
    Plans, collects and stores a run, then groups the litters, scores them and notifies.

    An error on a source is recorded on its run line, never raised further; three failed runs in a
    row send the « source en panne » alert.
    """

    def run_source(self, db: Session, source: ListingSource) -> CentraleCanineRunReport | HtmlRunReport:
        """
        Run a source with its real collector.

        Args:
            db: Database session.
            source: A collected source.

        Returns:
            The run report.

        Raises:
            ValueError: For a source without collector.
        """
        if source == ListingSource.CENTRALE_CANINE:
            return self.run_centrale_canine(db, CentraleCanineCollector())
        if source == ListingSource.CHIENS_DE_FRANCE:
            return self.run_html_source(db, source, ChiensDeFranceCollector())
        raise ValueError(f"Aucun collecteur pour {source}")

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
        source_run = self._open_run(db, ListingSource.CENTRALE_CANINE)
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

        def collect_and_store() -> IngestionSummary:
            """
            Read the planned pages and store their listings.

            Returns:
                The ingestion summary.

            Raises:
                CentraleCanineError: When there is nothing to read or the source refuses.
            """
            if not plan.breeds or not plan.departments:
                raise CentraleCanineError(NOTHING_TO_COLLECT_MESSAGE)
            report.collection = collector.collect(plan)
            return listing_ingestion_service.ingest(
                db,
                ListingSource.CENTRALE_CANINE,
                report.collection.listings,
                {department.code for department in plan.departments},
                naive_utc_now(),
            )

        report.summary, report.grouping, report.refresh = self._finish_run(db, source_run, collect_and_store)
        return report

    def run_html_source(self, db: Session, source: ListingSource, collector: HtmlSourceCollector) -> HtmlRunReport:
        """
        Read an HTML source for the active profiles, store what was found, then regroup, score and notify.

        Args:
            db: Database session.
            source: The HTML source.
            collector: Collector of that source (a real one, or one on a fake transport in the tests).

        Returns:
            The run report; ``source_run.status`` tells whether it succeeded.
        """
        source_run = self._open_run(db, source)
        plan = CollectionPlanner.build_html_plan(db, source)
        report = HtmlRunReport(source_run=source_run, plan=plan)

        def collect_and_store() -> IngestionSummary:
            """
            Read the planned pages and store their listings.

            Returns:
                The ingestion summary.

            Raises:
                SourceReadError: When there is nothing to read or the source refuses.
            """
            if not plan.breeds or not plan.departments:
                raise SourceReadError(NOTHING_TO_COLLECT_MESSAGE)
            report.collection = collector.collect(plan)
            return listing_ingestion_service.ingest(
                db, source, report.collection.listings, report.collection.collected_department_codes, naive_utc_now()
            )

        report.summary, report.grouping, report.refresh = self._finish_run(db, source_run, collect_and_store)
        return report

    @staticmethod
    def _open_run(db: Session, source: ListingSource) -> SourceRun:
        """
        Write the line of a run that starts.

        Args:
            db: Database session; committed.
            source: Source of the run.

        Returns:
            The run line.
        """
        source_run = SourceRun(source=source, started_at=naive_utc_now())
        db.add(source_run)
        db.commit()
        return source_run

    @staticmethod
    def _finish_run(
        db: Session, source_run: SourceRun, collect_and_store: Callable[[], IngestionSummary]
    ) -> tuple[IngestionSummary, GroupingResult, RefreshSummary]:
        """
        Collect and store, record the outcome on the run line, then regroup, score and notify; after a
        failure, send the « source en panne » alert when it is due.

        Args:
            db: Database session.
            source_run: The run line.
            collect_and_store: Reads the source and stores its listings.

        Returns:
            The ingestion summary, the grouping and the match refresh, empty after a failure.
        """
        summary = IngestionSummary()
        try:
            summary = collect_and_store()
            source_run.status = SourceRunStatus.OK
            source_run.listings_seen = summary.seen_count
            source_run.listings_new = len(summary.new_listing_ids)
            source_run.listings_changed = len(summary.changed_listing_ids)
        except Exception as error:
            # A failing source must never stop the others: the error goes to the run line.
            db.rollback()
            source_run.status = SourceRunStatus.ERROR
            source_run.error_message = str(error)[:2000]
            if isinstance(error, SourceReadError):
                logger.error("%s run failed: %s", source_run.source, error)
            else:
                logger.exception("%s run crashed", source_run.source)
        finally:
            source_run.finished_at = naive_utc_now()
            db.commit()

        if source_run.status != SourceRunStatus.OK:
            notifier_service.alert_if_source_down(db, source_run.source, naive_utc_now())
            return summary, GroupingResult(), RefreshSummary()
        now = naive_utc_now()
        grouping = litter_grouping_service.regroup(db, now)
        refresh = match_refresh_service.refresh(
            db,
            now,
            set(grouping.born_group_ids),
            should_notify=CollectionRunner._has_succeeded_before(db, source_run),
        )
        return summary, grouping, refresh

    @staticmethod
    def _has_succeeded_before(db: Session, source_run: SourceRun) -> bool:
        """
        Whether the source already had a successful run. Its first one only records what was already
        online before La Bonne Truffe watched it: nothing of it is news, even an ad without a date.

        Args:
            db: Database session.
            source_run: The run that just succeeded.

        Returns:
            True when an earlier run of the source succeeded.
        """
        return (
            db.query(SourceRun)
            .filter(
                SourceRun.source == source_run.source,
                SourceRun.status == SourceRunStatus.OK,
                SourceRun.id != source_run.id,
            )
            .first()
            is not None
        )

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
