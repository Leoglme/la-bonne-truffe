"""
Adds a link pasted on a breeder (docs/05, « Ajouter un lien »): its site on Chiens de France, read at once then every
morning; a Facebook, Instagram or YouTube account; or another site, whose page gives the social accounts at its bottom.
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from urllib.parse import urlparse

from fastapi import HTTPException, status
from selectolax.lexbor import LexborHTMLParser
from sqlalchemy.orm import Session

from core.config import settings
from enums.breeder_link_kind import BreederLinkKind
from enums.social_link_origin import SocialLinkOrigin
from models.breeder import Breeder
from services.breeder_query_service import BreederQueryService
from services.breeder_search_text import BreederSearchText
from services.breeder_social_links import BreederSocialLinks
from services.collectors.html_source import BREEDER_SITE_HOST_SUFFIX
from services.collectors.polite_http_client import PoliteHttpClient, SourceReadError
from services.collectors.social_link_parser import (
    FACEBOOK_ACCOUNT,
    INSTAGRAM_ACCOUNT,
    YOUTUBE_ACCOUNT,
    SocialLinkParser,
)

HTTPS_PREFIX = "https://"
UNREAD_HOSTS: frozenset[str] = frozenset({"www.chiens-de-france.com", "www.centrale-canine.fr"})
KINDS_BY_ACCOUNT: dict[str, BreederLinkKind] = {
    FACEBOOK_ACCOUNT: BreederLinkKind.FACEBOOK,
    INSTAGRAM_ACCOUNT: BreederLinkKind.INSTAGRAM,
    YOUTUBE_ACCOUNT: BreederLinkKind.YOUTUBE,
}
WEBSITE_LINK_LABEL = "Site"


@dataclass(frozen=True)
class BreederLinkReading:
    """What a pasted link is, the address kept for it, and the accounts the page of another site gives."""

    kind: BreederLinkKind
    address: str
    social_accounts: dict[str, str] = field(default_factory=dict)
    is_page_read: bool = False


class BreederLinkService:
    """Recognises a pasted link, then writes it on the breeder where it belongs."""

    def __init__(self, page_reader: Callable[[str], str] | None = None) -> None:
        """
        Prepare the service.

        Args:
            page_reader: Reads the HTML of a page, injected by the tests; otherwise the polite client with the
                honest User-Agent.
        """
        self.page_reader = page_reader or self._read_page

    def read(self, url: str) -> BreederLinkReading:
        """
        Recognise a link: a site on Chiens de France keeps only its root, a social account its address; for
        another site, its page is read for the accounts it links.

        Args:
            url: The link as pasted, with or without « https:// ».

        Returns:
            What the link is.

        Raises:
            HTTPException: 422 when the text is not the address of a page.
        """
        address = self._address_of(url)
        host = urlparse(address).netloc.lower()
        if host.endswith(BREEDER_SITE_HOST_SUFFIX) and host not in UNREAD_HOSTS:
            return BreederLinkReading(kind=BreederLinkKind.CHIENS_DE_FRANCE_SITE, address=f"{HTTPS_PREFIX}{host}")
        account = SocialLinkParser.account_of_address(address)
        if account is not None:
            return BreederLinkReading(kind=KINDS_BY_ACCOUNT[account], address=address)
        if host in UNREAD_HOSTS:
            return BreederLinkReading(kind=BreederLinkKind.WEBSITE, address=address)
        try:
            html = self.page_reader(address)
        except SourceReadError:
            return BreederLinkReading(kind=BreederLinkKind.WEBSITE, address=address)
        addresses = [(link.attributes.get("href") or "").strip() for link in LexborHTMLParser(html).css("a[href]")]
        return BreederLinkReading(
            kind=BreederLinkKind.WEBSITE,
            address=address,
            social_accounts=SocialLinkParser.accounts_in(addresses),
            is_page_read=True,
        )

    def add(self, db: Session, breeder_id: int, url: str) -> BreederLinkReading:
        """
        Write a pasted link on the breeder: a Chiens de France site becomes the one the morning run reads; a social
        account replaces the one known; another site becomes the website of the breeding (or one more link) and
        gives the accounts its page links, where none is known.

        Args:
            db: Database session; committed.
            breeder_id: The breeder.
            url: The link as pasted.

        Returns:
            What the link was.

        Raises:
            HTTPException: 404 for an unknown breeder, 422 for a text that is not an address.
        """
        breeder = BreederQueryService.get_breeder(db, breeder_id)
        reading = self.read(url)
        if reading.kind == BreederLinkKind.CHIENS_DE_FRANCE_SITE:
            breeder.chiens_de_france_site_url = reading.address
            breeder.website = breeder.website or reading.address
        elif reading.kind == BreederLinkKind.WEBSITE:
            self._keep_website(breeder, reading.address)
            for account, address in reading.social_accounts.items():
                BreederSocialLinks.keep(breeder, account, address, SocialLinkOrigin.BREEDER_SITE)
        else:
            BreederSocialLinks.keep(breeder, reading.kind.value, reading.address, SocialLinkOrigin.ADDED_BY_HAND)
        breeder.search_text = BreederSearchText.build(breeder)
        db.commit()
        return reading

    @staticmethod
    def _keep_website(breeder: Breeder, address: str) -> None:
        """
        Keep another site: the website of the breeding when it has none, else one more link.

        Args:
            breeder: The breeder.
            address: The address of the site.
        """
        if breeder.website is None:
            breeder.website = address
            return
        known_addresses = {breeder.website, *(str(link.get("url", "")) for link in breeder.links)}
        if address not in known_addresses:
            breeder.links = [*breeder.links, {"label": WEBSITE_LINK_LABEL, "url": address}]

    @staticmethod
    def _address_of(url: str) -> str:
        """
        The address of a pasted link, « https:// » added when missing.

        Args:
            url: The text pasted.

        Returns:
            The address.

        Raises:
            HTTPException: 422 when the text names no host.
        """
        text = url.strip()
        address = text if "://" in text else f"{HTTPS_PREFIX}{text}"
        parsed = urlparse(address)
        if parsed.scheme not in ("http", "https") or "." not in parsed.netloc or " " in text:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Adresse non reconnue")
        return address

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
        return PoliteHttpClient("Lien ajouté", settings.honest_user_agent).get(address, accept="text/html").text


breeder_link_service = BreederLinkService()
