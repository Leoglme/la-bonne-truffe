"""
The HTTP client every collector reads its source with: one request per second at most, through the
system ``curl`` (docs/02-sources.md), with errors worded for the run log.
"""

import time
from collections.abc import Callable

import httpx

from services.collectors.system_curl_transport import SystemCurlTransport

MISSING_PAGE_STATUS_CODES: frozenset[int] = frozenset({404, 410})
REFUSED_STATUS_CODE = 403


class SourceReadError(RuntimeError):
    """A source could not be read; the message says why, in French, for the run log."""


class SourcePageMissingError(SourceReadError):
    """The page is gone (404 or 410), like an ad withdrawn between the list and its page."""


class PoliteHttpClient:
    """Sends the GET requests of one source, at most one per ``seconds_between_requests``."""

    def __init__(
        self,
        source_label: str,
        user_agent: str,
        http_client: httpx.Client | None = None,
        seconds_between_requests: float = 1.0,
        sleep: Callable[[float], None] = time.sleep,
        monotonic_clock: Callable[[], float] = time.monotonic,
    ) -> None:
        """
        Prepare the client.

        Args:
            source_label: Name of the source in the error messages (« Chiens de France »).
            user_agent: User-Agent sent with every request.
            http_client: HTTP client, injected by the tests; otherwise one that sends through ``curl``.
            seconds_between_requests: Minimum delay between two requests.
            sleep: Pause function, injected by the tests.
            monotonic_clock: Clock measuring the delay, injected by the tests.
        """
        self.source_label = source_label
        self.user_agent = user_agent
        self.http_client = http_client or httpx.Client(
            timeout=30.0, follow_redirects=True, transport=SystemCurlTransport()
        )
        self.seconds_between_requests = seconds_between_requests
        self.sleep = sleep
        self.monotonic_clock = monotonic_clock
        self._last_request_at: float | None = None

    def get(self, url: str, accept: str, params: dict[str, str] | None = None) -> httpx.Response:
        """
        Send a GET request after the polite delay.

        Args:
            url: Address to read.
            accept: ``Accept`` header.
            params: Query parameters, if any.

        Returns:
            The successful response.

        Raises:
            SourcePageMissingError: When the page is gone.
            SourceReadError: On a network error or any other non-2xx status.
        """
        if self._last_request_at is not None:
            elapsed = self.monotonic_clock() - self._last_request_at
            if elapsed < self.seconds_between_requests:
                self.sleep(self.seconds_between_requests - elapsed)
        headers = {"User-Agent": self.user_agent, "Accept": accept, "Accept-Language": "fr-FR,fr;q=0.9"}
        try:
            response = self.http_client.get(url, params=params, headers=headers)
        except httpx.HTTPError as error:
            raise SourceReadError(f"{self.source_label} injoignable : {error}") from error
        finally:
            self._last_request_at = self.monotonic_clock()

        if response.status_code in MISSING_PAGE_STATUS_CODES:
            raise SourcePageMissingError(f"{self.source_label} : page disparue {response.url}")
        if response.status_code == REFUSED_STATUS_CODE:
            raise SourceReadError(
                f"{self.source_label} : 403, Cloudflare refuse ce client ou cette adresse "
                f"(cf-mitigated={response.headers.get('cf-mitigated', 'absent')})"
            )
        if response.status_code >= 400:
            raise SourceReadError(f"{self.source_label} : HTTP {response.status_code} pour {response.url}")
        return response
