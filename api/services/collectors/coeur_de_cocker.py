"""
Cœur de Cocker collector (docs/02-sources.md): a site devoted to the cocker, whose adoption page reads every ad
from one public JSON. One request per run, with the honest User-Agent; the robots.txt allows ``/wp-json/``.
Each ad offers one dog: a puppy of a born litter, or an adult the collector leaves out.
"""

import json
import logging
import re
import time
from collections.abc import Callable
from datetime import UTC, date, datetime
from typing import Any

import httpx

from core.clock import FRENCH_TIMEZONE
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

COEUR_DE_COCKER_BASE_URL = "https://coeurdecocker.fr"
ADS_URL = f"{COEUR_DE_COCKER_BASE_URL}/wp-json/cdc/v1/adoption/annonces"
PUPPY_TYPE = "Chiot"
AVAILABLE_STATUS = "disponible"
MALE = "male"
FEMALE = "femelle"
LEADING_AMOUNT_PATTERN = re.compile(r"\d[\d\s.]*")
THOUSANDS_SEPARATOR_PATTERN = re.compile(r"[\s.]")

LOF_STATUSES_BY_ANSWER: dict[str, LofStatus] = {"oui": LofStatus.LOF, "non": LofStatus.NON_LOF}

COLORS_BY_LABEL: dict[str, CoatColor] = {
    "noir": CoatColor.NOIR,
    "noir et feu": CoatColor.NOIR_ET_FEU,
    "marron": CoatColor.MARRON,
    "chocolat": CoatColor.MARRON,
    "marron et feu": CoatColor.MARRON_ET_FEU,
    "chocolat et feu": CoatColor.MARRON_ET_FEU,
    "dore": CoatColor.GOLD,
    "roux": CoatColor.GOLD,
    "fauve": CoatColor.GOLD,
    "gold": CoatColor.GOLD,
    "golden": CoatColor.GOLD,
    "rouge": CoatColor.GOLD,
    "bleu rouan": CoatColor.BLEU_ROUAN,
    "orange rouan": CoatColor.ORANGE_ROUAN,
    "marron rouan": CoatColor.MARRON_ROUAN,
    "chocolat rouan": CoatColor.MARRON_ROUAN,
    "tricolore": CoatColor.TRICOLORE,
    "bicolore": CoatColor.PARTICOLORE,
    "particolore": CoatColor.PARTICOLORE,
}


class CoeurDeCockerCollector:
    """Reads the JSON of the ads and keeps the puppies of the breeds and departments of the profiles."""

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
            "Cœur de Cocker", settings.honest_user_agent, http_client, seconds_between_requests, sleep, monotonic_clock
        )

    def collect(self, plan: HtmlCollectionPlan) -> HtmlCollection:
        """
        Read the ads once, then keep the puppies of the breeds and departments of the plan. The JSON covers every
        department, so every department of the plan is covered.

        Args:
            plan: Breeds and departments to read.

        Returns:
            The listings, the departments covered and the page read.

        Raises:
            SourceReadError: When the JSON cannot be read.
        """
        collection = HtmlCollection(collected_department_codes={department.code for department in plan.departments})
        if not plan.breeds:
            return collection
        response_text = self.polite_client.get(ADS_URL, accept="application/json").text
        collection.raw_pages.append(HtmlRawPage(ADS_URL, response_text))
        breed_ids_by_breed_name = {breed.source_slug: breed.breed_id for breed in plan.breeds}
        for ad in self.parse_ads(response_text):
            breed_id = breed_ids_by_breed_name.get(str(ad.get("race")))
            if breed_id is None or str(ad.get("departement")) not in collection.collected_department_codes:
                continue
            listing = self.listing_of_ad(ad, breed_id)
            if listing is not None:
                collection.listings.append(listing)
        return collection

    @staticmethod
    def parse_ads(response_text: str) -> list[dict[str, Any]]:
        """
        The ads of the JSON.

        Args:
            response_text: Body of the JSON response.

        Returns:
            The ads, in the order of the JSON.

        Raises:
            SourceReadError: When the body is not the list of ads.
        """
        try:
            ads = json.loads(response_text)
        except ValueError as error:
            raise SourceReadError(f"Cœur de Cocker : JSON illisible ({error})") from error
        if not isinstance(ads, list):
            raise SourceReadError("Cœur de Cocker : le JSON n'est plus une liste d'annonces")
        return [ad for ad in ads if isinstance(ad, dict)]

    @classmethod
    def listing_of_ad(cls, ad: dict[str, Any], breed_id: int) -> RawListing | None:
        """
        Read one ad: one puppy, its sex, its colour and whether it is still to adopt.

        Args:
            ad: The ad, as the JSON gives it.
            breed_id: Breed the listing was read for.

        Returns:
            A puppy ad, or None for an adult dog.
        """
        if ad.get("type") != PUPPY_TYPE:
            return None
        puppy_sex = cls._lowercase_without_accents(ad.get("sexe"))
        color_label = ad.get("couleur") if isinstance(ad.get("couleur"), str) else None
        color = COLORS_BY_LABEL.get(cls._lowercase_without_accents(color_label))
        lof_answer = cls._lowercase_without_accents(ad.get("lof"))
        slug = ad.get("slug") if isinstance(ad.get("slug"), str) else None
        return RawListing(
            source=ListingSource.COEUR_DE_COCKER,
            external_id=f"annonce-{ad['id']}",
            breed_id=breed_id,
            kind=ListingKind.PUPPY_AD,
            lof_status=LOF_STATUSES_BY_ANSWER.get(lof_answer, LofStatus.UNKNOWN),
            external_url=f"{COEUR_DE_COCKER_BASE_URL}/adoption/chien/{slug}/" if slug else None,
            birth_date=cls._date(ad.get("date_naissance")),
            male_count=cls._puppy_count_of_sex(puppy_sex, MALE),
            female_count=cls._puppy_count_of_sex(puppy_sex, FEMALE),
            puppies_available=1 if (ad.get("statut") or AVAILABLE_STATUS) == AVAILABLE_STATUS else 0,
            colors=(ColorReading(color, ColorConfidence.CERTAIN),) if color is not None else (),
            color_text=color_label,
            price_cents=cls._price_cents(ad.get("prix")),
            department_code=str(ad["departement"]) if ad.get("departement") else None,
            photos=cls._photos(ad.get("photos_urls")),
            breeder=cls._breeder(ad),
            published_at=cls._published_at(ad.get("date")),
            raw_json={"statut": ad.get("statut"), "type": ad.get("type"), "titre": ad.get("titre")},
        )

    @staticmethod
    def _breeder(ad: dict[str, Any]) -> RawBreeder | None:
        """
        The breeder of an ad, named by its Cœur de Cocker slug; its breeding name gives the affix that joins it to
        the same breeder on the Centrale Canine (same affix, same department).

        Args:
            ad: The ad.

        Returns:
            The breeder, or None when the ad does not name one.
        """
        slug = ad.get("eleveur_slug")
        if not isinstance(slug, str) or not slug:
            return None
        published_name = ad.get("eleveur_nom")
        name = BreederContactParser.readable_name(published_name if isinstance(published_name, str) else None)
        return RawBreeder(source_id=slug, display_name=name, affix=BreederContactParser.affix_of_breeding_name(name))

    @staticmethod
    def _price_cents(text: Any) -> int | None:
        """
        The price of an ad, from « 800 » or « 1400 Euros »; « Nous contacter » gives none.

        Args:
            text: The ``prix`` value.

        Returns:
            The price in cents, or None when the ad gives no amount.
        """
        price_match = LEADING_AMOUNT_PATTERN.match(text.strip()) if isinstance(text, str) else None
        if price_match is None:
            return None
        euros = int(THOUSANDS_SEPARATOR_PATTERN.sub("", price_match.group(0)))
        return euros * 100

    @staticmethod
    def _puppy_count_of_sex(puppy_sex: str, counted_sex: str) -> int | None:
        """
        How many puppies of a sex an ad offers: one for the sex of its puppy, none for the other sex.

        Args:
            puppy_sex: Sex of the puppy of the ad, in lowercase and without accents (« male », « femelle »).
            counted_sex: The sex to count.

        Returns:
            1 or 0, or None when the ad does not give the sex of its puppy.
        """
        if puppy_sex not in (MALE, FEMALE):
            return None
        if puppy_sex == counted_sex:
            return 1
        return 0

    @staticmethod
    def _lowercase_without_accents(text: Any) -> str:
        """
        A value of the JSON in lowercase and without accents: « Mâle » gives « male ».

        Args:
            text: The value.

        Returns:
            The text, empty when the value is not a text.
        """
        if not isinstance(text, str):
            return ""
        return without_accents(text.strip().lower())

    @staticmethod
    def _date(text: Any) -> date | None:
        """
        A day of the JSON (``2026-07-15``).

        Args:
            text: The value.

        Returns:
            The day, or None when absent or impossible.
        """
        if not isinstance(text, str):
            return None
        try:
            return date.fromisoformat(text)
        except ValueError:
            return None

    @staticmethod
    def _published_at(text: Any) -> datetime | None:
        """
        The publication time of the JSON (``2026-08-27 13:26:25``, French time), as the database stores it.

        Args:
            text: The value.

        Returns:
            The naive UTC time, or None when absent or unreadable.
        """
        if not isinstance(text, str):
            return None
        try:
            french_moment = datetime.fromisoformat(text).replace(tzinfo=FRENCH_TIMEZONE)
        except ValueError:
            return None
        return french_moment.astimezone(UTC).replace(tzinfo=None)

    @staticmethod
    def _photos(text: Any) -> tuple[str, ...]:
        """
        The photos of an ad, from the comma-separated list of the JSON.

        Args:
            text: The ``photos_urls`` value.

        Returns:
            Photo URLs, in order, each once.
        """
        if not isinstance(text, str):
            return ()
        urls = [url.strip() for url in text.split(",")]
        photo_urls = [url for url in urls if url.startswith("http")]
        return tuple(dict.fromkeys(photo_urls))
