"""ChiensDeFranceCollector: real (anonymized) pages, one listing per region, withdrawn ads, politeness."""

from datetime import date, datetime

import httpx

from core.config import settings
from enums.listing_kind import ListingKind
from enums.lof_status import LofStatus
from services.collectors.chiens_de_france import ChiensDeFranceCollector, ListedAd
from services.collectors.html_source import HtmlBreedTarget, HtmlCollectionPlan, HtmlDepartmentTarget
from services.collectors.raw_listing import RawBreeder
from tests.chiens_de_france_pages import chiens_de_france_collector_serving, recorded_page

COCKER = HtmlBreedTarget(breed_id=1, source_slug="cocker-spaniel-anglais")
LISTED_PUPPY = ListedAd(ListingKind.PUPPY_AD, "chiot-2199887", "https://www.chiens-de-france.com/chiot/2199887", "35")
LISTED_LITTER_TO_COME = ListedAd(
    ListingKind.LITTER_EXPECTED, "saillie-494882", "https://www.chiens-de-france.com/saillie/494882", "35"
)


def test_listing_page_lists_the_ads_under_each_department_heading() -> None:
    listed_ads = ChiensDeFranceCollector.parse_listing_page(recorded_page("listing_bretagne.html"))

    assert [(ad.kind, ad.external_id, ad.department_code) for ad in listed_ads] == [
        (ListingKind.PUPPY_AD, "chiot-2199887", "35"),
        (ListingKind.PUPPY_AD, "chiot-2199888", "35"),
        (ListingKind.LITTER_EXPECTED, "saillie-494882", "35"),
    ]


def test_puppy_page_gives_one_puppy_its_litter_code_and_its_breeder() -> None:
    listing = ChiensDeFranceCollector.parse_ad_page(recorded_page("puppy_2199887.html"), 1, LISTED_PUPPY)

    assert (listing.kind, listing.lof_status) == (ListingKind.PUPPY_AD, LofStatus.LOF)
    assert listing.litter_number == "LOF-2026024873-2026-13"
    assert listing.birth_date == date(2026, 8, 28)
    assert (listing.male_count, listing.female_count, listing.puppies_available) == (1, 0, 1)
    assert listing.price_cents == 140000
    assert (listing.zip_code, listing.city, listing.department_code) == ("35140", "Saint-Aubin-du-Cormier", "35")
    assert (listing.sire_name, listing.dam_name) == ("Père de test 11", "Mère de test 12")
    assert listing.published_at == datetime(2026, 10, 3)
    assert listing.colors == ()
    assert len(listing.photos) == 2
    assert listing.breeder == RawBreeder(
        source_id="elevage-a",
        affix="Du Clos de l'Élevage A",
        siren="000000001",
        zip_code="35140",
        city="Saint-Aubin-du-Cormier",
        website="https://elevage-a.chiens-de-france.com",
    )


def test_litter_to_come_page_gives_its_mating_date_and_unknown_sexes() -> None:
    listing = ChiensDeFranceCollector.parse_ad_page(
        recorded_page("litter_to_come_494882.html"), 1, LISTED_LITTER_TO_COME
    )

    assert listing.kind == ListingKind.LITTER_EXPECTED
    assert listing.mating_date == date(2026, 8, 28)
    assert (listing.birth_date, listing.male_count, listing.female_count) == (None, None, None)
    assert (listing.sire_name, listing.dam_name) == ("Père de test 11", "Mère de test 15 Du Clos de l'Élevage A")
    assert (listing.zip_code, listing.city) == ("35140", "Saint-Aubin-du-Cormier")
    assert listing.breeder is not None
    assert (listing.breeder.source_id, listing.breeder.siren) == ("elevage-a", "000000001")


def test_collect_reads_the_region_once_then_each_ad_and_skips_a_withdrawn_one() -> None:
    requests: list[httpx.Request] = []
    plan = HtmlCollectionPlan(
        breeds=(COCKER,),
        departments=(HtmlDepartmentTarget("35", "Bretagne"), HtmlDepartmentTarget("56", "Bretagne")),
    )

    collection = chiens_de_france_collector_serving(requests).collect(plan)

    assert [request.url.path for request in requests] == [
        "/chiots/cocker-spaniel-anglais/france/bretagne",
        "/chiot/2199887",
        "/chiot/2199888",
        "/saillie/494882",
    ]
    assert requests[0].headers["User-Agent"] == settings.honest_user_agent
    assert [listing.external_id for listing in collection.listings] == ["chiot-2199887", "saillie-494882"]
    assert collection.collected_department_codes == {"35", "56"}
    assert len(collection.raw_pages) == 3


def test_collect_waits_a_second_before_each_request_after_the_first() -> None:
    pauses: list[float] = []
    plan = HtmlCollectionPlan(breeds=(COCKER,), departments=(HtmlDepartmentTarget("35", "Bretagne"),))

    chiens_de_france_collector_serving(pauses=pauses).collect(plan)

    assert pauses == [1.0, 1.0, 1.0]


def test_department_of_an_unknown_region_is_not_read() -> None:
    requests: list[httpx.Request] = []
    plan = HtmlCollectionPlan(breeds=(COCKER,), departments=(HtmlDepartmentTarget("98", "Monaco"),))

    collection = chiens_de_france_collector_serving(requests).collect(plan)

    assert requests == []
    assert collection.collected_department_codes == set()
