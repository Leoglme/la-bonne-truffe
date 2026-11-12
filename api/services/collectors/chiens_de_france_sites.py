"""
Chiens de France breeder sites collector: the site each breeder gets on ``<slug>.chiens-de-france.com``
(docs/02-sources.md, « Site d'un éleveur sur Chiens de France »). For one breed of one site it reads the
litters to come, the litters for sale and each of their puppies, the litters born this year, the reproducers
shown, and what the site says of the breeding itself, its social accounts included. Before the sites, it reads
the regional lists of the breeders of the breed on the main site, which give the address of each site.
Politeness: one request per second and the honest User-Agent. A site that cannot be read is reported and the
run goes on with the next one.
"""

import logging
import re
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from datetime import date, datetime
from urllib.parse import urlparse

import httpx
from selectolax.lexbor import LexborHTMLParser, LexborNode

from core.config import settings
from core.text import without_accents
from enums.dog_role import DogRole
from enums.dog_sex import DogSex
from enums.listing_kind import ListingKind
from enums.listing_source import ListingSource
from enums.lof_status import LofStatus
from services.collectors.breeder_contact_parser import BreederContactParser
from services.collectors.chiens_de_france import (
    CHIENS_DE_FRANCE_BASE_URL,
    LITTER_PHOTO_PATH_PART,
    THUMBNAIL_PREFIX,
    affix_of,
    french_date_of,
    is_photo_file,
    litter_photos_of,
)
from services.collectors.html_source import (
    BREEDER_SITE_HOST_SUFFIX,
    WHITESPACE_PATTERN,
    HtmlAdParser,
    HtmlRawPage,
)
from services.collectors.polite_http_client import PoliteHttpClient, SourcePageMissingError, SourceReadError
from services.collectors.raw_dog import (
    RawBreederSiteFacts,
    RawBreederSiteLitter,
    RawDog,
    RawSiteDirectoryEntry,
)
from services.collectors.raw_listing import RawBreeder, RawListing
from services.collectors.social_link_parser import (
    FACEBOOK_ACCOUNT,
    INSTAGRAM_ACCOUNT,
    YOUTUBE_ACCOUNT,
    SocialLinkParser,
)
from services.dog_color_inference import DogColorInference

logger = logging.getLogger(__name__)

LITTERS_TO_COME_PATH = "saillies"
LITTERS_FOR_SALE_PATH = "chiots"
LITTER_FOR_SALE_PATH = "chiots-a-vendre"
LITTERS_BORN_PATH = "chiots-vendus"
DOG_LIST_PATHS: tuple[str, ...] = ("chiens/femelles", "chiens/males", "chiens/etalons")
MAIN_SITE_HOST = "www.chiens-de-france.com"
ZIP_CODE_PATTERN = re.compile(r"\b(\d{5})\b")

LITTER_TO_COME_LINK_PATTERN = re.compile(r"/saillie/(\d+)$")
LITTER_FOR_SALE_LINK_PATTERN = re.compile(r"/chiots-a-vendre/(\d+)$")
DOG_LINK_PATTERN = re.compile(r"/chien/(\d+)$")
PUPPY_NUMBER_PATTERN = re.compile(r"n°\s*(\d+)", re.IGNORECASE)
BREEDING_COUNTS_PATTERN = re.compile(r"(\d+)\s+femelles?\s+reproductrices?.*?(\d+)\s+portées?", re.DOTALL)
REGISTERED_ON_PATTERN = re.compile(r"Inscrit sur chiens-de-france\.com depuis le\s+(\d{1,2}[./]\d{1,2}[./]\d{4})")
RATING_PATTERN = re.compile(r"^\s*(\d+)")
BACKGROUND_IMAGE_PATTERN = re.compile(r"url\(\s*['\"]?([^'\")]+)")

SITE_AFFIX_SELECTORS: tuple[str, ...] = ("span.affixe-supp", "#pied a.affixe")
DOG_PHOTO_PATH_PART = "media_cdf/photos/chiens/"
SITE_PHOTO_PATH_PART = "media_cdf/photos/"
PARENT_ROLES: tuple[str, ...] = ("Père", "Mère")
SIRE_ROLE = "Père"
DAM_ROLE = "Mère"
LOF_YES = "oui"
TEXT_FRAGMENT_PREFIX = "#:~:text="


def breed_page_of(address: str | None, breed_slug: str) -> str | None:
    """
    The pages of a breed on a breeder site hosted by Chiens de France: the home of such a site sends to the first
    breed of the breeding, often another breed than the one looked for. Any other address is kept as it is.

    Args:
        address: A site address (« https://elevage-a.chiens-de-france.com »), None when unknown.
        breed_slug: The breed in the addresses of the sites (« cocker-spaniel-anglais »), empty when unknown.

    Returns:
        « https://elevage-a.chiens-de-france.com/cocker-spaniel-anglais » for the home of such a site, the address
        otherwise.
    """
    if address is None or not breed_slug:
        return address
    parsed_address = urlparse(address.strip())
    host = parsed_address.netloc.lower()
    if not host.endswith(BREEDER_SITE_HOST_SUFFIX) or host == MAIN_SITE_HOST or parsed_address.path.strip("/"):
        return address
    return f"{parsed_address.scheme or 'https'}://{host}/{breed_slug}"


def puppy_place_on_litter_page(litter_page_url: str, puppy_number: str) -> str:
    """
    The address that opens the page of a litter on a breeder site at one of its puppies. The site gives no puppy a
    page of its own, and the main site has none for a puppy the breeder only shows on its site (``/chiot/<n>`` sends
    to the regional list): a text fragment makes the browser scroll to the number of the puppy and mark it.

    Args:
        litter_page_url: The page of the litter (« …/cocker-spaniel-anglais/chiots-a-vendre/498070 »).
        puppy_number: The number of the puppy on Chiens de France (« 2211562 »).

    Returns:
        « …/cocker-spaniel-anglais/chiots-a-vendre/498070#:~:text=2211562 ».
    """
    return f"{litter_page_url}{TEXT_FRAGMENT_PREFIX}{puppy_number}"


@dataclass(frozen=True)
class SiteTarget:
    """
    One breeder site to read, for one breed.

    ``breeder_source_id`` is the subdomain slug (``elevage-a``), the identifier ``HtmlAdParser.breeder_of_site``
    gives the same breeder on the ad pages; ``fresh_dog_external_ids`` are the dogs whose page was read
    recently and is not read again.
    """

    breeder_id: int
    breeder_source_id: str
    site_url: str
    breed_id: int
    breed_slug: str
    fresh_dog_external_ids: frozenset[str] = frozenset()


@dataclass(frozen=True)
class SiteCollectionPlan:
    """The sites one run reads."""

    sites: tuple[SiteTarget, ...]


@dataclass(frozen=True)
class SiteDirectoryPlan:
    """The regional lists of breeders one run reads before the sites (``/eleveurs/<race>/france/<région>``)."""

    list_urls: tuple[str, ...]


@dataclass
class SiteDirectoryCollection:
    """What the regional lists bring back: one entry per breeder site, the pages, the lists not read."""

    entries: list[RawSiteDirectoryEntry] = field(default_factory=list)
    raw_pages: list[HtmlRawPage] = field(default_factory=list)
    failed_urls: list[str] = field(default_factory=list)


@dataclass
class SiteCollection:
    """What a run brings back: the listings and dogs read, the facts of each site, the pages, the sites not read."""

    listings: list[RawListing] = field(default_factory=list)
    dogs: list[RawDog] = field(default_factory=list)
    site_facts: list[RawBreederSiteFacts] = field(default_factory=list)
    raw_pages: list[HtmlRawPage] = field(default_factory=list)
    failed_sites: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ListedDog:
    """A dog as one of the dog lists of a site shows it (females, males, studs)."""

    external_id: str
    url: str
    name: str | None
    status_text: str | None
    photo_url: str | None


@dataclass(frozen=True)
class LinkedParent:
    """A parent as the « Les parents » box names and links it."""

    name: str
    external_id: str | None


class ChiensDeFranceSiteCollector:
    """Reads the pages of each breeder site of a plan, then each litter and each dog they link."""

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
            "Sites Chiens de France",
            settings.honest_user_agent,
            http_client,
            seconds_between_requests,
            sleep,
            monotonic_clock,
        )

    def collect(self, plan: SiteCollectionPlan) -> SiteCollection:
        """
        Read every site of the plan. A site that cannot be read is listed in ``failed_sites`` with the
        reason in the log, and the next one is read all the same.

        Args:
            plan: The sites to read.

        Returns:
            The listings, the dogs, the facts of each site read and the pages they come from.
        """
        collection = SiteCollection()
        for site in plan.sites:
            try:
                self._collect_site(site, collection)
            except SourceReadError as error:
                logger.warning("Sites Chiens de France: site not read %s: %s", site.site_url, error)
                collection.failed_sites.append(site.site_url)
        return collection

    def collect_directory(self, plan: SiteDirectoryPlan) -> SiteDirectoryCollection:
        """
        Read the regional lists of breeders of a plan. A list that cannot be read is listed in ``failed_urls``
        and the next one is read all the same.

        Args:
            plan: The lists to read.

        Returns:
            The breeder sites the lists give, and the pages they come from.
        """
        collection = SiteDirectoryCollection()
        for list_url in plan.list_urls:
            try:
                html = self.polite_client.get(list_url, accept="text/html").text
            except SourcePageMissingError as error:
                logger.info("Sites Chiens de France: regional list missing, skipped: %s", error)
                continue
            except SourceReadError as error:
                logger.warning("Sites Chiens de France: regional list not read %s: %s", list_url, error)
                collection.failed_urls.append(list_url)
                continue
            collection.raw_pages.append(HtmlRawPage(list_url, html))
            collection.entries.extend(self.parse_directory_page(LexborHTMLParser(html)))
        return collection

    def _collect_site(self, site: SiteTarget, collection: SiteCollection) -> None:
        """
        Read the pages of one site in the order docs/02 lists them, then each litter for sale and each dog
        they link. A page the site does not have is skipped; the facts of the site close the reading.

        Args:
            site: The site to read.
            collection: Filled with what the pages give.

        Raises:
            SourceReadError: When a page cannot be read for another reason than being gone.
        """
        breed_url = f"{site.site_url}/{site.breed_slug}"
        first_page_index = len(collection.raw_pages)
        photo_urls: list[str] = []
        breeding_counts: tuple[int | None, int | None] = (None, None)
        social_accounts: dict[str, str] = {}

        litters_to_come_tree = self._read_page(f"{breed_url}/{LITTERS_TO_COME_PATH}", collection)
        if litters_to_come_tree is not None:
            collection.listings.extend(self.parse_litters_to_come_page(litters_to_come_tree, site))
            social_accounts = self.parse_social_links(litters_to_come_tree)

        litters_for_sale_tree = self._read_page(f"{breed_url}/{LITTERS_FOR_SALE_PATH}", collection)
        if litters_for_sale_tree is not None:
            social_accounts = social_accounts or self.parse_social_links(litters_for_sale_tree)
            photo_urls.extend(litter_photos_of(litters_for_sale_tree))
            for litter_id in self.parse_litters_for_sale_page(litters_for_sale_tree):
                litter_url = f"{breed_url}/{LITTER_FOR_SALE_PATH}/{litter_id}"
                litter_tree = self._read_page(litter_url, collection)
                if litter_tree is None:
                    continue
                collection.listings.extend(self.parse_litter_for_sale_page(litter_tree, site, litter_url))
                photo_urls.extend(litter_photos_of(litter_tree))
                if breeding_counts == (None, None):
                    breeding_counts = self.breeding_counts(litter_tree)

        litters_born: tuple[RawBreederSiteLitter, ...] | None = None
        litters_born_tree = self._read_page(f"{breed_url}/{LITTERS_BORN_PATH}", collection)
        if litters_born_tree is not None:
            litters_born = tuple(self.parse_litters_born_page(litters_born_tree))
            social_accounts = social_accounts or self.parse_social_links(litters_born_tree)

        listed_dogs: dict[str, ListedDog] = {}
        for list_path in DOG_LIST_PATHS:
            dog_list_tree = self._read_page(f"{breed_url}/{list_path}", collection)
            if dog_list_tree is None:
                continue
            for listed_dog in self.parse_dog_list_page(dog_list_tree):
                known_dog = listed_dogs.get(listed_dog.external_id)
                if known_dog is None or (known_dog.status_text is None and listed_dog.status_text is not None):
                    listed_dogs[listed_dog.external_id] = listed_dog
        photo_urls.extend(listed_dog.photo_url for listed_dog in listed_dogs.values() if listed_dog.photo_url)
        for listed_dog in listed_dogs.values():
            if listed_dog.external_id in site.fresh_dog_external_ids:
                continue
            dog_tree = self._read_page(listed_dog.url, collection)
            if dog_tree is None:
                continue
            dog = self.parse_dog_page(dog_tree, site, listed_dog)
            collection.dogs.append(dog)
            photo_urls.extend(dog.photos)

        cover_photo_url = next(iter(photo_urls), None)
        if cover_photo_url is None:
            home_tree = self._read_page(breed_url, collection)
            cover_photo_url = self.home_cover_photo(home_tree) if home_tree is not None else None
        collection.site_facts.append(
            RawBreederSiteFacts(
                breeder_source_id=site.breeder_source_id,
                site_url=site.site_url,
                cover_photo_url=cover_photo_url,
                breeding_females_count=breeding_counts[0],
                litters_last_year_count=breeding_counts[1],
                registered_on=self._registered_on(collection.raw_pages[first_page_index:]),
                facebook_url=social_accounts.get(FACEBOOK_ACCOUNT),
                instagram_url=social_accounts.get(INSTAGRAM_ACCOUNT),
                youtube_url=social_accounts.get(YOUTUBE_ACCOUNT),
                litters_born=litters_born,
            )
        )

    def _read_page(self, url: str, collection: SiteCollection) -> LexborHTMLParser | None:
        """
        Read one page of a site and keep it with the pages of the run. A site without the breed sends its pages
        to another breed: such a page counts as missing.

        Args:
            url: Page address.
            collection: Where the page is kept.

        Returns:
            The parsed page, or None when the site has no such page.

        Raises:
            SourceReadError: On a network error or any status other than a missing page.
        """
        try:
            response = self.polite_client.get(url, accept="text/html")
        except SourcePageMissingError as error:
            logger.info("Sites Chiens de France: page missing, skipped: %s", error)
            return None
        if self._breed_slug_of(str(response.url)) != self._breed_slug_of(url):
            logger.info("Sites Chiens de France: page sent to another breed, skipped: %s", response.url)
            return None
        collection.raw_pages.append(HtmlRawPage(url, response.text))
        return LexborHTMLParser(response.text)

    @staticmethod
    def _breed_slug_of(url: str) -> str:
        """
        The breed a page of a site is about.

        Args:
            url: Page address (« https://elevage-a.chiens-de-france.com/cocker-spaniel-anglais/chiots »).

        Returns:
            The first segment of its path (« cocker-spaniel-anglais »).
        """
        return urlparse(url).path.strip("/").split("/", 1)[0]

    @classmethod
    def parse_litters_to_come_page(cls, tree: LexborHTMLParser, site: SiteTarget) -> list[RawListing]:
        """
        Read the « Portées à venir » list: one litter to come per mating, each named by its page on the main
        site (``/saillie/<id>``) so that both collectors describe the same listing, and linked to its page on the
        breeder's site, which the main site may not have.

        Args:
            tree: The parsed list.
            site: The site it belongs to.

        Returns:
            The litters to come, in page order, each once.
        """
        breeder = cls._breeder(site, cls._site_affix(tree))
        listings: dict[str, RawListing] = {}
        for link in tree.css("a.liste-portees[href]"):
            site_page_url = (link.attributes.get("href") or "").strip()
            link_match = LITTER_TO_COME_LINK_PATTERN.search(site_page_url)
            if link_match is None:
                continue
            litter_id = link_match.group(1)
            headline = HtmlAdParser.text_of(link.css_first("p.port"))
            parents = cls._listed_parents(link)
            listings.setdefault(
                litter_id,
                RawListing(
                    source=ListingSource.CHIENS_DE_FRANCE,
                    external_id=f"saillie-{litter_id}",
                    breed_id=site.breed_id,
                    kind=ListingKind.LITTER_EXPECTED,
                    lof_status=LofStatus.LOF,
                    external_url=f"{CHIENS_DE_FRANCE_BASE_URL}/saillie/{litter_id}",
                    breeder_site_page_url=site_page_url,
                    mating_date=french_date_of(headline),
                    sire_name=parents.get(SIRE_ROLE),
                    dam_name=parents.get(DAM_ROLE),
                    breeder=breeder,
                    raw_json={"headline": headline, "parents": parents, "site_url": site_page_url},
                ),
            )
        return list(listings.values())

    @staticmethod
    def parse_litters_for_sale_page(tree: LexborHTMLParser) -> list[str]:
        """
        The litters for sale a page links (``/chiots-a-vendre/<id>``); the site writes some of these links
        with a trailing space. A site with a single litter for sale sends « Chiots disponibles » straight to the
        page of that litter, which links to no litter: its canonical address gives the litter then.

        Args:
            tree: The parsed « Nos portées » list, or the page of the single litter for sale.

        Returns:
            The litter ids, in page order, each once.
        """
        litter_ids: dict[str, None] = {}
        for link in tree.css('link[rel="canonical"][href], a[href]'):
            link_match = LITTER_FOR_SALE_LINK_PATTERN.search((link.attributes.get("href") or "").strip())
            if link_match is not None:
                litter_ids[link_match.group(1)] = None
        return list(litter_ids)

    @classmethod
    def parse_litter_for_sale_page(cls, tree: LexborHTMLParser, site: SiteTarget, page_url: str) -> list[RawListing]:
        """
        Read the page of a litter for sale: one puppy ad per puppy box, each named by its page on the main site
        (``/chiot/<n>``), linked to its place on this page, with the facts of the litter table shared by all.

        Args:
            tree: The parsed litter page.
            site: The site it belongs to.
            page_url: Address of the page, kept in ``raw_json`` and pointed at each puppy.

        Returns:
            One listing per puppy, in page order.
        """
        facts = cls._table_facts(tree)
        breeder = cls._breeder(site, affix_of(facts.get("Affixe")) or cls._site_affix(tree))
        parents = cls._parents(tree)
        litter_code = facts.get("Code Portée")
        birth_date = french_date_of(facts.get("Date de naissance")) or french_date_of(
            HtmlAdParser.text_of(tree.css_first("article h3"))
        )
        is_lof = facts.get("Portée inscrite LOF", "").lower().startswith(LOF_YES)
        published_at = cls._published_at(facts.get("Annonce créer le"))
        page_photos = litter_photos_of(tree)
        listings: list[RawListing] = []
        for box in tree.css("div.box-chiot"):
            number_match = PUPPY_NUMBER_PATTERN.search(HtmlAdParser.text_of(box.css_first("p.infocdf")))
            if number_match is None:
                continue
            puppy_number = number_match.group(1)
            status_text = HtmlAdParser.text_of(box.css_first("div.status p"))
            male_count, female_count = cls._sex_counts(status_text)
            listings.append(
                RawListing(
                    source=ListingSource.CHIENS_DE_FRANCE,
                    external_id=f"chiot-{puppy_number}",
                    breed_id=site.breed_id,
                    kind=ListingKind.PUPPY_AD,
                    lof_status=LofStatus.LOF if is_lof else LofStatus.UNKNOWN,
                    external_url=f"{CHIENS_DE_FRANCE_BASE_URL}/chiot/{puppy_number}",
                    breeder_site_page_url=puppy_place_on_litter_page(page_url, puppy_number),
                    litter_number=WHITESPACE_PATTERN.sub("", litter_code) if litter_code else None,
                    birth_date=birth_date,
                    male_count=male_count,
                    female_count=female_count,
                    puppies_available=cls._puppies_available(status_text),
                    price_cents=HtmlAdParser.price_cents(status_text),
                    sire_name=parents[SIRE_ROLE].name if SIRE_ROLE in parents else None,
                    dam_name=parents[DAM_ROLE].name if DAM_ROLE in parents else None,
                    photos=cls._puppy_photos(box) or page_photos,
                    breeder=breeder,
                    published_at=published_at,
                    raw_json={
                        "name": HtmlAdParser.text_of(box.css_first("div.nom p.gras")),
                        "status": status_text,
                        "facts": facts,
                        "site_url": page_url,
                    },
                )
            )
        return listings

    @classmethod
    def breeding_counts(cls, tree: LexborHTMLParser) -> tuple[int | None, int | None]:
        """
        The « 18 femelles reproductrices au sein de l'élevage et 14 portées au cours de l'année écoulée »
        line of a litter page.

        Args:
            tree: The parsed litter page.

        Returns:
            The breeding females and the litters of the past year, both None when the line is absent.
        """
        counts_match = BREEDING_COUNTS_PATTERN.search(HtmlAdParser.text_of(tree.css_first("table.fiche-info")))
        if counts_match is None:
            return None, None
        return int(counts_match.group(1)), int(counts_match.group(2))

    @staticmethod
    def parse_social_links(tree: LexborHTMLParser) -> dict[str, str]:
        """
        The social accounts of the breeding, from the buttons of the site's menu (``a.nav-add-facebook``).

        Args:
            tree: Any parsed page of the site.

        Returns:
            Address by account (``facebook``, ``instagram``, ``youtube``), for those the menu shows.
        """
        addresses = [(link.attributes.get("href") or "").strip() for link in tree.css('a[class*="nav-add-"][href]')]
        return SocialLinkParser.accounts_in(addresses)

    @classmethod
    def parse_litters_born_page(cls, tree: LexborHTMLParser) -> list[RawBreederSiteLitter]:
        """
        Read the « Chiots nés chez nous » list of the year: one litter per entry, with its birth date, as its
        title writes it (« Portée née le 27/08/2026 »), and its parents.

        Args:
            tree: The parsed list.

        Returns:
            The litters, in page order; an entry without a date is left out.
        """
        litters: list[RawBreederSiteLitter] = []
        for link in tree.css("a.liste-portees[href]"):
            if LITTER_FOR_SALE_LINK_PATTERN.search((link.attributes.get("href") or "").strip()) is None:
                continue
            birth_date = french_date_of(link.attributes.get("title") or "") or french_date_of(
                HtmlAdParser.text_of(link.css_first("p.port"))
            )
            if birth_date is None:
                continue
            parents = cls._listed_parents(link)
            litters.append(
                RawBreederSiteLitter(
                    birth_date=birth_date, sire_name=parents.get(SIRE_ROLE), dam_name=parents.get(DAM_ROLE)
                )
            )
        return litters

    @staticmethod
    def parse_directory_page(tree: LexborHTMLParser) -> list[RawSiteDirectoryEntry]:
        """
        Read a regional list of the breeders of a breed: each box links the breeder's site and gives its name,
        then its postal code and its town (or its department).

        Args:
            tree: The parsed list.

        Returns:
            One entry per breeder site, in page order, each once.
        """
        entries: dict[str, RawSiteDirectoryEntry] = {}
        for box in tree.css("a.box-2-sm[href]"):
            host = urlparse((box.attributes.get("href") or "").strip()).netloc.lower()
            if not host.endswith(BREEDER_SITE_HOST_SUFFIX) or host == MAIN_SITE_HOST:
                continue
            name = HtmlAdParser.text_of(box.css_first("div.box-int-1")) or (box.attributes.get("title") or "").strip()
            if not name:
                continue
            place_node = box.css_first("div.box-int-3")
            zip_match = ZIP_CODE_PATTERN.search(HtmlAdParser.text_of(place_node))
            site_url = f"https://{host}"
            entries.setdefault(
                site_url,
                RawSiteDirectoryEntry(
                    site_url=site_url,
                    name=name,
                    zip_code=zip_match.group(1) if zip_match else None,
                    town=HtmlAdParser.text_of(place_node.css_first("span")) or None if place_node else None,
                ),
            )
        return list(entries.values())

    @staticmethod
    def parse_dog_list_page(tree: LexborHTMLParser) -> list[ListedDog]:
        """
        Read a dog list (females, males, studs): each box links the dog's page and may show a state
        (« Disponible pour saillie », « Chien à vendre ») over its photo.

        Args:
            tree: The parsed list.

        Returns:
            The dogs, in page order, each once.
        """
        listed_dogs: dict[str, ListedDog] = {}
        for box in tree.css("a.box-chiens[href]"):
            url = (box.attributes.get("href") or "").strip()
            link_match = DOG_LINK_PATTERN.search(url)
            if link_match is None:
                continue
            photo_node = box.css_first("div.in")
            photo_match = BACKGROUND_IMAGE_PATTERN.search(
                (photo_node.attributes.get("style") or "") if photo_node else ""
            )
            listed_dogs.setdefault(
                link_match.group(1),
                ListedDog(
                    external_id=link_match.group(1),
                    url=url,
                    name=HtmlAdParser.text_of(box.css_first("div.nom")) or None,
                    status_text=HtmlAdParser.text_of(box.css_first("div.box-chiens-etat")) or None,
                    photo_url=photo_match.group(1).strip()
                    if photo_match and is_photo_file(photo_match.group(1))
                    else None,
                ),
            )
        return list(listed_dogs.values())

    @classmethod
    def parse_dog_page(cls, tree: LexborHTMLParser, site: SiteTarget, listed_dog: ListedDog) -> RawDog:
        """
        Read the page of a reproducer: its title, its « née le » line, its table (Sexe, Couleur, Puce,
        Cotation, Statut), its parents and its photos.

        Args:
            tree: The parsed dog page.
            site: The site it belongs to.
            listed_dog: The dog as the list showed it.

        Returns:
            The dog.
        """
        facts = cls._table_facts(tree)
        full_name = BreederContactParser.readable_name(HtmlAdParser.text_of(tree.css_first("article h2"))) or (
            BreederContactParser.readable_name(listed_dog.name)
        )
        name, affix = cls._name_and_affix(full_name, cls._site_affix(tree))
        headline = HtmlAdParser.text_of(tree.css_first("article h3"))
        parents = cls._parents(tree)
        color_code = facts.get("Couleur") or None
        rating_match = RATING_PATTERN.match(facts.get("Cotation", ""))
        return RawDog(
            source=ListingSource.CHIENS_DE_FRANCE,
            external_id=listed_dog.external_id,
            role=DogRole.REPRODUCER,
            external_url=listed_dog.url,
            breeder_source_id=site.breeder_source_id,
            name=name,
            affix=affix,
            full_name=full_name,
            sex=cls._sex(facts.get("Sexe")),
            birth_date=french_date_of(headline),
            identifier=facts.get("Puce") or None,
            color_code=color_code,
            color=DogColorInference.canonical_color(color_code),
            rating=int(rating_match.group(1)) if rating_match else None,
            sire_external_id=parents[SIRE_ROLE].external_id if SIRE_ROLE in parents else None,
            dam_external_id=parents[DAM_ROLE].external_id if DAM_ROLE in parents else None,
            photos=cls._dog_photos(tree),
            availability_text=facts.get("Statut") or listed_dog.status_text,
        )

    @staticmethod
    def home_cover_photo(tree: LexborHTMLParser) -> str | None:
        """
        The first photo of the home page of a breed, loaded lazily (``data-original``) or not.

        Args:
            tree: The parsed home page.

        Returns:
            The photo URL, or None when the page shows none.
        """
        for image in tree.css("article.article-main img"):
            source = image.attributes.get("data-original") or image.attributes.get("src") or ""
            if SITE_PHOTO_PATH_PART in source and is_photo_file(source):
                return source
        return None

    @classmethod
    def _site_affix(cls, tree: LexborHTMLParser) -> str | None:
        """
        The affix the site shows in its banner and its footer.

        Args:
            tree: Any parsed page of the site.

        Returns:
            The affix, readable, or None when the site names none.
        """
        for selector in SITE_AFFIX_SELECTORS:
            affix = affix_of(HtmlAdParser.text_of(tree.css_first(selector)))
            if affix is not None:
                return affix
        return None

    @staticmethod
    def _breeder(site: SiteTarget, affix: str | None) -> RawBreeder:
        """
        The breeder the site belongs to, identified by its subdomain like on the ad pages.

        Args:
            site: The site.
            affix: Its affix, when shown.

        Returns:
            The breeder, with the site as its website.
        """
        return RawBreeder(source_id=site.breeder_source_id, affix=affix, website=site.site_url)

    @staticmethod
    def _listed_parents(node: LexborNode) -> dict[str, str]:
        """
        The parents of a litter in a list: each ``p.nom`` holds a « Père » or « Mère » label, then the name.

        Args:
            node: The litter entry.

        Returns:
            « Père » and « Mère » → name, for those shown.
        """
        parents: dict[str, str] = {}
        for name_line in node.css("p.nom"):
            spans = name_line.css("span")
            if len(spans) < 2:
                continue
            role = HtmlAdParser.text_of(spans[0])
            name = HtmlAdParser.text_of(spans[1])
            if role in PARENT_ROLES and name:
                parents.setdefault(role, name)
        return parents

    @staticmethod
    def _parents(tree: LexborHTMLParser) -> dict[str, LinkedParent]:
        """
        The parents of the « Les parents » box of a litter or dog page: each card links the parent's page
        on the main site (``/chien/<id>``, the same id as on the breeder's site) and names it.

        Args:
            tree: The parsed page.

        Returns:
            « Père » and « Mère » → the parent, for those shown.
        """
        parents: dict[str, LinkedParent] = {}
        for card in tree.css("a.fiche-parents"):
            role = HtmlAdParser.text_of(card.css_first("p.fp-int"))
            name = HtmlAdParser.text_of(card.css_first("p.fp-nom"))
            link_match = DOG_LINK_PATTERN.search((card.attributes.get("href") or "").strip())
            if role in PARENT_ROLES and name:
                parents.setdefault(role, LinkedParent(name, link_match.group(1) if link_match else None))
        return parents

    @staticmethod
    def _table_facts(tree: LexborHTMLParser) -> dict[str, str]:
        """
        The ``table.fiche-info`` of a litter or dog page: a ``td.int`` label (its « ? » tooltip dropped),
        then its ``td.cont`` value.

        Args:
            tree: The parsed page.

        Returns:
            Label → value.
        """
        facts: dict[str, str] = {}
        for row in tree.css("table.fiche-info tr"):
            label = HtmlAdParser.text_of(row.css_first("td.int")).removesuffix("?").strip()
            if label:
                facts[label] = HtmlAdParser.text_of(row.css_first("td.cont"))
        return facts

    @classmethod
    def _published_at(cls, text: str | None) -> datetime | None:
        """
        The publication day of « Annonce créer le 03/10/2026 », at midnight.

        Args:
            text: The table value.

        Returns:
            The publication time, or None.
        """
        published_on = french_date_of(text)
        if published_on is None:
            return None
        return datetime(published_on.year, published_on.month, published_on.day)

    @staticmethod
    def _sex_counts(status_text: str) -> tuple[int | None, int | None]:
        """
        One male or one female, from the « Mâle disponible… » / « Femelle réservée » line of a puppy.

        Args:
            status_text: The status line.

        Returns:
            Male and female counts, both None when the line names no sex.
        """
        lowered = without_accents(status_text).lower()
        if lowered.startswith("male"):
            return 1, 0
        if lowered.startswith("femelle"):
            return 0, 1
        return None, None

    @staticmethod
    def _sex(text: str | None) -> DogSex:
        """
        The sex of the « Sexe » row of a dog page.

        Args:
            text: The row value.

        Returns:
            The sex, unknown when the row says neither.
        """
        lowered = without_accents(text or "").lower()
        if lowered.startswith("femelle"):
            return DogSex.FEMALE
        if lowered.startswith("male"):
            return DogSex.MALE
        return DogSex.UNKNOWN

    @staticmethod
    def _puppies_available(status_text: str) -> int | None:
        """
        Whether a puppy is still offered, from its status line.

        Args:
            status_text: « Mâle disponible à la vente à 1400 € », « Femelle réservée », « Mâle vendu ».

        Returns:
            1 available, 0 reserved or sold, None when the line says neither.
        """
        lowered = without_accents(status_text).lower()
        if "disponible" in lowered:
            return 1
        if "reserv" in lowered or "vendu" in lowered:
            return 0
        return None

    @staticmethod
    def _name_and_affix(full_name: str | None, breeder_affix: str | None) -> tuple[str | None, str | None]:
        """
        Split a dog's full name from the breeder's affix when the name ends with it.

        Args:
            full_name: « Chien de test 1 Du Clos de l'Élevage A ».
            breeder_affix: « Du Clos de l'Élevage A ».

        Returns:
            The name and the affix; the full name and None when it does not carry the breeder's affix.
        """
        if full_name is None or breeder_affix is None or not full_name.lower().endswith(breeder_affix.lower()):
            return full_name, None
        return full_name[: len(full_name) - len(breeder_affix)].strip() or None, breeder_affix

    @staticmethod
    def _puppy_photos(box: LexborNode) -> tuple[str, ...]:
        """
        The full-size photos of one puppy box: those of its carousel, or the photo its thumbnail opens when the
        site shows a single thumbnail per puppy.

        Args:
            box: The ``div.box-chiot`` of the puppy.

        Returns:
            Photo URLs, in page order, each once; empty when the box ties no photo to the puppy.
        """
        photos: dict[str, None] = {}
        for node in box.css("div.boximg a[href], div.boximg img[src]"):
            source = node.attributes.get("href") or node.attributes.get("src") or ""
            if LITTER_PHOTO_PATH_PART in source and THUMBNAIL_PREFIX not in source and is_photo_file(source):
                photos[source] = None
        return tuple(photos)

    @staticmethod
    def _dog_photos(tree: LexborHTMLParser) -> tuple[str, ...]:
        """
        The photos of the dog itself (``media_cdf/photos/chiens/``), not those of its parents.

        Args:
            tree: The parsed dog page.

        Returns:
            Photo URLs, in page order, each once.
        """
        photos: dict[str, None] = {}
        for image in tree.css("img[src]"):
            source = image.attributes.get("src") or ""
            if DOG_PHOTO_PATH_PART in source and is_photo_file(source):
                photos[source] = None
        return tuple(photos)

    @classmethod
    def _registered_on(cls, pages: Sequence[HtmlRawPage]) -> date | None:
        """
        The « Inscrit sur chiens-de-france.com depuis le … » mention, wherever a page of the site shows it.

        Args:
            pages: The pages read on the site.

        Returns:
            The registration date, or None when no page shows it.
        """
        for page in pages:
            registered_match = REGISTERED_ON_PATTERN.search(page.html)
            if registered_match is not None:
                return french_date_of(registered_match.group(1))
        return None
