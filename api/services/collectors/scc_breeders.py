"""
Centrale Canine breeder directory collector: the breeders of a breed in each department of the profiles, and
the members of the club of the breed (docs/02, « Annuaire des éleveurs de la race », « Spaniel Club Français »).

Same access rules as the litters: a browser User-Agent, one request per second, relayed by the desktop app
when the server is refused.
"""

import logging
import math
import time
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from functools import partial
from typing import Any

import httpx

from services.collectors.breeder_contact_parser import BreederContactParser
from services.collectors.centrale_canine import (
    SCC_BASE_URL,
    SCC_BROWSER_USER_AGENT,
    SccDepartmentTarget,
    SccJsonPage,
    fetch_json_page,
    read_scc_breeder_contact,
    scc_absolute_url,
)
from services.collectors.polite_http_client import PoliteHttpClient
from services.collectors.raw_dog import RawBreederProfile
from services.collectors.scc_value_parser import SccValueParser

logger = logging.getLogger(__name__)

DIRECTORY_PAGE_SIZE = 10
MAX_DIRECTORY_PAGES = 400
CLUB_API_PATH = "/spaniel-club-francais/api/breeders"

# The node identifier the club API filters on (``n_race`` of the litters), per Centrale Canine breed slug.
CLUB_BREED_NODE_IDS: dict[str, str] = {"cocker-spaniel-anglais": "1728"}


@dataclass(frozen=True)
class SccDirectoryBreedTarget:
    """A breed to read in the directory, with the identifier the club API filters on when the club lists it."""

    breed_id: int
    scc_slug: str
    club_breed_node_id: str | None = None


@dataclass(frozen=True)
class SccBreederDirectoryPlan:
    """What one run reads: the directory of each breed in each department, then the club of each breed."""

    breeds: tuple[SccDirectoryBreedTarget, ...]
    departments: tuple[SccDepartmentTarget, ...]


@dataclass
class SccBreederDirectoryCollection:
    """Breeder profiles read by a run, and the raw pages they come from."""

    profiles: list[RawBreederProfile] = field(default_factory=list)
    raw_pages: list[SccJsonPage] = field(default_factory=list)


class SccBreederDirectoryCollector:
    """Reads the directory JSON page by page, politely, and turns each entry into a ``RawBreederProfile``."""

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
            http_client: HTTP client, injected by the tests; otherwise one that sends through the system
                ``curl``, which Cloudflare accepts where it refuses Python (docs/02-sources.md).
            seconds_between_requests: Minimum delay between two requests (politeness).
            sleep: Pause function, injected by the tests.
            monotonic_clock: Clock measuring the delay, injected by the tests.
        """
        self.polite_client = PoliteHttpClient(
            "Centrale Canine", SCC_BROWSER_USER_AGENT, http_client, seconds_between_requests, sleep, monotonic_clock
        )

    @staticmethod
    def directory_url(scc_slug: str, page_number: int) -> str:
        """
        URL of one page of the breeder directory of a breed.

        Args:
            scc_slug: Breed slug at the Centrale Canine (``cocker-spaniel-anglais``).
            page_number: Page, starting at 0.

        Returns:
            The URL, query string excluded.
        """
        return f"{SCC_BASE_URL}/api/breed/le-chien-de-race--{scc_slug}/eleveurs/{page_number}"

    @staticmethod
    def club_url(page_number: int) -> str:
        """
        URL of one page of the breeders the Spaniel Club Français lists.

        Args:
            page_number: Page, starting at 0.

        Returns:
            The URL, query string excluded.
        """
        return f"{SCC_BASE_URL}{CLUB_API_PATH}/{page_number}"

    def collect(self, plan: SccBreederDirectoryPlan) -> SccBreederDirectoryCollection:
        """
        Read the directory of every breed in every department of the plan, then the club of every breed it lists.

        Args:
            plan: Breeds and departments to read.

        Returns:
            The profiles found and the raw pages.

        Raises:
            CentraleCanineError: When a page cannot be read; the run fails as a whole.
        """
        collection = SccBreederDirectoryCollection()
        for breed in plan.breeds:
            for department in plan.departments:
                params = {"department": department.scc_term_id, "variety": "all", "_format": "json"}
                for raw_page in self._iterate_pages(partial(self.directory_url, breed.scc_slug), params):
                    collection.raw_pages.append(raw_page)
                    collection.profiles.extend(self.parse_profiles(raw_page.payload, is_from_club=False))
            if breed.club_breed_node_id is None:
                continue
            club_params = {"filter": breed.club_breed_node_id, "_format": "json"}
            for raw_page in self._iterate_pages(self.club_url, club_params):
                collection.raw_pages.append(raw_page)
                collection.profiles.extend(self.parse_profiles(raw_page.payload, is_from_club=True))
        return collection

    def _iterate_pages(self, url_of_page: Callable[[int], str], params: dict[str, str]) -> Iterator[SccJsonPage]:
        """
        Yield the pages of one listing, the first page giving the total.

        Args:
            url_of_page: Builds the URL of a page number.
            params: Query parameters of every page.

        Yields:
            Each page as received.
        """
        page_count = 1
        page_number = 0
        while page_number < page_count:
            url = url_of_page(page_number)
            payload = fetch_json_page(self.polite_client, url, params)
            yield SccJsonPage(url, payload)
            if page_number == 0:
                breeder_count = SccValueParser.to_int(self._breeders_block(payload).get("count")) or 0
                page_count = min(math.ceil(breeder_count / DIRECTORY_PAGE_SIZE), MAX_DIRECTORY_PAGES)
            page_number += 1

    @staticmethod
    def _breeders_block(payload: dict[str, Any]) -> dict[str, Any]:
        """
        The ``breeders`` object of a page, empty when missing (a page not relayed yet looks like that).

        Args:
            payload: Decoded page.

        Returns:
            The ``{"count", "users", "filters"}`` object.
        """
        breeders = payload.get("breeders")
        return breeders if isinstance(breeders, dict) else {}

    @classmethod
    def parse_profiles(cls, payload: dict[str, Any], is_from_club: bool) -> list[RawBreederProfile]:
        """
        Turn one page into breeder profiles.

        Args:
            payload: Decoded page.
            is_from_club: Whether the page lists the members of the club: each profile is then a member.

        Returns:
            The profiles of the page; an entry without breeder identifier is skipped and logged.
        """
        users = cls._breeders_block(payload).get("users")
        if not isinstance(users, list):
            return []
        profiles: list[RawBreederProfile] = []
        for user in users:
            if not isinstance(user, dict):
                continue
            profile = cls.parse_profile(user, is_from_club)
            if profile is None:
                logger.warning("Centrale Canine breeder without u_breeder_id skipped: %s", sorted(user)[:10])
                continue
            profiles.append(profile)
        return profiles

    @staticmethod
    def parse_profile(user: dict[str, Any], is_from_club: bool) -> RawBreederProfile | None:
        """
        Turn one directory entry into a profile, cleaned. The person's address and mail are never kept.

        Args:
            user: One ``users`` object of the JSON.
            is_from_club: Whether the entry comes from the club pages.

        Returns:
            The profile, or None when the entry has no ``u_breeder_id``.
        """
        source_id = SccValueParser.to_text(user.get("u_breeder_id"))
        if source_id is None:
            return None
        contact = read_scc_breeder_contact(user)
        varieties = user.get("u_variety")
        is_member = SccValueParser.to_bool(user.get("is_member"))
        return RawBreederProfile(
            source_id=source_id,
            scc_user_id=SccValueParser.to_text(user.get("u_id")),
            breeder_number=SccValueParser.to_text(user.get("u_breeder_number")),
            display_name=contact.display_name,
            affix=contact.affix,
            siren=contact.siren,
            phone_e164=contact.phone_e164,
            zip_code=contact.zip_code,
            city=contact.city,
            department_code=BreederContactParser.department_code(contact.zip_code),
            latitude=contact.latitude,
            longitude=contact.longitude,
            logo_url=scc_absolute_url(SccValueParser.to_text(user.get("u_user_picture_uri"))),
            site_slug=SccValueParser.to_text(user.get("u_breeder_site")),
            variety_ids=tuple(str(variety) for variety in varieties) if isinstance(varieties, list) else (),
            last_litter_at=SccValueParser.to_datetime(user.get("u_last_litter_date")),
            is_breed_club_member=True if is_from_club else is_member,
            is_selected=SccValueParser.to_bool(user.get("is_selected")),
        )
