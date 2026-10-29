"""
Whoof collector: the ads of a breed (docs/02-sources.md). Whoof is an Inertia app: each page carries its data as
JSON in the ``data-page`` attribute of its root, so the listing pages of a breed give every ad with its puppies
left, its parents (LOF numbers, ratings) and its breeder (SIREN, town). Politeness: one request per second and
the honest User-Agent; the robots.txt allows every page.
"""

import html
import json
import logging
import time
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

import httpx

from core.clock import french_date_of
from core.config import settings
from core.text import without_accents
from enums.coat_color import CoatColor
from enums.color_confidence import ColorConfidence
from enums.listing_kind import ListingKind
from enums.listing_source import ListingSource
from enums.lof_status import LofStatus
from services.collectors.breeder_contact_parser import BreederContactParser
from services.collectors.html_source import HtmlCollection, HtmlCollectionPlan, HtmlRawPage
from services.collectors.polite_http_client import PoliteHttpClient, SourceReadError
from services.collectors.raw_listing import ColorReading, RawBreeder, RawListing

logger = logging.getLogger(__name__)

WHOOF_BASE_URL = "https://whoof.fr"
DATA_PAGE_ATTRIBUTE = 'data-page="'
BORN_PUPPY_AD_TYPE = "born_puppy"
AVAILABLE_BOOKING_STATUS = "available"
WHITE = "blanc"
BLACK = "noir"
BROWN_WORDS: frozenset[str] = frozenset({"marron", "chocolat", "foie"})
GOLD_WORDS: frozenset[str] = frozenset({"roux", "dore", "orange", "fauve", "rouge", "gold", "golden"})


class WhoofCollector:
    """Reads the listing pages of a breed and keeps the ads of the departments of the profiles."""

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
            "Whoof", settings.honest_user_agent, http_client, seconds_between_requests, sleep, monotonic_clock
        )

    @staticmethod
    def listing_url(breed_slug: str, page_number: int) -> str:
        """
        Address of one page of the ads of a breed, all of France.

        Args:
            breed_slug: Breed slug on Whoof (``cocker-spaniel-anglais``).
            page_number: Page, from 1.

        Returns:
            The listing URL.
        """
        return f"{WHOOF_BASE_URL}/race/{breed_slug}/annonces?page={page_number}"

    def collect(self, plan: HtmlCollectionPlan) -> HtmlCollection:
        """
        Read every listing page of every breed of the plan. A page covers all of France, so every department of
        the plan is covered; the ads of the other departments are left out.

        Args:
            plan: Breeds and departments to read.

        Returns:
            The listings, the departments covered and the pages read.

        Raises:
            SourceReadError: When a page cannot be read, or no longer carries its data.
        """
        collection = HtmlCollection(collected_department_codes={department.code for department in plan.departments})
        for breed in plan.breeds:
            page_number = 1
            last_page_number = 1
            while page_number <= last_page_number:
                listing_url = self.listing_url(breed.source_slug, page_number)
                listing_html = self.polite_client.get(listing_url, accept="text/html").text
                collection.raw_pages.append(HtmlRawPage(listing_url, listing_html))
                ads, last_page_number = self.parse_listing_page(listing_html)
                for ad in ads:
                    listing = self.listing_of_ad(ad, breed.breed_id)
                    if listing is not None and listing.department_code in collection.collected_department_codes:
                        collection.listings.append(listing)
                page_number += 1
        return collection

    @staticmethod
    def parse_listing_page(page_html: str) -> tuple[list[dict[str, Any]], int]:
        """
        The ads of a listing page and the number of its last page, from the JSON of its ``data-page`` attribute.

        Args:
            page_html: The listing page.

        Returns:
            The ads in page order, and the last page number.

        Raises:
            SourceReadError: When the page no longer carries the data the collector reads.
        """
        start = page_html.find(DATA_PAGE_ATTRIBUTE)
        end = page_html.find('"', start + len(DATA_PAGE_ATTRIBUTE)) if start >= 0 else -1
        if end < 0:
            raise SourceReadError("Whoof : la page n'a plus de données data-page")
        try:
            page = json.loads(html.unescape(page_html[start + len(DATA_PAGE_ATTRIBUTE) : end]))
            ads = page["props"]["ads"]
            return list(ads["data"]), int(ads["meta"]["last_page"])
        except (ValueError, KeyError, TypeError) as error:
            raise SourceReadError(f"Whoof : données data-page illisibles ({error})") from error

    @classmethod
    def listing_of_ad(cls, ad: dict[str, Any], breed_id: int) -> RawListing | None:
        """
        Read one ad: the puppies of a born litter it offers, with their parents and their breeder.

        Args:
            ad: The ad, as the listing JSON gives it.
            breed_id: Breed the listing was read for.

        Returns:
            A puppy ad, or None for another kind of ad.
        """
        if ad.get("type") != BORN_PUPPY_AD_TYPE:
            logger.info("Whoof: ad %s of type %s left out", ad.get("id"), ad.get("type"))
            return None
        breeding: dict[str, Any] = ad.get("breeding") or {}
        father: dict[str, Any] = ad.get("father") or {}
        mother: dict[str, Any] = ad.get("mother") or {}
        documents: dict[str, Any] = ad.get("documents") or {}
        male_count = cls._count(ad.get("male_count"))
        female_count = cls._count(ad.get("female_count"))
        puppies_offered = (male_count or 0) + (female_count or 0)
        postal_code = BreederContactParser.postal_code(breeding.get("zip_code"))
        town = BreederContactParser.readable_name(breeding.get("city"))
        birth_moment = cls._utc_moment(ad.get("birthdate"))
        is_lof = (
            documents.get("birth_certificate") is True and bool(father.get("lof_id")) and bool(mother.get("lof_id"))
        )
        return RawListing(
            source=ListingSource.WHOOF,
            external_id=f"annonce-{ad['id']}",
            breed_id=breed_id,
            kind=ListingKind.PUPPY_AD,
            lof_status=LofStatus.LOF if is_lof else LofStatus.UNKNOWN,
            external_url=ad.get("public_url"),
            birth_date=french_date_of(birth_moment) if birth_moment else None,
            male_count=male_count,
            female_count=female_count,
            puppies_available=puppies_offered if ad.get("bookingStatus") == AVAILABLE_BOOKING_STATUS else 0,
            colors=cls._colors(ad.get("coat") or {}),
            color_text=cls._coat_text(ad.get("coat") or {}),
            price_cents=ad["price"] * 100 if isinstance(ad.get("price"), int) else None,
            department_code=BreederContactParser.department_code(postal_code),
            zip_code=postal_code,
            city=town,
            sire_name=BreederContactParser.readable_name(father.get("name")),
            sire_rating=cls._rating(father.get("notation")),
            dam_name=BreederContactParser.readable_name(mother.get("name")),
            dam_rating=cls._rating(mother.get("notation")),
            photos=(ad["main_photo"],) if isinstance(ad.get("main_photo"), str) else (),
            breeder=cls._breeder(breeding, postal_code, town),
            published_at=cls._utc_moment(ad.get("published_at")),
            raw_json={
                "booking_status": ad.get("bookingStatus"),
                "litter_id": (ad.get("litter") or {}).get("id"),
                "father_lof_id": father.get("lof_id"),
                "mother_lof_id": mother.get("lof_id"),
                "birth_certificate": documents.get("birth_certificate"),
            },
        )

    @staticmethod
    def _breeder(breeding: dict[str, Any], postal_code: str | None, town: str | None) -> RawBreeder | None:
        """
        The breeder of an ad, named by its Whoof slug.

        Args:
            breeding: The ``breeding`` of the ad.
            postal_code: Postal code of the breeding.
            town: Town of the breeding.

        Returns:
            The breeder, or None when the ad does not name it.
        """
        slug = breeding.get("slug")
        if not isinstance(slug, str) or not slug:
            return None
        return RawBreeder(
            source_id=slug,
            affix=BreederContactParser.readable_name(breeding.get("breeding_name")),
            siren=BreederContactParser.siren(breeding.get("siren")),
            zip_code=postal_code,
            city=town,
        )

    @staticmethod
    def _count(value: Any) -> int | None:
        """
        A count of puppies, as the JSON gives it.

        Args:
            value: The value read.

        Returns:
            The count, or None when absent.
        """
        return value if isinstance(value, int) and value >= 0 else None

    @staticmethod
    def _rating(value: Any) -> int | None:
        """
        The Centrale Canine rating of a parent, 1 to 6.

        Args:
            value: The ``notation`` read.

        Returns:
            The rating, or None when absent or out of the scale.
        """
        return value if isinstance(value, int) and 1 <= value <= 6 else None

    @staticmethod
    def _utc_moment(text: Any) -> datetime | None:
        """
        A moment of the JSON (``2026-05-31T22:00:00.000000Z``), as the database stores it.

        Args:
            text: ISO date and time in UTC.

        Returns:
            The naive UTC moment, or None when absent or unreadable.
        """
        if not isinstance(text, str):
            return None
        try:
            return datetime.fromisoformat(text).astimezone(UTC).replace(tzinfo=None)
        except ValueError:
            return None

    @staticmethod
    def _coat_words(coat: dict[str, Any]) -> list[str]:
        """
        The colour values of a coat, without accents nor shade number: ``marron-1`` gives ``marron``.

        Args:
            coat: The ``coat`` of the ad.

        Returns:
            The colour words, in the ad's order.
        """
        words: list[str] = []
        for color in coat.get("colors") or []:
            value = color.get("value") if isinstance(color, dict) else None
            if isinstance(value, str) and value:
                color_without_shade = value.split("-")[0]
                words.append(without_accents(color_without_shade.lower()))
        return words

    @classmethod
    def _coat_text(cls, coat: dict[str, Any]) -> str | None:
        """
        The coat as the breeder labels it, for the record.

        Args:
            coat: The ``coat`` of the ad.

        Returns:
            « Blanc, Noir », or None without colour.
        """
        labels = [color.get("label") for color in coat.get("colors") or [] if isinstance(color, dict)]
        text = ", ".join(label for label in labels if isinstance(label, str) and label)
        return text or None

    @classmethod
    def _colors(cls, coat: dict[str, Any]) -> tuple[ColorReading, ...]:
        """
        The canonical colour of a coat, only when its colours and marks name one without doubt.

        Args:
            coat: The ``coat`` of the ad: colour values and marks (``roaned``, ``black_fawn``…).

        Returns:
            The colour, certain, or nothing when the coat does not match a known one.
        """
        words = set(cls._coat_words(coat))
        marks: dict[str, Any] = coat.get("modifications") or {}
        has_tan = marks.get("black_fawn") is True or marks.get("fawn") is True
        others = words - {WHITE}
        color: CoatColor | None = None
        if marks.get("roaned") is True:
            if others == {BLACK}:
                color = CoatColor.BLEU_ROUAN
            elif others and others <= GOLD_WORDS:
                color = CoatColor.ORANGE_ROUAN
            elif others and others <= BROWN_WORDS:
                color = CoatColor.MARRON_ROUAN
        elif WHITE in words and len(others) >= 2:
            color = CoatColor.TRICOLORE
        elif WHITE in words and len(others) == 1:
            color = CoatColor.TRICOLORE if has_tan else CoatColor.PARTICOLORE
        elif others == {BLACK}:
            color = CoatColor.NOIR_ET_FEU if has_tan else CoatColor.NOIR
        elif others and others <= BROWN_WORDS:
            color = CoatColor.MARRON_ET_FEU if has_tan else CoatColor.MARRON
        elif others and others <= GOLD_WORDS:
            color = CoatColor.GOLD
        return (ColorReading(color, ColorConfidence.CERTAIN),) if color is not None else ()
