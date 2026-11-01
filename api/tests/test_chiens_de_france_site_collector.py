"""ChiensDeFranceSiteCollector: real (anonymized) pages of a breeder site, the reading order, a failing site, politeness."""

from datetime import date, datetime

import httpx
from selectolax.lexbor import LexborHTMLParser

from core.config import settings
from enums.coat_color import CoatColor
from enums.dog_role import DogRole
from enums.dog_sex import DogSex
from enums.listing_kind import ListingKind
from enums.lof_status import LofStatus
from services.collectors.chiens_de_france_sites import (
    ChiensDeFranceSiteCollector,
    ListedDog,
    SiteCollectionPlan,
    SiteDirectoryPlan,
)
from services.collectors.raw_dog import RawBreederSiteFacts, RawBreederSiteLitter, RawSiteDirectoryEntry
from services.collectors.raw_listing import RawBreeder
from tests.chiens_de_france_site_pages import (
    BROKEN_SITE_SLUG,
    DIRECTORY_LIST_URL,
    EMPTY_SITE_SLUG,
    RECORDED_SITE_SLUG,
    chiens_de_france_site_collector_serving,
    recorded_page,
    site_target,
)

RECORDED_SITE = site_target(RECORDED_SITE_SLUG)
SITE_URL = "https://elevage-a.chiens-de-france.com"
BREED_URL = f"{SITE_URL}/cocker-spaniel-anglais"
BREEDER = RawBreeder(source_id="elevage-a", affix="Du Clos de l'Élevage A", website=SITE_URL)
LISTED_FEMALE = ListedDog(
    external_id="1212400",
    url=f"{BREED_URL}/chien/1212400",
    name="Chien de test 1 Du Clos de l'Élevage A",
    status_text="Chien à vendre",
    photo_url=f"{SITE_URL}/media_cdf/photos/chiens/2020_04/photo-de-test-3.png",
)
RECORDED_SITE_PATHS = [
    "/cocker-spaniel-anglais/saillies",
    "/cocker-spaniel-anglais/chiots",
    "/cocker-spaniel-anglais/chiots-a-vendre/495610",
    "/cocker-spaniel-anglais/chiots-a-vendre/494507",
    "/cocker-spaniel-anglais/chiots-vendus",
    "/cocker-spaniel-anglais/chiens/femelles",
    "/cocker-spaniel-anglais/chiens/males",
    "/cocker-spaniel-anglais/chiens/etalons",
    "/cocker-spaniel-anglais/chien/1212400",
    "/cocker-spaniel-anglais/chien/1430047",
    "/cocker-spaniel-anglais/chien/1386355",
    "/cocker-spaniel-anglais/chien/1264388",
]


def parsed(file_name: str) -> LexborHTMLParser:
    """
    Parse a recorded page.

    Args:
        file_name: Its file in the fixtures.

    Returns:
        The parsed page.
    """
    return LexborHTMLParser(recorded_page(file_name))


def test_litters_to_come_page_gives_one_litter_per_mating_with_its_date_and_parents() -> None:
    listings = ChiensDeFranceSiteCollector.parse_litters_to_come_page(parsed("litters_to_come.html"), RECORDED_SITE)

    assert [listing.external_id for listing in listings] == ["saillie-495662", "saillie-495668"]
    assert [listing.external_url for listing in listings] == [
        "https://www.chiens-de-france.com/saillie/495662",
        "https://www.chiens-de-france.com/saillie/495668",
    ]
    assert {(listing.kind, listing.lof_status) for listing in listings} == {
        (ListingKind.LITTER_EXPECTED, LofStatus.LOF)
    }
    assert [listing.mating_date for listing in listings] == [date(2026, 8, 28), date(2026, 9, 14)]
    assert [(listing.sire_name, listing.dam_name) for listing in listings] == [
        ("Père de test 11", "Mère de test 15 Du Clos de l'Élevage A"),
        ("Père de test 11", "Mère de test 16 Du Clos de l'Élevage A"),
    ]
    assert listings[0].breeder == BREEDER
    assert (listings[0].department_code, listings[0].city, listings[0].birth_date) == (None, None, None)


def test_litters_to_come_page_without_mating_gives_nothing() -> None:
    listings = ChiensDeFranceSiteCollector.parse_litters_to_come_page(
        parsed("litters_to_come_empty.html"), RECORDED_SITE
    )

    assert listings == []


def test_litters_for_sale_page_links_each_litter_once_despite_the_trailing_space() -> None:
    litter_ids = ChiensDeFranceSiteCollector.parse_litters_for_sale_page(parsed("litters_for_sale.html"))

    assert litter_ids == ["495610", "494507"]


def test_litter_for_sale_page_gives_one_puppy_ad_per_puppy_with_its_status_and_price() -> None:
    page_url = f"{BREED_URL}/chiots-a-vendre/495610"

    listings = ChiensDeFranceSiteCollector.parse_litter_for_sale_page(
        parsed("litter_for_sale_495610.html"), RECORDED_SITE, page_url
    )

    assert [listing.external_id for listing in listings] == [
        "chiot-2199888",
        "chiot-2199886",
        "chiot-2199889",
        "chiot-2199887",
    ]
    assert listings[0].external_url == "https://www.chiens-de-france.com/chiot/2199888"
    assert [listing.puppies_available for listing in listings] == [1, 0, 0, 0]
    assert [(listing.male_count, listing.female_count) for listing in listings] == [(1, 0), (1, 0), (0, 1), (1, 0)]
    assert [listing.price_cents for listing in listings] == [140000, None, None, None]
    assert {listing.litter_number for listing in listings} == {"LOF-2026024873-2026-13"}
    assert {listing.birth_date for listing in listings} == {date(2026, 8, 28)}
    assert {(listing.kind, listing.lof_status) for listing in listings} == {(ListingKind.PUPPY_AD, LofStatus.LOF)}
    assert {listing.published_at for listing in listings} == {datetime(2026, 10, 3)}
    assert {(listing.sire_name, listing.dam_name) for listing in listings} == {("Père de test 11", "Mère de test 12")}
    assert listings[0].photos == (
        "https://www.chiens-de-france.com/photo/eleveurs/0/0/portees/photo-de-test-5.jpg",
        "https://www.chiens-de-france.com/photo/eleveurs/0/0/portees/photo-de-test-6.jpg",
    )
    assert listings[3].photos == (
        "https://www.chiens-de-france.com/photo/eleveurs/0/0/portees/photo-de-test-11.jpg",
        "https://www.chiens-de-france.com/photo/eleveurs/0/0/portees/photo-de-test-12.jpg",
    )
    assert listings[0].breeder == BREEDER
    assert listings[0].raw_json["site_url"] == page_url


def test_litter_for_sale_page_counts_the_breeding_females_and_the_litters_of_the_year() -> None:
    counts = ChiensDeFranceSiteCollector.breeding_counts(parsed("litter_for_sale_495610.html"))

    assert counts == (18, 14)


def test_dog_list_page_gives_each_dog_its_state_and_its_photo() -> None:
    females = ChiensDeFranceSiteCollector.parse_dog_list_page(parsed("females.html"))
    studs = ChiensDeFranceSiteCollector.parse_dog_list_page(parsed("studs.html"))

    assert females[0] == LISTED_FEMALE
    assert (females[1].external_id, females[1].name, females[1].status_text) == ("1430047", "Mère de test 12", None)
    assert [(stud.external_id, stud.status_text) for stud in studs] == [
        ("1386355", "Disponible pour saillie"),
        ("1264388", "Disponible pour saillie"),
    ]


def test_dog_page_gives_the_sex_the_colour_the_chip_and_the_rating() -> None:
    dog = ChiensDeFranceSiteCollector.parse_dog_page(parsed("dog_1212400.html"), RECORDED_SITE, LISTED_FEMALE)

    assert (dog.external_id, dog.role, dog.breeder_source_id) == ("1212400", DogRole.REPRODUCER, "elevage-a")
    assert dog.external_url == f"{BREED_URL}/chien/1212400"
    assert (dog.full_name, dog.name, dog.affix) == (
        "Chien de test 1 Du Clos de l'Élevage A",
        "Chien de test 1",
        "Du Clos de l'Élevage A",
    )
    assert (dog.sex, dog.birth_date) == (DogSex.FEMALE, date(2018, 4, 19))
    assert (dog.color_code, dog.color) == ("Noire et blanche", CoatColor.PARTICOLORE)
    assert (dog.identifier, dog.rating, dog.availability_text) == ("250000000000003", 1, "En vente")
    assert (dog.sire_external_id, dog.dam_external_id) == ("973026", "752478")
    assert dog.photos == (f"{SITE_URL}/media_cdf/photos/chiens/2020_04/photo-de-test-3.png",)


def test_stud_without_status_row_takes_the_state_of_its_list() -> None:
    listed_stud = ListedDog("1386355", f"{BREED_URL}/chien/1386355", "Père de test 11", "Disponible pour saillie", None)
    tree = LexborHTMLParser(
        "<article class='article-main'><h2>PÈRE DE TEST 11</h2><h3>mâle né le 04/12/2022</h3></article>"
    )

    dog = ChiensDeFranceSiteCollector.parse_dog_page(tree, RECORDED_SITE, listed_stud)

    assert (dog.full_name, dog.name, dog.affix) == ("Père de Test 11", "Père de Test 11", None)
    assert (dog.sex, dog.birth_date, dog.availability_text) == (
        DogSex.UNKNOWN,
        date(2022, 12, 4),
        "Disponible pour saillie",
    )
    assert (dog.color, dog.rating, dog.photos) == (CoatColor.INCONNUE, None, ())


def test_collect_reads_the_pages_in_order_then_each_litter_and_each_dog_and_skips_the_missing_ones() -> None:
    requests: list[httpx.Request] = []
    plan = SiteCollectionPlan(sites=(RECORDED_SITE,))

    collection = chiens_de_france_site_collector_serving(requests).collect(plan)

    assert [request.url.path for request in requests] == RECORDED_SITE_PATHS
    assert {request.url.host for request in requests} == {"elevage-a.chiens-de-france.com"}
    assert requests[0].headers["User-Agent"] == settings.honest_user_agent
    assert [listing.external_id for listing in collection.listings] == [
        "saillie-495662",
        "saillie-495668",
        "chiot-2199888",
        "chiot-2199886",
        "chiot-2199889",
        "chiot-2199887",
    ]
    assert [dog.external_id for dog in collection.dogs] == ["1212400"]
    assert [page.url for page in collection.raw_pages] == [
        f"{BREED_URL}/saillies",
        f"{BREED_URL}/chiots",
        f"{BREED_URL}/chiots-a-vendre/495610",
        f"{BREED_URL}/chiots-vendus",
        f"{BREED_URL}/chiens/femelles",
        f"{BREED_URL}/chiens/etalons",
        f"{BREED_URL}/chien/1212400",
    ]
    assert collection.failed_sites == []


def test_collect_gives_the_facts_of_the_site_with_its_first_litter_photo_as_cover() -> None:
    plan = SiteCollectionPlan(sites=(RECORDED_SITE,))

    collection = chiens_de_france_site_collector_serving().collect(plan)

    assert collection.site_facts == [
        RawBreederSiteFacts(
            breeder_source_id="elevage-a",
            site_url=SITE_URL,
            cover_photo_url=f"{SITE_URL}/media_cdf/photos/eleveurs/0/0/portees/photo-de-test-1.jpg",
            breeding_females_count=18,
            litters_last_year_count=14,
            registered_on=None,
            facebook_url="https://www.facebook.com/elevage.a.test",
            litters_born=(
                RawBreederSiteLitter(date(2026, 8, 28), "Père de test 11", "Mère de test 12 Du Clos de l'Élevage A"),
                RawBreederSiteLitter(date(2026, 7, 19), "Père de test 13", "Chien de test 1 Du Clos de l'Élevage A"),
            ),
        )
    ]


def test_collect_waits_a_second_before_each_request_after_the_first() -> None:
    pauses: list[float] = []
    plan = SiteCollectionPlan(sites=(RECORDED_SITE,))

    chiens_de_france_site_collector_serving(pauses=pauses).collect(plan)

    assert pauses == [1.0] * (len(RECORDED_SITE_PATHS) - 1)


def test_fresh_dog_page_is_not_read_again() -> None:
    requests: list[httpx.Request] = []
    plan = SiteCollectionPlan(sites=(site_target(RECORDED_SITE_SLUG, frozenset({"1212400", "1430047"})),))

    collection = chiens_de_france_site_collector_serving(requests).collect(plan)

    assert [request.url.path for request in requests if "/chien/" in request.url.path] == [
        "/cocker-spaniel-anglais/chien/1386355",
        "/cocker-spaniel-anglais/chien/1264388",
    ]
    assert collection.dogs == []


def test_site_without_puppy_nor_dog_takes_its_cover_from_its_home_page() -> None:
    requests: list[httpx.Request] = []
    plan = SiteCollectionPlan(sites=(site_target(EMPTY_SITE_SLUG),))

    collection = chiens_de_france_site_collector_serving(requests).collect(plan)

    assert [request.url.path for request in requests] == [
        "/cocker-spaniel-anglais/saillies",
        "/cocker-spaniel-anglais/chiots",
        "/cocker-spaniel-anglais/chiots-vendus",
        "/cocker-spaniel-anglais/chiens/femelles",
        "/cocker-spaniel-anglais/chiens/males",
        "/cocker-spaniel-anglais/chiens/etalons",
        "/cocker-spaniel-anglais",
    ]
    assert (collection.listings, collection.dogs, collection.failed_sites) == ([], [], [])
    assert collection.site_facts == [
        RawBreederSiteFacts(
            breeder_source_id="elevage-b",
            site_url="https://elevage-b.chiens-de-france.com",
            cover_photo_url=f"{SITE_URL}/media_cdf/photos/eleveurs/0/0/presentations/photo-de-test-18.jpg",
        )
    ]


def test_failing_site_is_reported_and_the_next_site_is_still_read() -> None:
    requests: list[httpx.Request] = []
    plan = SiteCollectionPlan(sites=(site_target(BROKEN_SITE_SLUG), RECORDED_SITE))

    collection = chiens_de_france_site_collector_serving(requests).collect(plan)

    assert collection.failed_sites == ["https://elevage-c.chiens-de-france.com"]
    assert [request.url.host for request in requests[:2]] == [
        "elevage-c.chiens-de-france.com",
        "elevage-a.chiens-de-france.com",
    ]
    assert [facts.breeder_source_id for facts in collection.site_facts] == ["elevage-a"]
    assert len(collection.listings) == 6


def test_the_menu_of_a_site_gives_its_social_accounts() -> None:
    assert ChiensDeFranceSiteCollector.parse_social_links(parsed("litters_born.html")) == {
        "facebook": "https://www.facebook.com/elevage.a.test"
    }
    assert ChiensDeFranceSiteCollector.parse_social_links(parsed("litters_to_come.html")) == {}


def test_litters_born_page_gives_each_litter_of_the_year_with_its_date_and_parents() -> None:
    litters = ChiensDeFranceSiteCollector.parse_litters_born_page(parsed("litters_born.html"))

    assert litters == [
        RawBreederSiteLitter(date(2026, 8, 28), "Père de test 11", "Mère de test 12 Du Clos de l'Élevage A"),
        RawBreederSiteLitter(date(2026, 7, 19), "Père de test 13", "Chien de test 1 Du Clos de l'Élevage A"),
    ]


def test_regional_list_gives_each_breeder_site_with_its_postal_code() -> None:
    entries = ChiensDeFranceSiteCollector.parse_directory_page(parsed("breeders_directory.html"))

    assert entries == [
        RawSiteDirectoryEntry(SITE_URL, "Sarl La Ferme Des Tests", "35340", "Liffré"),
        RawSiteDirectoryEntry(
            "https://elevage-d.chiens-de-france.com", "Du Clos de l'Élevage D", "35340", "ille-et-vilaine"
        ),
    ]


def test_collect_directory_reads_each_list_and_skips_a_missing_one() -> None:
    requests: list[httpx.Request] = []
    missing_list_url = "https://www.chiens-de-france.com/eleveurs/cocker-spaniel-anglais/france/normandie"
    plan = SiteDirectoryPlan(list_urls=(DIRECTORY_LIST_URL, missing_list_url))

    collection = chiens_de_france_site_collector_serving(requests).collect_directory(plan)

    assert [request.url for request in requests] == [DIRECTORY_LIST_URL, missing_list_url]
    assert [entry.site_url for entry in collection.entries] == [SITE_URL, "https://elevage-d.chiens-de-france.com"]
    assert [page.url for page in collection.raw_pages] == [DIRECTORY_LIST_URL]
    assert collection.failed_urls == []
