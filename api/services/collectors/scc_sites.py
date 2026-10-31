"""
Centrale Canine site collector: the mini-site of a breeding (``/<slug>``, docs/02 « Mini-site SCC d'un élevage »),
read for its photos: the cover of its home page, and the gallery images its « dogs » document carries.

Same access rules as the litters: a browser User-Agent, one request per second, relayed by the desktop app
when the server is refused.
"""

import logging
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import httpx

from services.collectors.centrale_canine import (
    SCC_BASE_URL,
    SCC_BROWSER_USER_AGENT,
    CentraleCanineError,
    SccJsonPage,
    fetch_json_page,
    scc_absolute_url,
)
from services.collectors.polite_http_client import PoliteHttpClient, SourcePageMissingError
from services.collectors.scc_value_parser import SccValueParser

logger = logging.getLogger(__name__)

GALLERY_IMAGE_BUNDLE = "gallery_image"
MAX_SITE_PHOTOS = 24


@dataclass(frozen=True)
class SccSiteTarget:
    """A breeding whose site is read: the breeder, and the slug of its site (``u_breeder_site``)."""

    breeder_id: int
    site_slug: str


@dataclass(frozen=True)
class SccSiteCollectionPlan:
    """What one run reads: the sites in priority order."""

    sites: tuple[SccSiteTarget, ...]


@dataclass(frozen=True)
class RawSccSite:
    """What the site of a breeding shows: its cover photo and its gallery; ``is_missing`` when the site is gone."""

    breeder_id: int
    site_slug: str
    cover_photo_url: str | None = None
    photo_urls: tuple[str, ...] = ()
    is_missing: bool = False


@dataclass
class SccSiteCollection:
    """Sites read by a run, the raw pages they come from, and how many pages were read."""

    sites: list[RawSccSite] = field(default_factory=list)
    raw_pages: list[SccJsonPage] = field(default_factory=list)
    pages_read: int = 0


class SccSiteCollector:
    """Reads the home page and the « dogs » document of each site, politely."""

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
    def homepage_url(site_slug: str) -> str:
        """
        URL of the JSON of the home page of a site.

        Args:
            site_slug: Slug of the site (``u_breeder_site`` of the directory).

        Returns:
            The URL, query string excluded.
        """
        return f"{SCC_BASE_URL}/{site_slug}/api/homepage"

    @staticmethod
    def dogs_url(site_slug: str) -> str:
        """
        URL of the JSON of the « dogs » document of a site, which carries the gallery images.

        Args:
            site_slug: Slug of the site.

        Returns:
            The URL, query string excluded.
        """
        return f"{SCC_BASE_URL}/{site_slug}/api/dogs"

    def collect(self, plan: SccSiteCollectionPlan) -> SccSiteCollection:
        """
        Read the home page then the « dogs » document of every site of the plan.

        Args:
            plan: The sites to read.

        Returns:
            The sites read; a site gone from the Centrale Canine is reported missing, a page not relayed yet
            leaves its site out.

        Raises:
            CentraleCanineError: When a page cannot be read; the run fails as a whole.
        """
        collection = SccSiteCollection()
        for target in plan.sites:
            homepage = self._fetch(collection, self.homepage_url(target.site_slug))
            if homepage is None:
                collection.sites.append(RawSccSite(target.breeder_id, target.site_slug, is_missing=True))
                continue
            if not isinstance(homepage.get("main_content"), dict):
                continue
            dogs_document = self._fetch(collection, self.dogs_url(target.site_slug))
            collection.sites.append(
                RawSccSite(
                    breeder_id=target.breeder_id,
                    site_slug=target.site_slug,
                    cover_photo_url=self.parse_cover(homepage),
                    photo_urls=self.parse_gallery(dogs_document) if dogs_document is not None else (),
                )
            )
        return collection

    @staticmethod
    def parse_cover(payload: dict[str, Any]) -> str | None:
        """
        The cover photo of a home page.

        Args:
            payload: The ``api/homepage`` JSON.

        Returns:
            The absolute URL of ``main_content.h_image_uri``, or None when the page has none or is not a home page.
        """
        main_content = payload.get("main_content")
        if not isinstance(main_content, dict):
            return None
        return scc_absolute_url(SccValueParser.to_text(main_content.get("h_image_uri")))

    @staticmethod
    def parse_gallery(payload: dict[str, Any]) -> tuple[str, ...]:
        """
        The gallery images a site document carries, each once, the first ``MAX_SITE_PHOTOS`` kept.

        Args:
            payload: The ``api/dogs`` JSON, whose ``media`` block lists the images of the site.

        Returns:
            The absolute URLs, in page order.
        """
        media = payload.get("media")
        if not isinstance(media, dict):
            return ()
        photos: dict[str, None] = {}
        for item in media.values():
            if not isinstance(item, dict) or item.get("m_bundle") != GALLERY_IMAGE_BUNDLE:
                continue
            url = scc_absolute_url(SccValueParser.to_text(item.get("m_image_uri")))
            if url is not None:
                photos[url] = None
        return tuple(photos)[:MAX_SITE_PHOTOS]

    def _fetch(self, collection: SccSiteCollection, url: str) -> dict[str, Any] | None:
        """
        Read one JSON page and count it.

        Args:
            collection: The collection, whose pages are counted and kept.
            url: Address to read.

        Returns:
            The decoded JSON object, or None when the site is gone (404).

        Raises:
            CentraleCanineError: When the page cannot be read for another reason.
        """
        try:
            payload = fetch_json_page(self.polite_client, url, {"_format": "json"})
        except CentraleCanineError as error:
            if isinstance(error.__cause__, SourcePageMissingError):
                collection.pages_read += 1
                return None
            raise
        collection.pages_read += 1
        collection.raw_pages.append(SccJsonPage(url, payload))
        return payload
