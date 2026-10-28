"""
Centrale Canine collector: the public JSON of the LOF litters, born and to be born.

Endpoint, parameters and fields are documented in docs/02-sources.md. Politeness: one request per
second at most, a browser User-Agent (the site refuses any other), never any protection bypass.
"""

import logging
import math
import time
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from typing import Any

import httpx

from enums.color_confidence import ColorConfidence
from enums.listing_kind import ListingKind
from enums.listing_source import ListingSource
from enums.lof_status import LofStatus
from services.collectors.raw_listing import ColorReading, RawListing
from services.collectors.scc_value_parser import SccValueParser

logger = logging.getLogger(__name__)

SCC_BASE_URL = "https://www.centrale-canine.fr"

# A plain browser User-Agent: the Centrale Canine answers 403 to any other (docs/02-sources.md).
SCC_BROWSER_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
)


class CentraleCanineError(RuntimeError):
    """The Centrale Canine could not be read; the message says why, in French, for the run log."""


@dataclass(frozen=True)
class SccVarietyTarget:
    """Canonical colours of one Centrale Canine variety identifier."""

    covered_colors: tuple[str, ...]
    is_ambiguous: bool


@dataclass(frozen=True)
class SccBreedTarget:
    """A breed to read, with the colour meaning of its varieties."""

    breed_id: int
    scc_slug: str
    varieties_by_source_id: dict[str, SccVarietyTarget]


@dataclass(frozen=True)
class SccDepartmentTarget:
    """A department to read, with the taxonomy identifier the ``department`` filter expects."""

    code: str
    scc_term_id: str


@dataclass(frozen=True)
class CentraleCanineCollectionPlan:
    """What one run reads: every breed of the active profiles, in every department that has a ``t_ID``."""

    breeds: tuple[SccBreedTarget, ...]
    departments: tuple[SccDepartmentTarget, ...]
    departments_without_term_id: tuple[str, ...] = ()


@dataclass(frozen=True)
class SccRawPage:
    """One JSON page exactly as received, kept for ``cli.py collect --save-raw``."""

    scc_slug: str
    department_code: str
    page_number: int
    payload: dict[str, Any]


@dataclass
class CentraleCanineCollection:
    """Listings read by a run, and the raw pages they come from."""

    listings: list[RawListing] = field(default_factory=list)
    raw_pages: list[SccRawPage] = field(default_factory=list)


class CentraleCanineCollector:
    """Reads the litters JSON page by page, politely, and turns each litter into a ``RawListing``."""

    PAGE_SIZE = 10
    MAX_PAGES_PER_QUERY = 100

    def __init__(
        self,
        http_client: httpx.Client | None = None,
        seconds_between_requests: float = 1.0,
        sleep: Callable[[float], None] = time.sleep,
        monotonic_clock: Callable[[], float] = time.monotonic,
    ) -> None:
        """
        Prepare the collector.

        Args:
            http_client: HTTP client, injected by the tests; a real one is created otherwise.
            seconds_between_requests: Minimum delay between two requests (politeness).
            sleep: Pause function, injected by the tests.
            monotonic_clock: Clock measuring the delay, injected by the tests.
        """
        self.http_client = http_client or httpx.Client(timeout=30.0, follow_redirects=True)
        self.seconds_between_requests = seconds_between_requests
        self.sleep = sleep
        self.monotonic_clock = monotonic_clock
        self._last_request_at: float | None = None

    @staticmethod
    def litters_url(scc_slug: str, page_number: int) -> str:
        """
        URL of one page of the litters JSON of a breed.

        Args:
            scc_slug: Breed slug at the Centrale Canine (``cocker-spaniel-anglais``).
            page_number: Page, starting at 0.

        Returns:
            The URL, query string excluded.
        """
        return f"{SCC_BASE_URL}/api/breed/le-chien-de-race--{scc_slug}/chiots-de-la-race/{page_number}"

    @staticmethod
    def breed_page_url(scc_slug: str) -> str:
        """
        URL of the public « chiots de la race » page, whose ``<select>`` lists the filter identifiers.

        Args:
            scc_slug: Breed slug at the Centrale Canine.

        Returns:
            The URL.
        """
        return f"{SCC_BASE_URL}/le-chien-de-race/{scc_slug}/chiots-de-la-race"

    def collect(self, plan: CentraleCanineCollectionPlan) -> CentraleCanineCollection:
        """
        Read every page of every breed and department of the plan.

        Args:
            plan: Breeds and departments to read.

        Returns:
            The listings found and the raw pages.

        Raises:
            CentraleCanineError: When a page cannot be read; the run fails as a whole.
        """
        collection = CentraleCanineCollection()
        for breed in plan.breeds:
            for department in plan.departments:
                for raw_page in self._iterate_pages(breed.scc_slug, department):
                    collection.raw_pages.append(raw_page)
                    collection.listings.extend(self.parse_litters_payload(raw_page.payload, breed, department.code))
        return collection

    def fetch_breed_page_html(self, scc_slug: str) -> str:
        """
        Read the public breed page, for its filter ``<select>`` elements.

        Args:
            scc_slug: Breed slug at the Centrale Canine.

        Returns:
            The HTML.

        Raises:
            CentraleCanineError: When the page cannot be read.
        """
        response = self._get(self.breed_page_url(scc_slug), params={}, accept="text/html")
        return response.text

    def _iterate_pages(self, scc_slug: str, department: SccDepartmentTarget) -> Iterator[SccRawPage]:
        """
        Yield the pages of one breed in one department, the first page giving the total.

        Args:
            scc_slug: Breed slug at the Centrale Canine.
            department: Department filter.

        Yields:
            Each page as received.
        """
        page_count = 1
        page_number = 0
        while page_number < page_count:
            payload = self._fetch_litters_page(scc_slug, department.scc_term_id, page_number)
            yield SccRawPage(scc_slug, department.code, page_number, payload)
            if page_number == 0:
                litter_count = SccValueParser.to_int(self._litters_block(payload).get("count")) or 0
                page_count = min(math.ceil(litter_count / self.PAGE_SIZE), self.MAX_PAGES_PER_QUERY)
            page_number += 1

    def _fetch_litters_page(self, scc_slug: str, department_term_id: str, page_number: int) -> dict[str, Any]:
        """
        Read one page of the litters JSON, every variety, born and to be born.

        Args:
            scc_slug: Breed slug at the Centrale Canine.
            department_term_id: ``t_ID`` of the department.
            page_number: Page, starting at 0.

        Returns:
            The decoded JSON object.

        Raises:
            CentraleCanineError: When the page cannot be read or is not a JSON object.
        """
        response = self._get(
            self.litters_url(scc_slug, page_number),
            params={
                "department": department_term_id,
                "variety": "all",
                "is_borned": "all",
                "sort": "0",
                "_format": "json",
            },
            accept="application/json",
        )
        try:
            payload = response.json()
        except ValueError as error:
            raise CentraleCanineError(f"Réponse non JSON pour {response.url}") from error
        if not isinstance(payload, dict):
            raise CentraleCanineError(f"Réponse JSON inattendue pour {response.url} : objet attendu")
        return payload

    def _get(self, url: str, params: dict[str, str], accept: str) -> httpx.Response:
        """
        Send a GET request, at most one per ``seconds_between_requests``.

        Args:
            url: Address to read.
            params: Query parameters.
            accept: ``Accept`` header.

        Returns:
            The successful response.

        Raises:
            CentraleCanineError: On a network error or a non-2xx status.
        """
        if self._last_request_at is not None:
            elapsed = self.monotonic_clock() - self._last_request_at
            if elapsed < self.seconds_between_requests:
                self.sleep(self.seconds_between_requests - elapsed)
        headers = {"User-Agent": SCC_BROWSER_USER_AGENT, "Accept": accept, "Accept-Language": "fr-FR,fr;q=0.9"}
        try:
            response = self.http_client.get(url, params=params, headers=headers)
        except httpx.HTTPError as error:
            raise CentraleCanineError(f"Centrale Canine injoignable : {error}") from error
        finally:
            self._last_request_at = self.monotonic_clock()

        if response.status_code == 403:
            raise CentraleCanineError(
                "Centrale Canine : 403, Cloudflare refuse cette adresse IP "
                f"(cf-mitigated={response.headers.get('cf-mitigated', 'absent')})"
            )
        if response.status_code >= 400:
            raise CentraleCanineError(f"Centrale Canine : HTTP {response.status_code} pour {response.url}")
        return response

    @staticmethod
    def _litters_block(payload: dict[str, Any]) -> dict[str, Any]:
        """
        The ``litters`` object of a page, empty when missing.

        Args:
            payload: Decoded page.

        Returns:
            The ``{"count", "node"}`` object.
        """
        litters = payload.get("litters")
        return litters if isinstance(litters, dict) else {}

    def parse_litters_payload(
        self, payload: dict[str, Any], breed: SccBreedTarget, department_code: str
    ) -> list[RawListing]:
        """
        Turn one page into listings. Litters are grouped by breeding quality (``1``, ``2``, ``3``).

        Args:
            payload: Decoded page.
            breed: Breed read, with its varieties.
            department_code: Department of the ``department`` filter used for this page.

        Returns:
            The listings of the page; a litter without identifier is skipped and logged.
        """
        nodes_by_group = self._litters_block(payload).get("node")
        # PHP encodes an empty associative array as a JSON list.
        if not isinstance(nodes_by_group, dict):
            return []
        listings: list[RawListing] = []
        for litters_of_group in nodes_by_group.values():
            if not isinstance(litters_of_group, dict):
                continue
            for litter in litters_of_group.values():
                if not isinstance(litter, dict):
                    continue
                listing = self.parse_litter(litter, breed, department_code)
                if listing is None:
                    logger.warning("Centrale Canine litter without n_id skipped: %s", sorted(litter)[:10])
                    continue
                listings.append(listing)
        return listings

    @staticmethod
    def parse_litter(litter: dict[str, Any], breed: SccBreedTarget, department_code: str) -> RawListing | None:
        """
        Turn one litter object into a listing, in the canonical vocabulary.

        Before the birth the Centrale Canine reports 0 males and 0 females: these counts are unknown,
        not zero, so they are stored as None until the litter is born.

        Args:
            litter: One ``n<id>`` object of the JSON.
            breed: Breed read, with its varieties.
            department_code: Department of the ``department`` filter.

        Returns:
            The listing, or None when the litter has no ``n_id``.
        """
        external_id = SccValueParser.to_text(litter.get("n_id"))
        if external_id is None:
            return None

        is_born = SccValueParser.to_bool(litter.get("n_is_borned"))
        birth_date = SccValueParser.to_french_date(litter.get("n_birth_date"))
        if is_born is None:
            is_born = birth_date is not None

        variety_source_id = SccValueParser.to_text(litter.get("n_variety_id"))
        variety = breed.varieties_by_source_id.get(variety_source_id or "")
        colors: tuple[ColorReading, ...] = ()
        if variety is not None:
            confidence = ColorConfidence.AMBIGUOUS if variety.is_ambiguous else ColorConfidence.CERTAIN
            colors = tuple(ColorReading(color, confidence.value) for color in variety.covered_colors)

        relative_url = SccValueParser.to_text(litter.get("url"))
        image_uri = SccValueParser.to_text(litter.get("n_image_uri"))

        return RawListing(
            source=ListingSource.CENTRALE_CANINE.value,
            external_id=external_id,
            breed_id=breed.breed_id,
            kind=(ListingKind.LITTER_BORN if is_born else ListingKind.LITTER_EXPECTED).value,
            # Every litter declared to the Centrale Canine goes to the LOF.
            lof_status=LofStatus.LOF.value,
            external_url=CentraleCanineCollector._absolute_url(relative_url),
            litter_number=SccValueParser.to_text(litter.get("n_litter_number")),
            mating_date=SccValueParser.to_french_date(litter.get("n_servicing_date")),
            birth_date=birth_date,
            male_count=SccValueParser.to_int(litter.get("n_male_number")) if is_born else None,
            female_count=SccValueParser.to_int(litter.get("n_female_number")) if is_born else None,
            variety_source_id=variety_source_id,
            colors=colors,
            color_text=SccValueParser.to_text(litter.get("n_variety")),
            department_code=department_code,
            sire_name=SccValueParser.to_text(litter.get("n_father_name")),
            sire_rating=SccValueParser.to_int(litter.get("n_father_notation")),
            dam_name=SccValueParser.to_text(litter.get("n_mother_name")),
            dam_rating=SccValueParser.to_int(litter.get("n_mother_notation")),
            litter_rating=SccValueParser.to_float(litter.get("n_average_notation")),
            photos=tuple(url for url in (CentraleCanineCollector._absolute_url(image_uri),) if url),
            breeder_source_id=SccValueParser.to_text(litter.get("n_breeder_id")),
            breeder_selection_group=SccValueParser.to_int(litter.get("n_selection")),
            source_changed_at=SccValueParser.to_datetime(litter.get("n_changed")),
            raw_json=litter,
        )

    @staticmethod
    def _absolute_url(path_or_url: str | None) -> str | None:
        """
        Make a site-relative path absolute.

        Args:
            path_or_url: ``/portee/123`` or an absolute URL.

        Returns:
            The absolute URL, or None when empty.
        """
        if not path_or_url:
            return None
        if path_or_url.startswith(("http://", "https://")):
            return path_or_url
        return f"{SCC_BASE_URL}/{path_or_url.lstrip('/')}"
