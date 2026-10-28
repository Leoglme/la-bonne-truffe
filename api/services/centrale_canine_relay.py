"""
Relay of the Centrale Canine by the desktop app (docs/02-sources.md): the API plans the run and stores it,
the Windows app of a computer that is on reads the pages with the curl Cloudflare accepts.
"""

import secrets
import threading
from dataclasses import dataclass
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
from services.collection_runner import collection_runner
from services.collectors.centrale_canine import CentraleCanineCollector, CentraleCanineError
from services.collectors.relayed_pages_transport import RelayedPagesTransport, RelayPlanningTransport
from services.source_status_service import SourceStatusService

INTERVAL_BETWEEN_RUNS = timedelta(minutes=55)
RELAY_LEASE_DURATION = timedelta(minutes=10)


class RelayLeaseLostError(RuntimeError):
    """The relay token is not the one of the relay in progress: it expired, or another computer took over."""


@dataclass
class RelayLease:
    """The relay a computer holds: its token, and until when."""

    token: str
    expires_at: datetime


class CentraleCanineRelay:
    """
    Hands the Centrale Canine run of the hour to one desktop app, tells it which pages to read, then runs
    the usual collection on them. The lease lives in memory: the API runs a single process.
    """

    def __init__(self) -> None:
        """Start without any relay in progress."""
        self.lease: RelayLease | None = None
        self._lock = threading.Lock()

    def answer(
        self, db: Session, relay_request: CentraleCanineRelayRequest, now: datetime
    ) -> CentraleCanineRelayAnswer:
        """
        Answer a call of a desktop app: start a relay, ask for the pages still to read, or run.

        Args:
            db: Database session.
            relay_request: The call, with every page read since the relay started.
            now: Current time, naive UTC.

        Returns:
            What the desktop app does next.

        Raises:
            RelayLeaseLostError: When the token is not the one of the relay in progress.
        """
        with self._lock:
            if relay_request.relay_token is None:
                return self._start(db, relay_request.is_requested_by_user, now)
            if not self._is_held_by(relay_request.relay_token, now):
                raise RelayLeaseLostError("Ce relevé a expiré, ou un autre PC l'a repris")
            return self._advance(db, relay_request.relay_token, relay_request.responses, now)

    def _start(self, db: Session, is_requested_by_user: bool, now: datetime) -> CentraleCanineRelayAnswer:
        """
        Give the relay to the calling app, unless another one holds it or the last run is recent.

        Args:
            db: Database session.
            is_requested_by_user: « Relever maintenant »: a recent run does not matter.
            now: Current time, naive UTC.

        Returns:
            The first pages to read, or why there is nothing to do.
        """
        if self.lease is not None and self.lease.expires_at > now:
            return CentraleCanineRelayAnswer(
                state=CentraleCanineRelayState.BUSY, relay_token=None, page_requests=[], source_statuses=[]
            )
        if not is_requested_by_user and not self._is_run_due(db, now):
            return CentraleCanineRelayAnswer(
                state=CentraleCanineRelayState.NOT_DUE, relay_token=None, page_requests=[], source_statuses=[]
            )
        return self._advance(db, secrets.token_urlsafe(16), [], now)

    def _advance(
        self, db: Session, relay_token: str, responses: list[RelayedPageResponse], now: datetime
    ) -> CentraleCanineRelayAnswer:
        """
        Ask for the pages still to read; once there are none, run the collection on the pages read.

        Args:
            db: Database session.
            relay_token: Token of the relay.
            responses: Every page read since the relay started.
            now: Current time, naive UTC.

        Returns:
            The pages to read next, or the statuses after the run.
        """
        unread_page_requests = self._unread_page_requests(db, responses)
        if unread_page_requests:
            self.lease = RelayLease(token=relay_token, expires_at=now + RELAY_LEASE_DURATION)
            return CentraleCanineRelayAnswer(
                state=CentraleCanineRelayState.PAGES_NEEDED,
                relay_token=relay_token,
                page_requests=unread_page_requests,
                source_statuses=[],
            )
        self.lease = None
        collection_runner.run_centrale_canine(db, self._collector_on(RelayedPagesTransport(responses)))
        return CentraleCanineRelayAnswer(
            state=CentraleCanineRelayState.RUN_FINISHED,
            relay_token=None,
            page_requests=[],
            source_statuses=SourceStatusService.list_statuses(db),
        )

    def _unread_page_requests(self, db: Session, responses: list[RelayedPageResponse]) -> list[RelayPageRequest]:
        """
        Replay the plan on the pages read so far and list those still to read. A page that came back as an
        error ends the planning: the run then records the error.

        Args:
            db: Database session.
            responses: Every page read since the relay started.

        Returns:
            The pages still to read, in the order the collector reads them.
        """
        planning_transport = RelayPlanningTransport(responses)
        collector = self._collector_on(planning_transport)
        plan = collection_runner.plan_centrale_canine(db, collector)
        try:
            collector.collect(plan)
        except CentraleCanineError:
            return []
        return planning_transport.unread_page_requests

    def _is_held_by(self, relay_token: str, now: datetime) -> bool:
        """
        Whether the token is the one of the relay in progress.

        Args:
            relay_token: Token sent by the desktop app.
            now: Current time, naive UTC.

        Returns:
            True while the relay is that app's and has not expired.
        """
        return self.lease is not None and self.lease.token == relay_token and self.lease.expires_at > now

    @staticmethod
    def _is_run_due(db: Session, now: datetime) -> bool:
        """
        Whether the last Centrale Canine run started long enough ago for a new one.

        Args:
            db: Database session.
            now: Current time, naive UTC.

        Returns:
            True when there is no run yet, or when the last one started ``INTERVAL_BETWEEN_RUNS`` ago or more.
        """
        last_run = (
            db.query(SourceRun)
            .filter(SourceRun.source == ListingSource.CENTRALE_CANINE)
            .order_by(SourceRun.started_at.desc())
            .first()
        )
        return last_run is None or last_run.started_at <= now - INTERVAL_BETWEEN_RUNS

    @staticmethod
    def _collector_on(transport: httpx.BaseTransport) -> CentraleCanineCollector:
        """
        A collector that reads through the given transport, without the polite pause: nothing goes on the network.

        Args:
            transport: Transport serving the relayed pages.

        Returns:
            The collector.
        """
        return CentraleCanineCollector(http_client=httpx.Client(transport=transport), sleep=lambda _seconds: None)


centrale_canine_relay = CentraleCanineRelay()
