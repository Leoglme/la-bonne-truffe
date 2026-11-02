"""Reads once the own website of each breeding for the photo it puts forward (docs/05, « Sites des élevages »)."""

import logging
from collections.abc import Callable
from datetime import datetime
from urllib.parse import urlparse

from selectolax.lexbor import LexborHTMLParser
from sqlalchemy.orm import Session

from core.config import settings
from models.breeder import Breeder
from services.collectors.html_source import BREEDER_SITE_HOST_SUFFIX
from services.collectors.polite_http_client import PoliteHttpClient, SourcePageMissingError, SourceReadError
from services.collectors.site_image_parser import SiteImageParser

logger = logging.getLogger(__name__)

# Sites read by their own collector, or pages of an account rather than of a site: never read here.
NOT_OWN_WEBSITE_HOSTS: tuple[str, ...] = (
    BREEDER_SITE_HOST_SUFFIX.removeprefix("."),
    "centrale-canine.fr",
    "facebook.com",
    "instagram.com",
    "youtube.com",
    "youtu.be",
)
WEBSITES_READ_PER_RUN = 20


class BreederWebsiteService:
    """Reads the websites of the breedings that have one, once each, for their photo."""

    def __init__(self, page_reader: Callable[[str], str] | None = None) -> None:
        """
        Prepare the service.

        Args:
            page_reader: Reads the HTML of a page, injected by the tests; otherwise the polite client with the
                honest User-Agent.
        """
        self.page_reader = page_reader or self._read_page

    def read_unread_websites(self, db: Session, now: datetime) -> list[int]:
        """
        Read the websites not read yet, ``WEBSITES_READ_PER_RUN`` at most, and keep the photo each puts forward;
        a page without one keeps the photo known. A website that does not answer now is tried again at the next
        run; a page gone is not.

        Args:
            db: Database session; committed.
            now: Run time, naive UTC.

        Returns:
            The breeders that got a photo, by id.
        """
        breeders = (
            db.query(Breeder)
            .filter(Breeder.website.is_not(None), Breeder.website_read_at.is_(None))
            .order_by(Breeder.id)
            .all()
        )
        own_website_breeders = [breeder for breeder in breeders if self.is_own_website(breeder.website)]
        photographed_breeder_ids: list[int] = []
        for breeder in own_website_breeders[:WEBSITES_READ_PER_RUN]:
            address = breeder.website or ""
            try:
                html = self.page_reader(address)
            except SourcePageMissingError:
                breeder.website_read_at = now
                continue
            except SourceReadError as error:
                logger.info("Website of breeder %d not read: %s", breeder.id, error)
                continue
            breeder.website_read_at = now
            photo_url = SiteImageParser.main_photo(LexborHTMLParser(html), address)
            if photo_url is not None:
                breeder.website_photo_url = photo_url
                photographed_breeder_ids.append(breeder.id)
        db.commit()
        return photographed_breeder_ids

    @staticmethod
    def is_own_website(address: str | None) -> bool:
        """
        Whether an address is a website of the breeding to read here: not its Chiens de France or Centrale Canine
        site, which their collectors read, nor a Facebook, Instagram or YouTube account.

        Args:
            address: The website of a breeder.

        Returns:
            True for a website read for its photo.
        """
        host = urlparse(address or "").netloc.lower()
        return bool(host) and not any(host == suffix or host.endswith(f".{suffix}") for suffix in NOT_OWN_WEBSITE_HOSTS)

    @staticmethod
    def _read_page(address: str) -> str:
        """
        Read a page once, politely, with the honest User-Agent.

        Args:
            address: The page.

        Returns:
            Its HTML.

        Raises:
            SourceReadError: When the page cannot be read.
        """
        return PoliteHttpClient("Site d'élevage", settings.honest_user_agent).get(address, accept="text/html").text


breeder_website_service = BreederWebsiteService()
