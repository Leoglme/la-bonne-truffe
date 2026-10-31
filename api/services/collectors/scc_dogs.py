"""
Centrale Canine dog collector: the page of a litter, which names its parents and lists its registered puppies,
then the page of each dog, which gives its colour, rating and health tests (docs/02, « Portée », « Chien »).

Same access rules as the litters: a browser User-Agent, one request per second, relayed by the desktop app
when the server is refused. Only what describes a dog is kept: the owner's contact details of the page are
dropped before anything is stored (docs/01, « Données personnelles »).
"""

import logging
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any

import httpx

from enums.dog_role import DogRole
from enums.dog_sex import DogSex
from enums.listing_source import ListingSource
from services.collectors.breeder_contact_parser import BreederContactParser
from services.collectors.centrale_canine import (
    SCC_BASE_URL,
    SCC_BROWSER_USER_AGENT,
    SccJsonPage,
    fetch_json_page,
    scc_absolute_url,
)
from services.collectors.polite_http_client import PoliteHttpClient
from services.collectors.raw_dog import RawDog
from services.collectors.scc_value_parser import SccValueParser
from services.dog_color_inference import DogColorInference

logger = logging.getLogger(__name__)

FRENCH_DATE_FORMAT = "%d/%m/%Y"
MALE_FLAG = "O"
FEMALE_FLAG = "N"


@dataclass(frozen=True)
class SccLitterTarget:
    """A litter whose Centrale Canine page is read, and which of its dogs' pages are worth reading."""

    group_id: int
    scc_litter_id: str
    read_parents: bool
    read_puppies: bool
    fresh_dog_ids: frozenset[str] = frozenset()


@dataclass(frozen=True)
class SccDogCollectionPlan:
    """What one run reads: the litters in priority order, within a budget of pages."""

    litters: tuple[SccLitterTarget, ...]
    page_budget: int


@dataclass(frozen=True)
class RawPuppyReference:
    """One registered puppy as the litter page lists it, before its own page is read."""

    dog_id: str
    name: str | None
    identifier: str | None
    sex: DogSex


@dataclass(frozen=True)
class RawLitterDetail:
    """What the page of a litter adds to its listing: the identifiers of the parents and the registered puppies."""

    group_id: int
    scc_litter_id: str
    sire_dog_id: str | None
    dam_dog_id: str | None
    puppies: tuple[RawPuppyReference, ...]


@dataclass
class SccDogCollection:
    """Litter details and dogs read by a run, the raw pages they come from, and how many pages were read."""

    litter_details: list[RawLitterDetail] = field(default_factory=list)
    dogs: list[RawDog] = field(default_factory=list)
    raw_pages: list[SccJsonPage] = field(default_factory=list)
    pages_read: int = 0


class SccDogCollector:
    """Reads litter and dog pages, politely, within the budget of the plan."""

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
    def litter_url(scc_litter_id: str) -> str:
        """
        URL of the JSON of a litter.

        Args:
            scc_litter_id: ``n_litter_id`` of the litter (the number of its ``/portee/<id>`` page).

        Returns:
            The URL, query string excluded.
        """
        return f"{SCC_BASE_URL}/api/litter/{scc_litter_id}"

    @staticmethod
    def dog_url(dog_id: str) -> str:
        """
        URL of the JSON of a dog.

        Args:
            dog_id: LOF Select identifier of the dog.

        Returns:
            The URL, query string excluded.
        """
        return f"{SCC_BASE_URL}/api/dog/{dog_id}"

    def collect(self, plan: SccDogCollectionPlan) -> SccDogCollection:
        """
        Read the litters of the plan, then the dogs each one names, until the budget of pages is spent.

        Args:
            plan: Litters to read, in priority order, and the budget.

        Returns:
            The litter details and the dogs found, with the raw pages.

        Raises:
            CentraleCanineError: When a page cannot be read; the run fails as a whole.
        """
        collection = SccDogCollection()
        for target in plan.litters:
            if collection.pages_read >= plan.page_budget:
                break
            detail = self.parse_litter_detail(self._fetch(collection, self.litter_url(target.scc_litter_id)), target)
            if detail is None:
                continue
            collection.litter_details.append(detail)
            for dog_id, role in self._dog_pages_of(detail, target):
                if collection.pages_read >= plan.page_budget:
                    break
                dog = self.parse_dog(self._fetch(collection, self.dog_url(dog_id)), role, detail.group_id)
                if dog is not None:
                    collection.dogs.append(dog)
        return collection

    @staticmethod
    def _dog_pages_of(detail: RawLitterDetail, target: SccLitterTarget) -> list[tuple[str, DogRole]]:
        """
        The dog pages a litter calls for: its parents, then its puppies, minus the pages read recently.

        Args:
            detail: What the litter page said.
            target: What the plan asks for this litter.

        Returns:
            Dog identifier and role, in reading order, each once.
        """
        pages: dict[str, DogRole] = {}
        if target.read_parents:
            for parent_id in (detail.sire_dog_id, detail.dam_dog_id):
                if parent_id is not None:
                    pages.setdefault(parent_id, DogRole.PARENT)
        if target.read_puppies:
            for puppy in detail.puppies:
                pages.setdefault(puppy.dog_id, DogRole.PUPPY)
        return [(dog_id, role) for dog_id, role in pages.items() if dog_id not in target.fresh_dog_ids]

    def _fetch(self, collection: SccDogCollection, url: str) -> dict[str, Any]:
        """
        Read one JSON page and count it.

        Args:
            collection: The collection, whose pages are counted and kept.
            url: Address to read.

        Returns:
            The decoded JSON object.

        Raises:
            CentraleCanineError: When the page cannot be read or is not a JSON object.
        """
        payload = fetch_json_page(self.polite_client, url, {"_format": "json"})
        collection.pages_read += 1
        collection.raw_pages.append(SccJsonPage(url, payload))
        return payload

    @classmethod
    def parse_litter_detail(cls, payload: dict[str, Any], target: SccLitterTarget) -> RawLitterDetail | None:
        """
        Read the parents and the registered puppies of a litter page.

        The identifiers of the parents are those of their dog nodes (``node[<n_father>].n_dog_id``), never
        ``n_father`` itself, which numbers another entity (docs/02).

        Args:
            payload: Decoded page.
            target: The litter asked for.

        Returns:
            The detail, or None for a page that holds no litter (one not relayed yet).
        """
        main_content = payload.get("main_content")
        if not isinstance(main_content, dict):
            return None
        nodes = payload.get("node")
        nodes_by_id = nodes if isinstance(nodes, dict) else {}
        return RawLitterDetail(
            group_id=target.group_id,
            scc_litter_id=target.scc_litter_id,
            sire_dog_id=cls._parent_dog_id(main_content.get("n_father"), nodes_by_id),
            dam_dog_id=cls._parent_dog_id(main_content.get("n_mother"), nodes_by_id),
            puppies=cls._puppies(payload.get("dogs")),
        )

    @staticmethod
    def _parent_dog_id(node_reference: object, nodes_by_id: dict[str, Any]) -> str | None:
        """
        The LOF Select identifier of a parent, from the node the litter references.

        Args:
            node_reference: ``n_father`` or ``n_mother`` of the litter.
            nodes_by_id: The ``node`` block of the page.

        Returns:
            The identifier, or None when the page does not describe the parent.
        """
        node_id = SccValueParser.to_text(node_reference)
        node = nodes_by_id.get(node_id or "")
        if not isinstance(node, dict):
            return None
        return SccValueParser.to_text(node.get("n_dog_id"))

    @staticmethod
    def _puppies(dogs_block: object) -> tuple[RawPuppyReference, ...]:
        """
        The registered puppies of the ``dogs`` block, males then females.

        Args:
            dogs_block: ``{"male": {<id>: {...}}, "female": {...}}``, or nothing before the registration.

        Returns:
            The puppies, each with its dog identifier taken from the end of its page slug.
        """
        if not isinstance(dogs_block, dict):
            return ()
        puppies: list[RawPuppyReference] = []
        for sex_key, sex in (("male", DogSex.MALE), ("female", DogSex.FEMALE)):
            entries = dogs_block.get(sex_key)
            if not isinstance(entries, dict):
                continue
            for entry in entries.values():
                if not isinstance(entry, dict):
                    continue
                slug = SccValueParser.to_text(entry.get("url")) or ""
                dog_id = slug.rsplit("-", 1)[-1] if "-" in slug else slug
                if not dog_id.isdigit():
                    continue
                puppies.append(
                    RawPuppyReference(
                        dog_id=dog_id,
                        name=BreederContactParser.readable_name(SccValueParser.to_text(entry.get("n_name"))),
                        identifier=SccValueParser.to_text(entry.get("n_id")),
                        sex=sex,
                    )
                )
        return tuple(puppies)

    @classmethod
    def parse_dog(cls, payload: dict[str, Any], role: DogRole, litter_group_id: int) -> RawDog | None:
        """
        Read a dog page: identity, colour, rating, health tests, parents. Nothing of the owner is kept.

        Args:
            payload: Decoded page.
            role: Why the dog is read: a parent or a puppy of the litter.
            litter_group_id: The litter, kept on a puppy only.

        Returns:
            The dog, or None for a page that holds no dog (one not relayed yet).
        """
        web_service = payload.get("ws")
        dog = web_service.get("chien") if isinstance(web_service, dict) else None
        if not isinstance(dog, dict) or dog.get("id") is None:
            return None
        health_codes = cls._health_codes(dog.get("santes"))
        color_code = SccValueParser.to_text(dog.get("couleur"))
        dna = dog.get("adn")
        sire = dog.get("pere")
        dam = dog.get("mere")
        return RawDog(
            source=ListingSource.CENTRALE_CANINE,
            external_id=str(dog["id"]),
            role=role,
            external_url=scc_absolute_url(SccValueParser.to_text(payload.get("url"))),
            litter_group_id=litter_group_id if role == DogRole.PUPPY else None,
            name=BreederContactParser.readable_name(SccValueParser.to_text(dog.get("nom"))),
            affix=BreederContactParser.readable_name(SccValueParser.to_text(dog.get("affixe"))),
            full_name=SccValueParser.to_text(dog.get("nomComplet")),
            sex=cls._sex(SccValueParser.to_text(dog.get("sexeMale"))),
            birth_date=cls._french_date(SccValueParser.to_text(dog.get("dateNaissance"))),
            lof_number=SccValueParser.to_text(dog.get("numLof")),
            identifier=SccValueParser.to_text(dog.get("puce")) or SccValueParser.to_text(dog.get("tatouage")),
            color_code=color_code,
            color=DogColorInference.canonical_color(color_code),
            rating=SccValueParser.to_int(dog.get("cotation")),
            health_codes=health_codes,
            e_locus=DogColorInference.e_locus_of(health_codes),
            has_dna_profile=bool(dna) if isinstance(dna, list) else None,
            sire_external_id=str(sire["id"]) if isinstance(sire, dict) and sire.get("id") is not None else None,
            dam_external_id=str(dam["id"]) if isinstance(dam, dict) and dam.get("id") is not None else None,
        )

    @staticmethod
    def _health_codes(tests: object) -> tuple[str, ...]:
        """
        The codes of the health tests of a dog page.

        Args:
            tests: ``santes``: a list of ``{"code", "libelle", ...}``.

        Returns:
            The codes, in page order.
        """
        if not isinstance(tests, list):
            return ()
        codes: list[str] = []
        for test in tests:
            code = SccValueParser.to_text(test.get("code")) if isinstance(test, dict) else None
            if code:
                codes.append(code)
        return tuple(codes)

    @staticmethod
    def _sex(flag: str | None) -> DogSex:
        """
        The sex of a dog, from its ``sexeMale`` flag.

        Args:
            flag: « O » for a male, « N » for a female.

        Returns:
            The sex, unknown for any other value.
        """
        if flag == MALE_FLAG:
            return DogSex.MALE
        if flag == FEMALE_FLAG:
            return DogSex.FEMALE
        return DogSex.UNKNOWN

    @staticmethod
    def _french_date(text: str | None) -> date | None:
        """
        Read a date written ``05/07/2026``.

        Args:
            text: The date, or None.

        Returns:
            The date, or None when absent or unreadable.
        """
        if not text:
            return None
        try:
            return datetime.strptime(text, FRENCH_DATE_FORMAT).date()
        except ValueError:
            return None
