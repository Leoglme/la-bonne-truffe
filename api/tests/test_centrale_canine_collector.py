"""CentraleCanineCollector: parsing of the documented JSON shape, polite paging, refusals."""

import copy
import json
from datetime import date
from pathlib import Path
from typing import Any

import httpx
import pytest

from services.collectors.centrale_canine import (
    SCC_BROWSER_USER_AGENT,
    CentraleCanineCollectionPlan,
    CentraleCanineCollector,
    CentraleCanineError,
    SccBreedTarget,
    SccDepartmentTarget,
    SccVarietyTarget,
)
from services.collectors.raw_listing import RawListing

FIXTURES = Path(__file__).parent / "fixtures" / "centrale_canine"

COCKER = SccBreedTarget(
    breed_id=1,
    scc_slug="cocker-spaniel-anglais",
    varieties_by_source_id={
        "317": SccVarietyTarget(covered_colors=("gold",), is_ambiguous=False),
        "159": SccVarietyTarget(covered_colors=("noir", "noir_et_feu", "marron", "marron_et_feu"), is_ambiguous=True),
    },
)
ILLE_ET_VILAINE = SccDepartmentTarget(code="35", scc_term_id="t_41")


def load_page() -> dict[str, Any]:
    """The synthetic page of the fixtures (documented shape, test values)."""
    return json.loads((FIXTURES / "litters_35_page_0.json").read_text(encoding="utf-8"))


def listings_by_id(listings: list[RawListing]) -> dict[str, RawListing]:
    """Index listings by their source identifier."""
    return {listing.external_id: listing for listing in listings}


def test_born_litter_reads_sexes_dates_and_certain_gold() -> None:
    listing = listings_by_id(CentraleCanineCollector().parse_litters_payload(load_page(), COCKER, "35"))["9000001"]

    assert listing.kind == "litter_born"
    assert listing.lof_status == "lof"
    assert listing.birth_date == date(2026, 10, 27)
    assert listing.mating_date == date(2026, 8, 24)
    assert (listing.male_count, listing.female_count) == (2, 3)
    assert [color.as_json() for color in listing.colors] == [{"color": "gold", "confidence": "certain"}]
    assert listing.litter_number == "LOF-TEST-0001"
    assert (listing.sire_rating, listing.dam_rating) == (4, 2)
    assert (listing.breeder_source_id, listing.breeder_selection_group) == ("7000001", 1)
    assert listing.external_url == "https://www.centrale-canine.fr/portee/9000001"
    assert listing.department_code == "35"
    assert listing.photos == ()


def test_expected_litter_keeps_sexes_unknown_instead_of_zero() -> None:
    listing = listings_by_id(CentraleCanineCollector().parse_litters_payload(load_page(), COCKER, "35"))["9000002"]

    assert listing.kind == "litter_expected"
    assert listing.birth_date is None
    assert listing.mating_date == date(2026, 10, 10)
    assert (listing.male_count, listing.female_count) == (None, None)
    assert listing.litter_number is None
    assert (listing.sire_rating, listing.dam_rating) == (5, None)


def test_bundle_variety_is_ambiguous_and_unknown_variety_stays_uncoloured() -> None:
    listings = listings_by_id(CentraleCanineCollector().parse_litters_payload(load_page(), COCKER, "35"))

    bundle = listings["9000003"]
    assert {color.confidence for color in bundle.colors} == {"ambiguous"}
    assert len(bundle.colors) == 4
    assert bundle.litter_rating == 3.5
    assert bundle.photos == ("https://www.centrale-canine.fr/sites/default/files/test/portee-9000003.jpg",)

    unknown_variety = listings["9000004"]
    assert unknown_variety.colors == ()
    assert unknown_variety.color_text == "variété de test inconnue"


def test_empty_node_list_from_php_gives_no_listing() -> None:
    payload = {"litters": {"count": 0, "node": []}}

    assert CentraleCanineCollector().parse_litters_payload(payload, COCKER, "35") == []


def test_collect_pages_politely_with_a_browser_user_agent() -> None:
    first_page = load_page()
    first_page["litters"]["count"] = 12
    second_page = copy.deepcopy(load_page())
    second_page["litters"]["node"] = {
        "1": {"n9000099": {**first_page["litters"]["node"]["1"]["n9000001"], "n_id": 9000099}}
    }
    requests: list[httpx.Request] = []

    def answer(request: httpx.Request) -> httpx.Response:
        """Serve page 0 then page 1, like the real endpoint."""
        requests.append(request)
        page = first_page if request.url.path.endswith("/0") else second_page
        return httpx.Response(200, json=page)

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
    assert len(collection.listings) == 5
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
