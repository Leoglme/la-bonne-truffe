"""What the HTML collectors share: the plan a run reads, what it brings back, and how their ad pages are read."""

import re
from dataclasses import dataclass, field
from typing import Protocol
from urllib.parse import urlparse

from selectolax.lexbor import LexborNode

from services.collectors.breeder_contact_parser import BreederContactParser
from services.collectors.raw_listing import RawBreeder, RawListing

WHITESPACE_PATTERN = re.compile(r"\s+")
PRICE_PATTERN = re.compile(r"(\d[\d\s]*)\s*€")
BREEDER_SITE_HOST_SUFFIX = ".chiens-de-france.com"


@dataclass(frozen=True)
class HtmlBreedTarget:
    """A breed to read on an HTML source, with the slug the source uses in its addresses."""

    breed_id: int
    source_slug: str


@dataclass(frozen=True)
class HtmlDepartmentTarget:
    """A department of the profiles, with the region the sources group it under."""

    code: str
    region_name: str


@dataclass(frozen=True)
class HtmlCollectionPlan:
    """What one run reads on an HTML source: the breeds of the active profiles, in their departments."""

    breeds: tuple[HtmlBreedTarget, ...]
    departments: tuple[HtmlDepartmentTarget, ...]


@dataclass(frozen=True)
class HtmlRawPage:
    """One page exactly as received, kept for ``cli.py collect --save-raw``."""

    url: str
    html: str


@dataclass
class HtmlCollection:
    """Listings read by a run, the departments it covered, and the pages they come from."""

    listings: list[RawListing] = field(default_factory=list)
    collected_department_codes: set[str] = field(default_factory=set)
    raw_pages: list[HtmlRawPage] = field(default_factory=list)


class HtmlSourceCollector(Protocol):
    """What the collection runner needs from an HTML collector."""

    def collect(self, plan: HtmlCollectionPlan) -> HtmlCollection:
        """
        Read the source for a plan.

        Args:
            plan: Breeds and departments to read.

        Returns:
            The listings, the departments covered and the pages read.
        """
        ...


class HtmlAdParser:
    """Reads what the ad pages of Chiens de France and Chiots de France write the same way."""

    @staticmethod
    def text_of(node: LexborNode | None) -> str:
        """
        The text of a node, spaces collapsed.

        Args:
            node: The node, if found.

        Returns:
            Its text, or an empty string.
        """
        return WHITESPACE_PATTERN.sub(" ", node.text()).strip() if node is not None else ""

    @staticmethod
    def price_cents(price_text: str) -> int | None:
        """
        The price of an ad, from « A vendre 1 400 € ».

        Args:
            price_text: Text of the price box.

        Returns:
            The price in cents, or None when the ad gives no amount.
        """
        price_match = PRICE_PATTERN.search(price_text)
        return int(WHITESPACE_PATTERN.sub("", price_match.group(1))) * 100 if price_match else None

    @staticmethod
    def breeder_of_site(
        site_link: LexborNode | None,
        affix: str | None,
        siret_text: str | None,
        postal_code: str | None,
        town: str | None,
    ) -> RawBreeder | None:
        """
        The breeder of an ad. Both sources link it to its site hosted by Chiens de France, whose name
        identifies it (``elevage-a.chiens-de-france.com``); without a site, its affix or its SIREN does.

        Args:
            site_link: The link to the breeder's site, where the page shows the breeder.
            affix: The affix shown.
            siret_text: SIRET shown, if any.
            postal_code: Postal code of the ad.
            town: Town of the ad.

        Returns:
            The breeder, or None when nothing names it.
        """
        siren = BreederContactParser.siren(siret_text)
        host = urlparse(site_link.attributes.get("href") or "").netloc if site_link is not None else ""
        site_name = host.removesuffix(BREEDER_SITE_HOST_SUFFIX) if host.endswith(BREEDER_SITE_HOST_SUFFIX) else None
        source_id = site_name or BreederContactParser.affix_key(affix) or siren
        if source_id is None:
            return None
        return RawBreeder(source_id=source_id, affix=affix, siren=siren, zip_code=postal_code, city=town)
