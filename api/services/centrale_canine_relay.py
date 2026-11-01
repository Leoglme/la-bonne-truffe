"""
Relay of the Centrale Canine by the desktop app (docs/02-sources.md, docs/05 « Nouveaux relevés »): the API plans
each run and stores it, the Windows app of a computer that is on reads the pages with the curl Cloudflare accepts.

One relay chains, under the same token, the sources the Centrale Canine serves: the litters, then the breeder
directory when its day has come, then the dog pages. The app only sees pages to read and the states
« pages_needed » / « run_finished ». The pages read are kept here for the time of the relay.
"""

import secrets
import threading
from dataclasses import dataclass, field
from datetime import datetime, timedelta

import httpx
from sqlalchemy.orm import Session

from enums.centrale_canine_relay_state import CentraleCanineRelayState
from enums.listing_source import ListingSource
from models.source_run import SourceRun
from schemas.centrale_canine_relay import (
    CentraleCanineRelayAnswer,
    CentraleCanineRelayRequest,
    RelayedPageResponse,
    RelayPageRequest,
)
from schemas.source_activity import CentraleCanineRelayActivity
from services import source_status_service
from services.collection_planner import CollectionPlanner
from services.collection_runner import collection_runner
from services.collectors.centrale_canine import CentraleCanineCollector, CentraleCanineError
from services.collectors.relayed_pages_transport import RelayedPagesTransport, RelayPlanningTransport
from services.collectors.scc_breeders import SccBreederDirectoryCollector
from services.collectors.scc_dogs import SccDogCollector
from services.collectors.scc_sites import SccSiteCollector
from services.dog_collection_planner import DogCollectionPlanner
from services.source_status_service import SourceStatusService

RELAY_LEASE_DURATION = timedelta(minutes=10)

# A relay whose computer has not called back for that long is dead (app closed, PC asleep): the next call takes over.
ABANDONED_RELAY_DELAY = timedelta(minutes=2)

# Pages asked per answer: the app calls back often, so that the relay stays alive and the progress shows.
MAX_PAGE_REQUESTS_PER_ANSWER = 20

# A hidden desktop app still checks about once a minute: silent for that long, its computer is off or asleep.
DESKTOP_APP_PRESENCE_WINDOW = timedelta(minutes=3)

# The order the sources are relayed in, and how long a run of each stays valid.
RELAYED_SOURCE_ORDER: tuple[ListingSource, ...] = (
    ListingSource.CENTRALE_CANINE,
    ListingSource.SCC_BREEDERS,
    ListingSource.SCC_SITES,
    ListingSource.SCC_DOGS,
)
INTERVALS_BETWEEN_RUNS: dict[ListingSource, timedelta] = {
    ListingSource.CENTRALE_CANINE: timedelta(minutes=55),
    ListingSource.SCC_BREEDERS: timedelta(hours=20),
    ListingSource.SCC_SITES: timedelta(hours=20),
    ListingSource.SCC_DOGS: timedelta(minutes=55),
}


class RelayLeaseLostError(RuntimeError):
    """The relay token is not the one of the relay in progress: it expired, or another computer took over."""


@dataclass
class RelayLease:
    """
    The relay a computer holds: its token, until when, its last call, the source it is on, the pages read, and
    how far it is in that source (pages read, pages still asked), for the other devices to show.
    """

    token: str
    expires_at: datetime
    touched_at: datetime
    source: ListingSource
    is_wanted: bool = False
    responses_by_url: dict[str, RelayedPageResponse] = field(default_factory=dict)
    pages_read_count: int = 0
    pages_left_count: int = 0


class CentraleCanineRelay:
    """
    Hands the Centrale Canine runs of the hour to one desktop app, tells it which pages to read, then runs
    the usual collection on them, source after source. The lease lives in memory: the API runs a single process.
    """

    def __init__(self) -> None:
        """Start without any relay in progress, nor any desktop app seen."""
        self.lease: RelayLease | None = None
        self.is_run_requested = False
        self.desktop_app_seen_at: datetime | None = None
        self._lock = threading.Lock()

    def request_run(self) -> None:
        """Have the next desktop app that checks in run every source, even when its last run is recent."""
        with self._lock:
            self.is_run_requested = True

    def answer(
        self, db: Session, relay_request: CentraleCanineRelayRequest, now: datetime
    ) -> CentraleCanineRelayAnswer:
        """
        Answer a call of a desktop app: start a relay, ask for the pages still to read, or run.

        Args:
            db: Database session.
            relay_request: The call, with the pages read since the previous one.
            now: Current time, naive UTC.

        Returns:
            What the desktop app does next.

        Raises:
            RelayLeaseLostError: When the token is not the one of the relay in progress.
        """
        with self._lock:
            self.desktop_app_seen_at = now
            if relay_request.relay_token is None:
                return self._start(db, relay_request.is_requested_by_user, now)
            lease = self.lease
            if lease is None or lease.token != relay_request.relay_token or lease.expires_at <= now:
                raise RelayLeaseLostError("Ce relevé a expiré, ou un autre PC l'a repris")
            lease.touched_at = now
            for response in relay_request.responses:
                if response.url not in lease.responses_by_url:
                    lease.pages_read_count += 1
                lease.responses_by_url[response.url] = response
            return self._advance(db, lease, now)

    def activity(self, now: datetime) -> CentraleCanineRelayActivity:
        """
        Where the relay stands, for every device to show it. Read without the lock, which a run holds for
        seconds: each value is read once, and a call landing in between only shifts the picture by one poll.

        Args:
            now: Current time, naive UTC.

        Returns:
            The relay in progress, if a computer still calls back, the request waiting, and whether a computer is on.
        """
        lease = self.lease
        seen_at = self.desktop_app_seen_at
        is_desktop_app_on = seen_at is not None and now - seen_at < DESKTOP_APP_PRESENCE_WINDOW
        if lease is None or not self._is_alive(lease, now):
            return CentraleCanineRelayActivity(
                is_relaying=False,
                source=None,
                pages_read_count=0,
                pages_left_count=0,
                is_requested=self.is_run_requested,
                is_desktop_app_on=is_desktop_app_on,
            )
        return CentraleCanineRelayActivity(
            is_relaying=True,
            source=lease.source,
            pages_read_count=lease.pages_read_count,
            pages_left_count=lease.pages_left_count,
            is_requested=self.is_run_requested,
            is_desktop_app_on=is_desktop_app_on,
        )

    def _start(self, db: Session, is_requested_by_user: bool, now: datetime) -> CentraleCanineRelayAnswer:
        """
        Give the relay to the calling app, unless another one holds it and still calls back, or no source is
        due and nobody asked. A relay silent for ``ABANDONED_RELAY_DELAY`` is dead: the call takes it over. A
        request made while another computer relays is kept for the next check of any computer.

        Args:
            db: Database session.
            is_requested_by_user: « Relever maintenant »: every source runs, whatever its last run.
            now: Current time, naive UTC.

        Returns:
            The first pages to read, or why there is nothing to do.
        """
        lease = self.lease
        if lease is not None and self._is_alive(lease, now):
            if is_requested_by_user:
                self.is_run_requested = True
            return self._answer(CentraleCanineRelayState.BUSY)
        is_wanted = is_requested_by_user or self.is_run_requested
        first_source = self._next_due_source(db, None, now, is_wanted)
        if first_source is None:
            return self._answer(CentraleCanineRelayState.NOT_DUE)
        self.is_run_requested = False
        lease = RelayLease(
            token=secrets.token_urlsafe(16),
            expires_at=now + RELAY_LEASE_DURATION,
            touched_at=now,
            source=first_source,
            is_wanted=is_wanted,
        )
        return self._advance(db, lease, now)

    def _advance(self, db: Session, lease: RelayLease, now: datetime) -> CentraleCanineRelayAnswer:
        """
        Ask for the pages still to read for the current source; once there are none, run it, then go on
        with the next source due, until none is left.

        Args:
            db: Database session.
            lease: The relay in progress.
            now: Current time, naive UTC.

        Returns:
            The pages to read next, or the statuses after the last run.
        """
        while True:
            unread_page_requests = self._unread_page_requests(db, lease.source, lease, now)
            if unread_page_requests:
                lease.expires_at = now + RELAY_LEASE_DURATION
                lease.pages_left_count = len(unread_page_requests)
                self.lease = lease
                return CentraleCanineRelayAnswer(
                    state=CentraleCanineRelayState.PAGES_NEEDED,
                    relay_token=lease.token,
                    page_requests=unread_page_requests[:MAX_PAGE_REQUESTS_PER_ANSWER],
                    source_statuses=[],
                    source=lease.source,
                )
            self._run(db, lease)
            next_source = self._next_due_source(db, lease.source, now, lease.is_wanted)
            if next_source is None:
                self.lease = None
                return CentraleCanineRelayAnswer(
                    state=CentraleCanineRelayState.RUN_FINISHED,
                    relay_token=None,
                    page_requests=[],
                    source_statuses=SourceStatusService.list_statuses(db),
                    source=lease.source,
                )
            lease.source = next_source
            lease.pages_read_count = 0
            lease.pages_left_count = 0

    def _unread_page_requests(
        self, db: Session, source: ListingSource, lease: RelayLease, now: datetime
    ) -> list[RelayPageRequest]:
        """
        Replay the plan of a source on the pages read so far and list those still to read. A page that came
        back as an error ends the planning: the run then records the error.

        Args:
            db: Database session.
            source: The source being relayed.
            lease: The relay, holding the pages read.
            now: Current time, naive UTC.

        Returns:
            The pages still to read, in the order the collector reads them.
        """
        planning_transport = RelayPlanningTransport(list(lease.responses_by_url.values()))
        try:
            if source == ListingSource.SCC_BREEDERS:
                self._directory_collector_on(planning_transport).collect(
                    CollectionPlanner.build_scc_breeder_directory_plan(db)
                )
            elif source == ListingSource.SCC_SITES:
                self._site_collector_on(planning_transport).collect(CollectionPlanner.build_scc_sites_plan(db, now))
            elif source == ListingSource.SCC_DOGS:
                self._dog_collector_on(planning_transport).collect(DogCollectionPlanner.build(db, now))
            else:
                collector = self._collector_on(planning_transport)
                collector.collect(collection_runner.plan_centrale_canine(db, collector))
        except CentraleCanineError:
            return []
        return planning_transport.unread_page_requests

    def _run(self, db: Session, lease: RelayLease) -> None:
        """
        Run the current source of the relay on the pages read.

        Args:
            db: Database session.
            lease: The relay, holding the pages read.
        """
        transport = RelayedPagesTransport(list(lease.responses_by_url.values()))
        if lease.source == ListingSource.SCC_BREEDERS:
            collection_runner.run_scc_breeders(db, self._directory_collector_on(transport))
        elif lease.source == ListingSource.SCC_SITES:
            collection_runner.run_scc_sites(db, self._site_collector_on(transport))
        elif lease.source == ListingSource.SCC_DOGS:
            collection_runner.run_scc_dogs(db, self._dog_collector_on(transport))
        else:
            collection_runner.run_centrale_canine(db, self._collector_on(transport))

    def _next_due_source(
        self, db: Session, after: ListingSource | None, now: datetime, is_wanted: bool
    ) -> ListingSource | None:
        """
        The next relayed source due, in the order of ``RELAYED_SOURCE_ORDER``: a relay Léo asked for takes
        every source that has something to read, whatever its last run.

        Args:
            db: Database session.
            after: The source just run, None to start from the first one.
            now: Current time, naive UTC.
            is_wanted: Whether the relay was asked for, from the app or from the phone.

        Returns:
            The source, or None when none is due.
        """
        relayed_sources = source_status_service.DESKTOP_RELAYED_SOURCES
        start = RELAYED_SOURCE_ORDER.index(after) + 1 if after is not None else 0
        for source in RELAYED_SOURCE_ORDER[start:]:
            if source not in relayed_sources:
                continue
            if not is_wanted and not self._is_run_due(db, source, now):
                continue
            if self._has_something_to_read(db, source, now):
                return source
        return None

    @staticmethod
    def _is_alive(lease: RelayLease, now: datetime) -> bool:
        """
        Whether the computer holding a relay still calls back: a relay silent for ``ABANDONED_RELAY_DELAY`` is
        dead (app closed, PC asleep), and the next call takes it over.

        Args:
            lease: The relay.
            now: Current time, naive UTC.

        Returns:
            True while the relay runs.
        """
        return lease.expires_at > now and now - lease.touched_at < ABANDONED_RELAY_DELAY

    @staticmethod
    def _is_run_due(db: Session, source: ListingSource, now: datetime) -> bool:
        """
        Whether the last run of a source started long enough ago for a new one.

        Args:
            db: Database session.
            source: The source.
            now: Current time, naive UTC.

        Returns:
            True when there is no run yet, or when the last one started its interval ago or more.
        """
        last_run = db.query(SourceRun).filter(SourceRun.source == source).order_by(SourceRun.started_at.desc()).first()
        return last_run is None or last_run.started_at <= now - INTERVALS_BETWEEN_RUNS[source]

    @staticmethod
    def _has_something_to_read(db: Session, source: ListingSource, now: datetime) -> bool:
        """
        Whether a run of the source would read anything: the dog pages only when a litter needs one, the
        sites only when one is due, the directory only when a department has its identifier.

        Args:
            db: Database session.
            source: The source.
            now: Current time, naive UTC.

        Returns:
            True when the run is worth starting.
        """
        if source == ListingSource.SCC_DOGS:
            return bool(DogCollectionPlanner.build(db, now).litters)
        if source == ListingSource.SCC_SITES:
            return bool(CollectionPlanner.build_scc_sites_plan(db, now).sites)
        if source == ListingSource.SCC_BREEDERS:
            plan = CollectionPlanner.build_scc_breeder_directory_plan(db)
            return bool(plan.breeds and plan.departments)
        return True

    @staticmethod
    def _answer(state: CentraleCanineRelayState) -> CentraleCanineRelayAnswer:
        """
        An answer without pages nor statuses.

        Args:
            state: « busy » or « not_due ».

        Returns:
            The answer.
        """
        return CentraleCanineRelayAnswer(state=state, relay_token=None, page_requests=[], source_statuses=[])

    @staticmethod
    def _collector_on(transport: httpx.BaseTransport) -> CentraleCanineCollector:
        """
        A litters collector that reads through the given transport, without the polite pause: nothing goes on
        the network.

        Args:
            transport: Transport serving the relayed pages.

        Returns:
            The collector.
        """
        return CentraleCanineCollector(http_client=httpx.Client(transport=transport), sleep=lambda _seconds: None)

    @staticmethod
    def _directory_collector_on(transport: httpx.BaseTransport) -> SccBreederDirectoryCollector:
        """
        A directory collector on the given transport, without the polite pause.

        Args:
            transport: Transport serving the relayed pages.

        Returns:
            The collector.
        """
        return SccBreederDirectoryCollector(http_client=httpx.Client(transport=transport), sleep=lambda _seconds: None)

    @staticmethod
    def _dog_collector_on(transport: httpx.BaseTransport) -> SccDogCollector:
        """
        A dog collector on the given transport, without the polite pause.

        Args:
            transport: Transport serving the relayed pages.

        Returns:
            The collector.
        """
        return SccDogCollector(http_client=httpx.Client(transport=transport), sleep=lambda _seconds: None)

    @staticmethod
    def _site_collector_on(transport: httpx.BaseTransport) -> SccSiteCollector:
        """
        A site collector on the given transport, without the polite pause.

        Args:
            transport: Transport serving the relayed pages.

        Returns:
            The collector.
        """
        return SccSiteCollector(http_client=httpx.Client(transport=transport), sleep=lambda _seconds: None)


centrale_canine_relay = CentraleCanineRelay()
