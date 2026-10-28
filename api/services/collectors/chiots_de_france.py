"""
Chiots de France collector: the France listing of a breed, filtered on the departments of the profiles,
then the page of each ad (docs/02-sources.md). An ad is a born litter with the puppies still available.
Its LOF status is the badge of its card: the ad page shows the same badges on every ad. Politeness: one
request per second, the honest User-Agent, and only the paths robots.txt allows.
"""

import json
import logging
import re
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime
from urllib.parse import urlparse

import httpx
from selectolax.lexbor import LexborHTMLParser

from core.config import settings
from enums.listing_kind import ListingKind
from enums.listing_source import ListingSource
from enums.lof_status import LofStatus
from services.collectors.breeder_contact_parser import BreederContactParser
from services.collectors.html_source import HtmlAdParser, HtmlCollection, HtmlCollectionPlan, HtmlRawPage
from services.collectors.polite_http_client import PoliteHttpClient
from services.collectors.raw_listing import RawListing

logger = logging.getLogger(__name__)

CHIOTS_DE_FRANCE_BASE_URL = "https://www.chiots-de-france.com"

FRENCH_MONTHS: dict[str, int] = {
    "janvier": 1,
    "février": 2,
    "mars": 3,
    "avril": 4,
    "mai": 5,
    "juin": 6,
    "juillet": 7,
    "août": 8,
    "septembre": 9,
    "octobre": 10,
    "novembre": 11,
    "décembre": 12,
}

CARD_DEPARTMENT_PATTERN = re.compile(r"departement\s+(\d{2,3}|2[AB])\b")
AD_ID_PATTERN = re.compile(r"_(\d+)_\d+\.html$")
FRENCH_LONG_DATE_PATTERN = re.compile(r"(\d{1,2})(?:er)?\s+([a-zéû]+)\s+(\d{4})")
AVAILABLE_PUPPIES_PATTERN = re.compile(r"(\d+)\s+(mâle|femelle)")
POSTAL_CODE_AND_TOWN_PATTERN = re.compile(r"(\d{5})\s+([^,]+)")
PHOTO_LIST_PATTERN = re.compile(r"const DB_PHOTOS\s*=\s*(\[.*?\]);", re.S)
LOOKALIKE_BREED_PREFIX = "Type "
BREEDER_HEADING_PREFIX = "Elevage "
LOF_BADGE = "LOF"


@dataclass(frozen=True)
class ListedLitterAd:
    """A litter ad found on the France listing, with its department and the LOF badge of its card."""

    external_id: str
    url: str
    department_code: str
    is_lof: bool


class ChiotsDeFranceCollector:
    """Reads the France listing of a breed, then each ad of the departments of the profiles."""

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
            http_client: HTTP client, injected by the tests; otherwise one that sends through ``curl``.
            seconds_between_requests: Minimum delay between two requests (politeness).
            sleep: Pause function, injected by the tests.
            monotonic_clock: Clock measuring the delay, injected by the tests.
        """
        self.polite_client = PoliteHttpClient(
            "Chiots de France",
            settings.honest_user_agent,
            http_client,
            seconds_between_requests,
            sleep,
            monotonic_clock,
        )

    @staticmethod
    def listing_url(breed_slug: str) -> str:
        """
        Address of the ads of a breed in all of France, on one page.

        Args:
            breed_slug: Breed slug on Chiots de France (``cocker-spaniel-anglais``).

        Returns:
            The listing URL.
        """
        return f"{CHIOTS_DE_FRANCE_BASE_URL}/chiots/{breed_slug}/france"

    def collect(self, plan: HtmlCollectionPlan) -> HtmlCollection:
        """
        Read the France listing of every breed of the plan, then each ad of its departments. The listing
        covers every department, so every department of the plan is covered.

        Args:
            plan: Breeds and departments to read.

        Returns:
            The listings, the departments covered and the pages read.

        Raises:
            SourceReadError: When a page cannot be read; an ad withdrawn in the meantime is skipped.
        """
        collection = HtmlCollection(collected_department_codes={department.code for department in plan.departments})
        for breed in plan.breeds:
            listing_url = self.listing_url(breed.source_slug)
            listing_html = self.polite_client.get(listing_url, accept="text/html").text
            collection.raw_pages.append(HtmlRawPage(listing_url, listing_html))
            for listed_ad in self.parse_listing_page(listing_html):
                if listed_ad.department_code not in collection.collected_department_codes:
                    continue
                response = self.polite_client.get(listed_ad.url, accept="text/html")
                if response.url.path != urlparse(listed_ad.url).path:
                    logger.info("Chiots de France: ad %s withdrawn, sent to %s", listed_ad.url, response.url)
                    continue
                collection.raw_pages.append(HtmlRawPage(listed_ad.url, response.text))
                collection.listings.append(self.parse_ad_page(response.text, breed.breed_id, listed_ad))
        return collection

    @staticmethod
    def parse_listing_page(html: str) -> list[ListedLitterAd]:
        """
        Find the ads of the France listing. A dog outside the LOF may not carry the breed's name, so the
        site lists it as « Type Cocker… », whether a cocker without papers or a crossbreed: such a card is
        left out (docs/08), like a card without department.

        Args:
            html: The listing page.

        Returns:
            The ads in page order.
        """
        tree = LexborHTMLParser(html)
        listed_ads: list[ListedLitterAd] = []
        for card in tree.css("div.list-box.result a.box"):
            if HtmlAdParser.text_of(card.css_first(".race")).startswith(LOOKALIKE_BREED_PREFIX):
                continue
            url = card.attributes.get("href") or ""
            id_match = AD_ID_PATTERN.search(url)
            place = card.css_first(".lieu .txt")
            department_match = CARD_DEPARTMENT_PATTERN.search(place.attributes.get("title") or "" if place else "")
            if id_match is None or department_match is None:
                continue
            listed_ads.append(
                ListedLitterAd(
                    external_id=f"annonce-{id_match.group(1)}",
                    url=url,
                    department_code=department_match.group(1),
                    is_lof=HtmlAdParser.text_of(card.css_first(".vign")) == LOF_BADGE,
                )
            )
        return listed_ads

    @classmethod
    def parse_ad_page(cls, html: str, breed_id: int, listed_ad: ListedLitterAd) -> RawListing:
        """
        Read the page of a litter ad.

        Args:
            html: The ad page.
            breed_id: Breed the listing was read for.
            listed_ad: The ad as its card showed it.

        Returns:
            The listing: a born litter, with the males and females still available.
        """
        tree = LexborHTMLParser(html)
        facts = cls._facts(tree)
        available_text = HtmlAdParser.text_of(tree.css_first(".nbr-male-femelle"))
        male_count, female_count = cls._available_puppies(available_text)
        price_text = HtmlAdParser.text_of(tree.css_first(".fiche-prix"))
        postal_code, town = cls._postal_code_and_town(facts.get("Lieu"))
        seller_heading = HtmlAdParser.text_of(tree.css_first("h2.sh1"))
        affix = (
            BreederContactParser.readable_name(seller_heading.removeprefix(BREEDER_HEADING_PREFIX))
            if seller_heading.startswith(BREEDER_HEADING_PREFIX)
            else None
        )
        published_on = cls._french_long_date(facts.get("Mise en ligne de l'annonce"))
        return RawListing(
            source=ListingSource.CHIOTS_DE_FRANCE,
            external_id=listed_ad.external_id,
            breed_id=breed_id,
            kind=ListingKind.LITTER_BORN,
            lof_status=LofStatus.LOF if listed_ad.is_lof else LofStatus.NON_LOF,
            external_url=listed_ad.url,
            birth_date=cls._french_long_date(facts.get("Date de naissance")),
            male_count=male_count,
            female_count=female_count,
            puppies_available=(male_count or 0) + (female_count or 0) if available_text else None,
            price_cents=HtmlAdParser.price_cents(price_text),
            department_code=listed_ad.department_code,
            zip_code=postal_code,
            city=town,
            sire_name=HtmlAdParser.text_of(tree.css_first(".fiche-parents a.fiche-pere .nom")) or None,
            dam_name=HtmlAdParser.text_of(tree.css_first(".fiche-parents a.fiche-mere .nom")) or None,
            photos=cls._photos(html),
            breeder=HtmlAdParser.breeder_of_site(
                tree.css_first("a.bouton-site-eleveur"), affix, facts.get("SIRET"), postal_code, town
            ),
            published_at=datetime(published_on.year, published_on.month, published_on.day) if published_on else None,
            raw_json={"facts": facts, "available": available_text, "price": price_text, "seller": seller_heading},
        )

    @staticmethod
    def _facts(tree: LexborHTMLParser) -> dict[str, str]:
        """
        The facts of an ad page: each item of its two lists, a ``.int`` label and a ``.cont`` value.

        Args:
            tree: The parsed page.

        Returns:
            Label → value; a label without value (« Portée de 6 chiots ») is kept with an empty value.
        """
        facts: dict[str, str] = {}
        for item in tree.css("ul.fiche-info-tab li, ul.fiche-info-supp li"):
            label = HtmlAdParser.text_of(item.css_first(".int"))
            if label:
                facts[label] = HtmlAdParser.text_of(item.css_first(".cont"))
        return facts

    @staticmethod
    def _available_puppies(text: str) -> tuple[int | None, int | None]:
        """
        The males and females still available, from « 4 mâles et 5 femelles disponibles »: a sex the
        sentence leaves out has none left.

        Args:
            text: The sentence, empty when the page has none.

        Returns:
            Males and females, both None without a sentence.
        """
        if not text:
            return None, None
        counts = {sex: int(count) for count, sex in AVAILABLE_PUPPIES_PATTERN.findall(text)}
        return counts.get("mâle", 0), counts.get("femelle", 0)

    @staticmethod
    def _postal_code_and_town(text: str | None) -> tuple[str | None, str | None]:
        """
        The postal code and the town of « 72500 Jupilles, Pays de la Loire ».

        Args:
            text: The « Lieu » value.

        Returns:
            The postal code and the town, readable, each None when absent.
        """
        match = POSTAL_CODE_AND_TOWN_PATTERN.search(text or "")
        if match is None:
            return None, None
        return match.group(1), BreederContactParser.readable_name(match.group(2))

    @staticmethod
    def _french_long_date(text: str | None) -> date | None:
        """
        Read a French date written in words, « 14 mai 2026 » or « 1er octobre 2026 ».

        Args:
            text: The text holding the date.

        Returns:
            The date, or None when absent or impossible.
        """
        match = FRENCH_LONG_DATE_PATTERN.search((text or "").lower())
        if match is None or match.group(2) not in FRENCH_MONTHS:
            return None
        try:
            return date(int(match.group(3)), FRENCH_MONTHS[match.group(2)], int(match.group(1)))
        except ValueError:
            return None

    @staticmethod
    def _photos(html: str) -> tuple[str, ...]:
        """
        The photos of the ad, from the ``DB_PHOTOS`` list its gallery script holds.

        Args:
            html: The ad page.

        Returns:
            Photo URLs, in gallery order, each once.
        """
        match = PHOTO_LIST_PATTERN.search(html)
        if match is None:
            return ()
        try:
            gallery = json.loads(match.group(1))
        except ValueError:
            return ()
        photos: dict[str, None] = {}
        for photo in gallery if isinstance(gallery, list) else []:
            if isinstance(photo, dict) and isinstance(photo.get("src"), str):
                photos[photo["src"]] = None
        return tuple(photos)
