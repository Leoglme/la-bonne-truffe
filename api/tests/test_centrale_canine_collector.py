"""CentraleCanineCollector: parsing of real (anonymized) pages, polite paging, refusals."""

import json
from datetime import date, datetime
from pathlib import Path
from typing import Any

import httpx
import pytest

from enums.coat_color import CoatColor
from services.collectors.centrale_canine import (
    SCC_BROWSER_USER_AGENT,
    CentraleCanineCollectionPlan,
    CentraleCanineCollector,
    CentraleCanineError,
    SccBreedTarget,
    SccDepartmentTarget,
    SccVarietyTarget,
)
from services.collectors.raw_listing import RawBreeder, RawListing
from tests.centrale_canine_pages import mark_breed_club_member

FIXTURES = Path(__file__).parent / "fixtures" / "centrale_canine"

COCKER = SccBreedTarget(
    breed_id=1,
    scc_slug="cocker-spaniel-anglais",
    varieties_by_source_id={
        "158": SccVarietyTarget(covered_colors=(CoatColor.GOLD,), is_ambiguous=False),
        "159": SccVarietyTarget(
            covered_colors=(CoatColor.NOIR, CoatColor.NOIR_ET_FEU, CoatColor.MARRON, CoatColor.MARRON_ET_FEU),
            is_ambiguous=True,
        ),
    },
)
ILLE_ET_VILAINE = SccDepartmentTarget(code="35", scc_term_id="t_41")


def load_page(page_number: int) -> dict[str, Any]:
    """A recorded page of the cocker litters in Ille-et-Vilaine."""
    page: dict[str, Any] = json.loads((FIXTURES / f"litters_35_page_{page_number}.json").read_text(encoding="utf-8"))
    return page


def listings_by_id(listings: list[RawListing]) -> dict[str, RawListing]:
    """Index listings by their source identifier."""
    return {listing.external_id: listing for listing in listings}


def parse_first_page() -> dict[str, RawListing]:
    """The listings of the first recorded page."""
    return listings_by_id(CentraleCanineCollector().parse_litters_payload(load_page(0), COCKER, "35"))


def test_born_litter_reads_the_drupal_lists_and_the_gold_variety() -> None:
    listing = parse_first_page()["4236807"]

    assert listing.kind == "litter_born"
    assert listing.lof_status == "lof"
    assert listing.birth_date == date(2026, 7, 5)
    assert listing.mating_date == date(2026, 5, 2)
    assert (listing.male_count, listing.female_count) == (2, 1)
    assert listing.variety_source_id == "158"
    assert listing.color_text == "rouge et dore"
    assert [color.as_json() for color in listing.colors] == [{"color": "gold", "confidence": "certain"}]
    assert listing.litter_number == "LOF-2026016223-2026-11"
    assert (listing.sire_rating, listing.dam_rating, listing.litter_rating) == (1, 1, 2.0)
    assert listing.external_url == "https://www.centrale-canine.fr/portee/2817650"
    assert listing.published_at == datetime(2026, 6, 22, 8, 19, 52)
    assert listing.department_code == "35"


def test_breeder_comes_from_the_breeders_block_of_the_page() -> None:
    listing = parse_first_page()["4236807"]

    assert listing.breeder == RawBreeder(
        source_id="379540",
        display_name="Éleveur B",
        affix="Du Clos de l'Élevage B",
        siren=None,
        phone_e164="+33600000002",
        zip_code="35140",
        city="Saint-Aubin-du-Cormier",
        latitude=48.26,
        longitude=-1.40,
        selection_group=2,
        is_breed_club_member=False,
    )
    assert (listing.zip_code, listing.city) == ("35140", "Saint-Aubin-du-Cormier")

    breeder_with_siren = parse_first_page()["4337070"].breeder
    assert breeder_with_siren is not None and breeder_with_siren.siren == "000000001"


def test_a_member_of_the_breed_club_is_told_by_its_breeders_entry() -> None:
    page = load_page(0)
    mark_breed_club_member([page], "4236807")

    listings = listings_by_id(CentraleCanineCollector().parse_litters_payload(page, COCKER, "35"))

    member = listings["4236807"].breeder
    other_breeder = listings["4337070"].breeder
    assert member is not None and member.is_breed_club_member is True
    assert other_breeder is not None and other_breeder.is_breed_club_member is False


def test_expected_litter_keeps_sexes_unknown_instead_of_zero() -> None:
    listing = parse_first_page()["4337070"]

    assert listing.kind == "litter_expected"
    assert listing.birth_date is None
    assert listing.mating_date == date(2026, 8, 31)
    assert (listing.male_count, listing.female_count) == (None, None)
    assert listing.litter_number is None


def test_a_born_litter_with_no_male_keeps_its_zero() -> None:
    listing = parse_first_page()["4337069"]

    assert (listing.male_count, listing.female_count) == (0, 2)


def test_bundle_variety_is_ambiguous_and_an_unmapped_variety_stays_uncoloured() -> None:
    listings = parse_first_page()

    bundle = listings["4320577"]
    assert {color.confidence for color in bundle.colors} == {"ambiguous"}
    assert len(bundle.colors) == 4
    assert bundle.color_text == "noir - noir et feu marron - marron et feu"

    other_colours = listings["4198846"]
    assert other_colours.variety_source_id == "317"
    assert other_colours.colors == ()
    assert other_colours.color_text == "autres couleurs"


def test_page_filters_list_departments_varieties_and_birth_statuses() -> None:
    filters = CentraleCanineCollector.page_filters(load_page(0))

    assert filters["department"]["t_41"] == "35 - Ile-et-Vilaine"
    assert filters["variety"] == {
        "158": "rouge et dore",
        "159": "noir - noir et feu marron - marron et feu",
        "317": "autres couleurs",
    }
    assert filters["is_borned"] == {"yes": "Disponibles", "no": "A naître", "all": "Toutes"}


def test_empty_node_list_from_php_gives_no_listing() -> None:
    payload = {"litters": {"count": 0, "node": []}}

    assert CentraleCanineCollector().parse_litters_payload(payload, COCKER, "35") == []


def test_collect_pages_politely_with_a_browser_user_agent() -> None:
    requests: list[httpx.Request] = []

    def answer(request: httpx.Request) -> httpx.Response:
        """Serve the two recorded pages, like the real endpoint."""
        requests.append(request)
        page_number = int(request.url.path.rsplit("/", 1)[1])
        return httpx.Response(200, json=load_page(page_number))

    pauses: list[float] = []
    collector = CentraleCanineCollector(
        http_client=httpx.Client(transport=httpx.MockTransport(answer)),
        sleep=pauses.append,
        monotonic_clock=lambda: 100.0,
    )

    collection = collector.collect(CentraleCanineCollectionPlan(breeds=(COCKER,), departments=(ILLE_ET_VILAINE,)))

    assert [request.url.path.rsplit("/", 1)[1] for request in requests] == ["0", "1"]
    assert dict(requests[0].url.params) == {
        "department": "t_41",
        "variety": "all",
        "is_borned": "all",
        "sort": "0",
        "_format": "json",
    }
    assert requests[0].headers["User-Agent"] == SCC_BROWSER_USER_AGENT
    assert requests[0].headers["Accept"] == "application/json"
    assert pauses == [1.0]
    assert len(collection.listings) == 19
    assert [page.page_number for page in collection.raw_pages] == [0, 1]


def test_cloudflare_refusal_is_reported_without_retrying() -> None:
    calls: list[httpx.Request] = []

    def refuse(request: httpx.Request) -> httpx.Response:
        """Behave like Cloudflare challenging a data-centre IP."""
        calls.append(request)
        return httpx.Response(403, headers={"cf-mitigated": "challenge"}, text="Just a moment...")

    collector = CentraleCanineCollector(http_client=httpx.Client(transport=httpx.MockTransport(refuse)))

    with pytest.raises(CentraleCanineError, match="Cloudflare"):
        collector.collect(CentraleCanineCollectionPlan(breeds=(COCKER,), departments=(ILLE_ET_VILAINE,)))
    assert len(calls) == 1
