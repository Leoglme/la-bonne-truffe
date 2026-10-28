"""
Chiens de France collector: the breed listing of each region, then the page of each puppy and of each
litter to come (docs/02-sources.md). The site only lists LOF puppies. Politeness: one request per second,
the honest User-Agent, and only the paths robots.txt allows (``/chiots/…``, ``/chiot/…``, ``/saillie/…``).
"""

import logging
import re
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime

import httpx
from selectolax.lexbor import LexborHTMLParser

from core.config import settings
from enums.listing_kind import ListingKind
from enums.listing_source import ListingSource
from enums.lof_status import LofStatus
from services.collectors.breeder_contact_parser import BreederContactParser
from services.collectors.html_source import (
    WHITESPACE_PATTERN,
    HtmlAdParser,
    HtmlCollection,
    HtmlCollectionPlan,
    HtmlRawPage,
)
from services.collectors.polite_http_client import PoliteHttpClient, SourcePageMissingError
from services.collectors.raw_listing import RawListing

logger = logging.getLogger(__name__)

CHIENS_DE_FRANCE_BASE_URL = "https://www.chiens-de-france.com"

REGION_SLUGS: dict[str, str] = {
    "Auvergne-Rhône-Alpes": "auvergne-rhone-alpes",
    "Bourgogne-Franche-Comté": "bourgogne-franche-comte",
    "Bretagne": "bretagne",
    "Centre-Val de Loire": "centre-val-de-loire",
    "Corse": "corse",
    "Grand Est": "grand-est",
    "Guadeloupe": "guadeloupe",
    "Guyane": "guyane",
    "Hauts-de-France": "hauts-de-france",
    "La Réunion": "reunion",
    "Martinique": "martinique",
    "Mayotte": "mayotte",
    "Normandie": "normandie",
    "Nouvelle-Aquitaine": "nouvelle-aquitaine",
    "Occitanie": "occitanie",
    "Pays de la Loire": "pays-de-la-loire",
    "Provence-Alpes-Côte d'Azur": "provence-alpes-cote-dazur",
    "Île-de-France": "ile-de-france",
}

DEPARTMENT_HEADING_PATTERN = re.compile(r"Département\s+(\d{2,3}|2[AB])\b")
PUPPY_PATH_PATTERN = re.compile(r"/chiot/(\d+)$")
LITTER_TO_COME_PATH_PATTERN = re.compile(r"/saillie/(\d+)$")
FRENCH_DATE_PATTERN = re.compile(r"(\d{1,2})[./](\d{1,2})[./](\d{4})")
POSTAL_CODE_AND_TOWN_PATTERN = re.compile(r"(\d{5})\s+(.+)")
BREEDER_SITE_PREFIX = "Elevage "
LITTER_PHOTO_PATH_PART = "/portees/"
THUMBNAIL_PREFIX = "TN200_"


@dataclass(frozen=True)
class ListedAd:
    """An ad found on a regional listing: a puppy for sale or a litter to come."""

    kind: ListingKind
    external_id: str
    url: str
    department_code: str


class ChiensDeFranceCollector:
    """Reads the regional listings of a breed, then each ad they show."""

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
            "Chiens de France",
            settings.honest_user_agent,
            http_client,
            seconds_between_requests,
            sleep,
            monotonic_clock,
        )

    @staticmethod
    def listing_url(breed_slug: str, region_slug: str) -> str:
        """
        Address of the puppies of a breed in a French region.

        Args:
            breed_slug: Breed slug on Chiens de France (``cocker-spaniel-anglais``).
            region_slug: Region slug (``bretagne``).

        Returns:
            The listing URL.
        """
        return f"{CHIENS_DE_FRANCE_BASE_URL}/chiots/{breed_slug}/france/{region_slug}"

    def collect(self, plan: HtmlCollectionPlan) -> HtmlCollection:
        """
        Read the listing of every region of the plan, then every ad of its departments.

        Args:
            plan: Breeds and departments to read.

        Returns:
            The listings, the departments covered and the pages read.

        Raises:
            SourceReadError: When a listing cannot be read; an ad withdrawn in the meantime is skipped.
        """
        collection = HtmlCollection()
        wanted_department_codes = {department.code for department in plan.departments}
        region_slugs = list(
            dict.fromkeys(
                REGION_SLUGS[department.region_name]
                for department in plan.departments
                if department.region_name in REGION_SLUGS
            )
        )
        collection.collected_department_codes = {
            department.code for department in plan.departments if department.region_name in REGION_SLUGS
        }
        for breed in plan.breeds:
            for region_slug in region_slugs:
                listing_url = self.listing_url(breed.source_slug, region_slug)
                listing_html = self._read(listing_url)
                collection.raw_pages.append(HtmlRawPage(listing_url, listing_html))
                for listed_ad in self.parse_listing_page(listing_html):
                    if listed_ad.department_code not in wanted_department_codes:
                        continue
                    try:
                        ad_html = self._read(listed_ad.url)
                    except SourcePageMissingError as error:
                        logger.info("Chiens de France: ad withdrawn while reading: %s", error)
                        continue
                    collection.raw_pages.append(HtmlRawPage(listed_ad.url, ad_html))
                    collection.listings.append(self.parse_ad_page(ad_html, breed.breed_id, listed_ad))
        return collection

    def _read(self, url: str) -> str:
        """
        Read one page.

        Args:
            url: Page address.

        Returns:
            Its HTML.
        """
        return self.polite_client.get(url, accept="text/html").text

    @staticmethod
    def parse_listing_page(html: str) -> list[ListedAd]:
        """
        Find the ads of a regional listing, each under its « Département NN » heading. The other
        sections of the page (other regions, other countries) are left out.

        Args:
            html: The listing page.

        Returns:
            The ads in page order, each once.
        """
        tree = LexborHTMLParser(html)
        listed_ads: dict[str, ListedAd] = {}
        current_department_code: str | None = None
        for node in tree.css("h2, a[href]"):
            if node.tag == "h2":
                heading_match = DEPARTMENT_HEADING_PATTERN.search(node.text())
                current_department_code = heading_match.group(1) if heading_match else None
                continue
            if current_department_code is None:
                continue
            url = node.attributes.get("href") or ""
            puppy_match = PUPPY_PATH_PATTERN.search(url)
            litter_to_come_match = LITTER_TO_COME_PATH_PATTERN.search(url)
            if puppy_match is not None:
                external_id = f"chiot-{puppy_match.group(1)}"
                listed_ads.setdefault(
                    external_id, ListedAd(ListingKind.PUPPY_AD, external_id, url, current_department_code)
                )
            elif litter_to_come_match is not None:
                external_id = f"saillie-{litter_to_come_match.group(1)}"
                listed_ads.setdefault(
                    external_id, ListedAd(ListingKind.LITTER_EXPECTED, external_id, url, current_department_code)
                )
        return list(listed_ads.values())

    @classmethod
    def parse_ad_page(cls, html: str, breed_id: int, listed_ad: ListedAd) -> RawListing:
        """
        Read an ad page, a puppy or a litter to come.

        Args:
            html: The ad page.
            breed_id: Breed the listing was read for.
            listed_ad: The ad as the listing showed it.

        Returns:
            The listing.
        """
        tree = LexborHTMLParser(html)
        if listed_ad.kind == ListingKind.PUPPY_AD:
            return cls.parse_puppy_page(tree, breed_id, listed_ad)
        return cls.parse_litter_to_come_page(tree, breed_id, listed_ad)

    @classmethod
    def parse_puppy_page(cls, tree: LexborHTMLParser, breed_id: int, listed_ad: ListedAd) -> RawListing:
        """
        Read the page of one puppy for sale. The colour is not on the page: it stays unknown.

        Args:
            tree: The parsed page.
            breed_id: Breed the listing was read for.
            listed_ad: The ad as the listing showed it.

        Returns:
            The listing, one puppy of its sex.
        """
        headline_facts = cls._headline_facts(tree)
        summary_facts = cls._summary_facts(tree)
        detail_facts = cls._detail_facts(tree)
        sex = headline_facts.get("Sexe", "")
        is_male = sex.startswith("Mâle")
        is_female = sex.startswith("Femelle")
        has_known_sex = is_male or is_female
        price_text = HtmlAdParser.text_of(tree.css_first("div.fiche-prix div.prix"))
        town, postal_code = cls._town_and_postal_code(tree)
        parents = cls._parents(tree)
        affix = cls._affix(summary_facts.get("Eleveur"))
        litter_code = detail_facts.get("Code portée")
        return RawListing(
            source=ListingSource.CHIENS_DE_FRANCE,
            external_id=listed_ad.external_id,
            breed_id=breed_id,
            kind=ListingKind.PUPPY_AD,
            lof_status=LofStatus.LOF,
            external_url=listed_ad.url,
            litter_number=WHITESPACE_PATTERN.sub("", litter_code) if litter_code else None,
            birth_date=cls._french_date(cls._birth_date_text(tree)),
            male_count=int(is_male) if has_known_sex else None,
            female_count=int(is_female) if has_known_sex else None,
            puppies_available=cls._puppies_available(price_text),
            price_cents=HtmlAdParser.price_cents(price_text),
            department_code=listed_ad.department_code,
            zip_code=postal_code,
            city=town,
            sire_name=parents.get("Père"),
            dam_name=parents.get("Mère"),
            photos=cls._litter_photos(tree),
            breeder=HtmlAdParser.breeder_of_site(
                tree.css_first("div.fiche-recap a[href]"), affix, detail_facts.get("Siret"), postal_code, town
            ),
            published_at=cls._published_at(detail_facts.get("Informations complémentaires")),
            raw_json={"headline": headline_facts, "details": detail_facts, "price": price_text},
        )

    @classmethod
    def parse_litter_to_come_page(cls, tree: LexborHTMLParser, breed_id: int, listed_ad: ListedAd) -> RawListing:
        """
        Read the page of a litter to come, announced from its mating.

        Args:
            tree: The parsed page.
            breed_id: Breed the listing was read for.
            listed_ad: The ad as the listing showed it.

        Returns:
            The listing, with its mating date and sexes still unknown.
        """
        facts = cls._list_facts(tree)
        town_node = tree.css_first("p.lieu-ville")
        town_match = POSTAL_CODE_AND_TOWN_PATTERN.match(HtmlAdParser.text_of(town_node))
        postal_code = town_match.group(1) if town_match else None
        town = BreederContactParser.readable_name(town_match.group(2)) if town_match else None
        parents = cls._litter_to_come_parents(tree)
        breeder_site_link = tree.css_first("a.fichesite")
        breeder_site_text = HtmlAdParser.text_of(breeder_site_link)
        affix = cls._affix(breeder_site_text.removeprefix(BREEDER_SITE_PREFIX) if breeder_site_text else None)
        return RawListing(
            source=ListingSource.CHIENS_DE_FRANCE,
            external_id=listed_ad.external_id,
            breed_id=breed_id,
            kind=ListingKind.LITTER_EXPECTED,
            lof_status=LofStatus.LOF,
            external_url=listed_ad.url,
            mating_date=cls._french_date(facts.get("Date de saillie")),
            department_code=listed_ad.department_code,
            zip_code=postal_code,
            city=town,
            sire_name=parents.get("Père"),
            dam_name=parents.get("Mère"),
            breeder=HtmlAdParser.breeder_of_site(breeder_site_link, affix, facts.get("Pro / Siret"), postal_code, town),
            raw_json={"facts": facts},
        )

    @staticmethod
    def _headline_facts(tree: LexborHTMLParser) -> dict[str, str]:
        """
        The facts at the top of a puppy page (« Sexe », « Disponibilité »…), the label without its note.

        Args:
            tree: The parsed page.

        Returns:
            Label → value.
        """
        facts: dict[str, str] = {}
        for block in tree.css("div.fiche-info-rgp"):
            title = block.css_first("div.fiche-info-titre")
            if title is None:
                continue
            label = HtmlAdParser.text_of(title).split("(")[0].strip()
            facts[label] = HtmlAdParser.text_of(block.css_first("div.int"))
        return facts

    @staticmethod
    def _summary_facts(tree: LexborHTMLParser) -> dict[str, str]:
        """
        The « Lieu » and « Eleveur » box of a puppy page.

        Args:
            tree: The parsed page.

        Returns:
            Label → value.
        """
        facts: dict[str, str] = {}
        label: str | None = None
        for node in tree.css("div.fiche-recap div.left, div.fiche-recap div.right"):
            if "left" in (node.attributes.get("class") or "").split():
                label = HtmlAdParser.text_of(node)
            elif label is not None:
                facts[label] = HtmlAdParser.text_of(node)
                label = None
        return facts

    @staticmethod
    def _detail_facts(tree: LexborHTMLParser) -> dict[str, str]:
        """
        The « Informations supplémentaires » and « Portée » boxes of a puppy page: each label sits in a
        ``div.int`` followed by its value.

        Args:
            tree: The parsed page.

        Returns:
            Label → value.
        """
        facts: dict[str, str] = {}
        for label_node in tree.css("div.fiche-box div.int"):
            value_node = label_node.next
            while value_node is not None and value_node.tag != "div":
                value_node = value_node.next
            if value_node is not None:
                facts[HtmlAdParser.text_of(label_node)] = HtmlAdParser.text_of(value_node)
        return facts

    @staticmethod
    def _list_facts(tree: LexborHTMLParser) -> dict[str, str]:
        """
        The facts of a litter-to-come page, one ``<li>`` each: a ``div`` label, then its value.

        Args:
            tree: The parsed page.

        Returns:
            Label → value.
        """
        facts: dict[str, str] = {}
        for item in tree.css("li"):
            label_node = item.css_first("div")
            value_node = item.css_first("p")
            if label_node is not None and value_node is not None:
                facts[HtmlAdParser.text_of(label_node)] = HtmlAdParser.text_of(value_node)
        return facts

    @staticmethod
    def _birth_date_text(tree: LexborHTMLParser) -> str | None:
        """
        The « (Né le 28.08.2026) » note of the age of a puppy.

        Args:
            tree: The parsed page.

        Returns:
            The note, or None when the page has none.
        """
        for title in tree.css("div.fiche-info-titre span"):
            text = HtmlAdParser.text_of(title)
            if "le " in text:
                return text
        return None

    @staticmethod
    def _french_date(text: str | None) -> date | None:
        """
        Read a French date written ``28.08.2026`` or ``29/08/2026``.

        Args:
            text: The text holding the date.

        Returns:
            The date, or None when absent or impossible.
        """
        match = FRENCH_DATE_PATTERN.search(text or "")
        if match is None:
            return None
        day, month, year = (int(part) for part in match.groups())
        try:
            return date(year, month, day)
        except ValueError:
            return None

    @classmethod
    def _published_at(cls, text: str | None) -> datetime | None:
        """
        The publication day of « Annonce créée le 03.10.2026 », at midnight UTC.

        Args:
            text: The « Informations complémentaires » value.

        Returns:
            The publication time, or None.
        """
        published_on = cls._french_date(text.split("Inscrit")[0] if text else None)
        if published_on is None:
            return None
        return datetime(published_on.year, published_on.month, published_on.day)

    @staticmethod
    def _puppies_available(price_text: str) -> int | None:
        """
        Whether the puppy is still offered, from the price box.

        Args:
            price_text: Text of the price box (« A vendre 1400 € »).

        Returns:
            1 for sale, 0 reserved or sold, None when the box says neither.
        """
        lowered = price_text.lower()
        if "vendre" in lowered:
            return 1
        if "réserv" in lowered or "vendu" in lowered:
            return 0
        return None

    @staticmethod
    def _town_and_postal_code(tree: LexborHTMLParser) -> tuple[str | None, str | None]:
        """
        The town and postal code of the « Lieu » box: the town, then « 35133 - France » below it.

        Args:
            tree: The parsed page.

        Returns:
            The town and the postal code, each None when absent.
        """
        for label in tree.css("div.fiche-recap div.left"):
            if HtmlAdParser.text_of(label) != "Lieu":
                continue
            value = label.next
            while value is not None and value.tag != "div":
                value = value.next
            if value is None:
                return None, None
            postal_line = HtmlAdParser.text_of(next((child for child in value.iter() if child.tag == "div"), None))
            town_text = HtmlAdParser.text_of(value).removesuffix(postal_line).strip()
            postal_match = re.search(r"\d{5}", postal_line)
            return BreederContactParser.readable_name(town_text), postal_match.group(0) if postal_match else None
        return None, None

    @staticmethod
    def _parents(tree: LexborHTMLParser) -> dict[str, str]:
        """
        The father and mother of a puppy, from the « Les parents » box.

        Args:
            tree: The parsed page.

        Returns:
            « Père » and « Mère » → name, for those shown.
        """
        parents: dict[str, str] = {}
        for card in tree.css("div.pedifich"):
            role = HtmlAdParser.text_of(card.css_first("div.type"))
            name_box = card.css_first("div.nom")
            name_node = next((child for child in name_box.iter() if child.tag == "div"), None) if name_box else None
            name = HtmlAdParser.text_of(name_node)
            if role in ("Père", "Mère") and name:
                parents[role] = name
        return parents

    @staticmethod
    def _litter_to_come_parents(tree: LexborHTMLParser) -> dict[str, str]:
        """
        The father and mother of a litter to come: a « Père » or « Mère » label, then a ``div.nom``.

        Args:
            tree: The parsed page.

        Returns:
            « Père » and « Mère » → name, for those shown.
        """
        parents: dict[str, str] = {}
        for name_node in tree.css("div.nom"):
            label_node = name_node.prev
            while label_node is not None and label_node.tag != "div":
                label_node = label_node.prev
            role = HtmlAdParser.text_of(label_node)
            if role in ("Père", "Mère") and role not in parents:
                parents[role] = HtmlAdParser.text_of(name_node)
        return parents

    @staticmethod
    def _affix(text: str | None) -> str | None:
        """
        The affix as the page writes it, or None for a breeder « Sans affixe ».

        Args:
            text: The breeder name shown.

        Returns:
            The affix, readable, or None.
        """
        if not text or text.lower().startswith("sans affixe"):
            return None
        return BreederContactParser.readable_name(text)

    @staticmethod
    def _litter_photos(tree: LexborHTMLParser) -> tuple[str, ...]:
        """
        The full-size photos of the litter, without their thumbnails.

        Args:
            tree: The parsed page.

        Returns:
            Photo URLs, in page order, each once.
        """
        photos: dict[str, None] = {}
        for image in tree.css("img[src]"):
            source = image.attributes.get("src") or ""
            if LITTER_PHOTO_PATH_PART in source and THUMBNAIL_PREFIX not in source:
                photos[source] = None
        return tuple(photos)
