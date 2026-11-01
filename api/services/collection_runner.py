"""Runs one collection on one source and writes its ``source_runs`` line."""

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime

from sqlalchemy.orm import Session

from core.clock import naive_utc_now
from enums.listing_source import ListingSource
from enums.source_run_status import SourceRunStatus
from models.breed import Breed
from models.source_run import SourceRun
from services.breeder_alert_service import BreederRunFacts, breeder_alert_service
from services.breeder_directory_ingestion import breeder_directory_ingestion_service
from services.breeder_site_ingestion import breeder_site_ingestion_service
from services.collection_planner import CollectionPlanner
from services.collectors.centrale_canine import (
    CentraleCanineCollection,
    CentraleCanineCollectionPlan,
    CentraleCanineCollector,
    CentraleCanineError,
)
from services.collectors.chiens_de_france import ChiensDeFranceCollector
from services.collectors.chiens_de_france_sites import (
    ChiensDeFranceSiteCollector,
    SiteCollection,
    SiteCollectionPlan,
)
from services.collectors.chiots_de_france import ChiotsDeFranceCollector
from services.collectors.coeur_de_cocker import CoeurDeCockerCollector
from services.collectors.html_source import HtmlCollection, HtmlCollectionPlan, HtmlSourceCollector
from services.collectors.polite_http_client import SourceReadError
from services.collectors.scc_breeders import (
    SccBreederDirectoryCollection,
    SccBreederDirectoryCollector,
    SccBreederDirectoryPlan,
)
from services.collectors.scc_dogs import SccDogCollection, SccDogCollectionPlan, SccDogCollector
from services.collectors.scc_sites import SccSiteCollection, SccSiteCollectionPlan, SccSiteCollector
from services.collectors.whoof import WhoofCollector
from services.dog_collection_planner import DogCollectionPlanner
from services.dog_ingestion import dog_ingestion_service
from services.listing_ingestion import IngestionSummary, listing_ingestion_service
from services.litter_grouping import GroupingResult, litter_grouping_service
from services.matching.match_refresh import match_refresh_service
from services.notifier import notifier_service
from services.scc_reference_sync import scc_reference_sync
from services.scc_site_ingestion import scc_site_ingestion_service

logger = logging.getLogger(__name__)

INTERRUPTED_RUN_MESSAGE = "Relevé interrompu : le serveur a redémarré pendant le relevé."

NOTHING_TO_COLLECT_MESSAGE = "Rien à relever : aucun profil actif avec une race et un département connus"


@dataclass
class SccBreederDirectoryRunReport:
    """Everything a run of the Centrale Canine breeder directory did."""

    source_run: SourceRun
    plan: SccBreederDirectoryPlan
    collection: SccBreederDirectoryCollection = field(default_factory=SccBreederDirectoryCollection)
    summary: IngestionSummary = field(default_factory=IngestionSummary)
    grouping: GroupingResult = field(default_factory=GroupingResult)


@dataclass
class SccDogRunReport:
    """Everything a run of the Centrale Canine dog pages did."""

    source_run: SourceRun
    plan: SccDogCollectionPlan
    collection: SccDogCollection = field(default_factory=SccDogCollection)
    summary: IngestionSummary = field(default_factory=IngestionSummary)
    grouping: GroupingResult = field(default_factory=GroupingResult)


@dataclass
class SccSitesRunReport:
    """Everything a run of the Centrale Canine sites of the breedings did."""

    source_run: SourceRun
    plan: SccSiteCollectionPlan
    collection: SccSiteCollection = field(default_factory=SccSiteCollection)
    summary: IngestionSummary = field(default_factory=IngestionSummary)
    grouping: GroupingResult = field(default_factory=GroupingResult)


@dataclass
class CentraleCanineRunReport:
    """Everything a Centrale Canine run did, for the command line and the worker log."""

    source_run: SourceRun
    plan: CentraleCanineCollectionPlan
    collection: CentraleCanineCollection = field(default_factory=CentraleCanineCollection)
    summary: IngestionSummary = field(default_factory=IngestionSummary)
    grouping: GroupingResult = field(default_factory=GroupingResult)


@dataclass
class HtmlRunReport:
    """Everything a run of an HTML source did, for the command line and the worker log."""

    source_run: SourceRun
    plan: HtmlCollectionPlan
    collection: HtmlCollection = field(default_factory=HtmlCollection)
    summary: IngestionSummary = field(default_factory=IngestionSummary)
    grouping: GroupingResult = field(default_factory=GroupingResult)


@dataclass
class BreederSitesRunReport:
    """Everything a run of the breeder sites on Chiens de France did."""

    source_run: SourceRun
    plan: SiteCollectionPlan
    collection: SiteCollection = field(default_factory=SiteCollection)
    summary: IngestionSummary = field(default_factory=IngestionSummary)
    grouping: GroupingResult = field(default_factory=GroupingResult)


RunReport = (
    CentraleCanineRunReport
    | HtmlRunReport
    | SccBreederDirectoryRunReport
    | SccSitesRunReport
    | SccDogRunReport
    | BreederSitesRunReport
)


class CollectionRunner:
    """
    Plans, collects and stores a run, then groups the litters, scores them and notifies.

    An error on a source is recorded on its run line, never raised further; three failed runs in a
    row send the « source en panne » alert.
    """

    def run_source(self, db: Session, source: ListingSource) -> RunReport:
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
        if source == ListingSource.CHIOTS_DE_FRANCE:
            return self.run_html_source(db, source, ChiotsDeFranceCollector())
        if source == ListingSource.WHOOF:
            return self.run_html_source(db, source, WhoofCollector())
        if source == ListingSource.COEUR_DE_COCKER:
            return self.run_html_source(db, source, CoeurDeCockerCollector())
        if source == ListingSource.SCC_BREEDERS:
            return self.run_scc_breeders(db, SccBreederDirectoryCollector())
        if source == ListingSource.SCC_DOGS:
            return self.run_scc_dogs(db, SccDogCollector())
        if source == ListingSource.SCC_SITES:
            return self.run_scc_sites(db, SccSiteCollector())
        if source == ListingSource.CHIENS_DE_FRANCE_SITES:
            return self.run_breeder_sites(db, ChiensDeFranceSiteCollector())
        raise ValueError(f"Aucun collecteur pour {source}")

    def run_breeder_sites(self, db: Session, collector: ChiensDeFranceSiteCollector) -> BreederSitesRunReport:
        """
        Read the site of every breeder known on Chiens de France: future litters, puppies for sale with their
        photos, reproducers; then regroup, score and notify.

        Args:
            db: Database session.
            collector: Collector to read with (a real one, or one on a fake transport in the tests).

        Returns:
            The run report; a site that fails is listed in ``collection.failed_sites`` without failing the run.
        """
        source_run = self._open_run(db, ListingSource.CHIENS_DE_FRANCE_SITES)
        plan = CollectionPlanner.build_breeder_sites_plan(db, naive_utc_now())
        report = BreederSitesRunReport(source_run=source_run, plan=plan)

        def collect_and_store() -> IngestionSummary:
            """
            Read the planned sites and store what they bring.

            Returns:
                The ingestion summary.
            """
            report.collection = collector.collect(plan)
            return breeder_site_ingestion_service.ingest(db, plan, report.collection, naive_utc_now())

        report.summary, report.grouping = self._finish_run(db, source_run, collect_and_store)
        return report

    def run_scc_breeders(self, db: Session, collector: SccBreederDirectoryCollector) -> SccBreederDirectoryRunReport:
        """
        Read the breeder directory of the Centrale Canine and the club of the breed, and store the breeders.

        Args:
            db: Database session.
            collector: Collector to read with (a real one, or one on a fake transport in the tests).

        Returns:
            The run report; ``listings_seen`` counts the breeders seen and ``listings_new`` the breeders created.
        """
        source_run = self._open_run(db, ListingSource.SCC_BREEDERS)
        plan = CollectionPlanner.build_scc_breeder_directory_plan(db)
        report = SccBreederDirectoryRunReport(source_run=source_run, plan=plan)

        def collect_and_store() -> IngestionSummary:
            """
            Read the planned pages and store their breeders.

            Returns:
                The ingestion summary.

            Raises:
                CentraleCanineError: When there is nothing to read or the source refuses.
            """
            if not plan.breeds or not plan.departments:
                raise CentraleCanineError(NOTHING_TO_COLLECT_MESSAGE)
            report.collection = collector.collect(plan)
            directory_summary = breeder_directory_ingestion_service.ingest(
                db, report.collection.profiles, naive_utc_now()
            )
            return IngestionSummary(
                seen_count=directory_summary.seen_count,
                new_breeder_or_dog_count=len(directory_summary.new_breeder_ids),
                changed_breeder_or_dog_count=len(directory_summary.updated_breeder_ids),
            )

        report.summary, report.grouping = self._finish_run(db, source_run, collect_and_store)
        return report

    def run_scc_dogs(self, db: Session, collector: SccDogCollector) -> SccDogRunReport:
        """
        Read the Centrale Canine pages of the litters that need them (parents, registered puppies), store the
        dogs, then re-evaluate the litters whose colours the dogs settle.

        Args:
            db: Database session.
            collector: Collector to read with (a real one, or one on a fake transport in the tests).

        Returns:
            The run report; ``listings_seen`` counts the dogs read and ``listings_new`` the dogs created.
        """
        source_run = self._open_run(db, ListingSource.SCC_DOGS)
        plan = DogCollectionPlanner.build(db, naive_utc_now())
        report = SccDogRunReport(source_run=source_run, plan=plan)

        def collect_and_store() -> IngestionSummary:
            """
            Read the planned pages and store their dogs.

            Returns:
                The ingestion summary.
            """
            report.collection = collector.collect(plan)
            dog_summary = dog_ingestion_service.ingest(
                db, report.collection.dogs, report.collection.litter_details, naive_utc_now()
            )
            return IngestionSummary(
                seen_count=dog_summary.seen_count,
                new_breeder_or_dog_count=len(dog_summary.new_dog_ids),
                changed_breeder_or_dog_count=len(dog_summary.changed_group_ids),
            )

        report.summary, report.grouping = self._finish_run(db, source_run, collect_and_store)
        return report

    def run_scc_sites(self, db: Session, collector: SccSiteCollector) -> SccSitesRunReport:
        """
        Read the Centrale Canine site of the breedings whose turn has come, and store their photos.

        Args:
            db: Database session.
            collector: Collector to read with (a real one, or one on a fake transport in the tests).

        Returns:
            The run report; ``listings_seen`` counts the sites read and ``listings_changed`` the breeders whose
            photos changed.
        """
        source_run = self._open_run(db, ListingSource.SCC_SITES)
        plan = CollectionPlanner.build_scc_sites_plan(db, naive_utc_now())
        report = SccSitesRunReport(source_run=source_run, plan=plan)

        def collect_and_store() -> IngestionSummary:
            """
            Read the planned sites and store their photos.

            Returns:
                The ingestion summary.
            """
            report.collection = collector.collect(plan)
            site_summary = scc_site_ingestion_service.ingest(db, report.collection.sites, naive_utc_now())
            return IngestionSummary(
                seen_count=site_summary.seen_count,
                changed_breeder_or_dog_count=len(site_summary.updated_breeder_ids),
            )

        report.summary, report.grouping = self._finish_run(db, source_run, collect_and_store)
        return report

    def plan_centrale_canine(self, db: Session, collector: CentraleCanineCollector) -> CentraleCanineCollectionPlan:
        """
        Plan a Centrale Canine run, after reading the identifiers a profile department lacks.

        Args:
            db: Database session.
            collector: Collector that reads the « all departments » page when an identifier is missing.

        Returns:
            The plan.
        """
        plan = CollectionPlanner.build_centrale_canine_plan(db)
        if plan.departments_without_term_id:
            self._sync_department_identifiers(db, collector, plan)
            plan = CollectionPlanner.build_centrale_canine_plan(db)
        return plan

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
        plan = self.plan_centrale_canine(db, collector)
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

        report.summary, report.grouping = self._finish_run(db, source_run, collect_and_store)
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

        report.summary, report.grouping = self._finish_run(db, source_run, collect_and_store)
        return report

    @staticmethod
    def close_interrupted_runs(db: Session, now: datetime) -> int:
        """
        Close as failed the runs still « running » that started before now: the process that ran them stopped
        (a deployment restarts the API and the worker together), and nothing else would ever close them.

        Args:
            db: Database session; committed.
            now: Start of the process that calls, naive UTC.

        Returns:
            How many runs were closed.
        """
        interrupted_runs = (
            db.query(SourceRun).filter(SourceRun.status == SourceRunStatus.RUNNING, SourceRun.started_at < now).all()
        )
        for source_run in interrupted_runs:
            source_run.status = SourceRunStatus.ERROR
            source_run.finished_at = now
            source_run.error_message = INTERRUPTED_RUN_MESSAGE
        db.commit()
        return len(interrupted_runs)

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
    ) -> tuple[IngestionSummary, GroupingResult]:
        """
        Collect and store, then regroup, score and notify, and record the outcome on the run line: a crash in
        the grouping or the matching fails the run, and the next run finds the births again; after a failure,
        send the « source en panne » alert when it is due.

        Args:
            db: Database session.
            source_run: The run line.
            collect_and_store: Reads the source and stores its listings.

        Returns:
            The ingestion summary and the grouping, empty after a failure.
        """
        summary = IngestionSummary()
        try:
            summary = collect_and_store()
            should_notify = CollectionRunner._has_succeeded_before(db, source_run)
            now = naive_utc_now()
            grouping = litter_grouping_service.regroup(db, now)
            match_refresh_service.refresh(
                db,
                now,
                set(grouping.born_group_ids),
                should_notify=should_notify,
                fewer_puppies_group_ids=set(grouping.fewer_puppies_group_ids),
            )
            breeder_alert_service.raise_events(
                db,
                BreederRunFacts(
                    new_group_ids=set(grouping.new_group_ids),
                    born_group_ids=set(grouping.born_group_ids),
                    new_listing_ids=list(summary.new_listing_ids),
                    changed_listing_ids=list(summary.changed_listing_ids),
                    run_started_at=source_run.started_at,
                ),
                now,
                should_notify=should_notify,
            )
            source_run.status = SourceRunStatus.OK
        except Exception as error:
            # A failing source must never stop the others: the error goes to the run line.
            db.rollback()
            grouping = GroupingResult()
            source_run.status = SourceRunStatus.ERROR
            source_run.error_message = str(error)[:2000]
            if isinstance(error, SourceReadError):
                logger.error("%s run failed: %s", source_run.source, error)
            else:
                logger.exception("%s run crashed", source_run.source)
        finally:
            source_run.listings_seen = summary.seen_count
            source_run.listings_new = len(summary.new_listing_ids) + summary.new_breeder_or_dog_count
            source_run.listings_changed = len(summary.changed_listing_ids) + summary.changed_breeder_or_dog_count
            source_run.finished_at = naive_utc_now()
            db.commit()

        if source_run.status != SourceRunStatus.OK:
            notifier_service.alert_if_source_down(db, source_run.source, naive_utc_now())
        return summary, grouping

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
