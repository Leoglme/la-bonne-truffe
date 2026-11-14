"""ChiensDeFranceSiteCollector: real (anonymized) pages of a breeder site, the reading order, a failing site, politeness."""

from dataclasses import replace
from datetime import date, datetime

import httpx
from selectolax.lexbor import LexborHTMLParser

from core.config import settings
from enums.coat_color import CoatColor
from enums.color_confidence import ColorConfidence
from enums.dog_role import DogRole
from enums.dog_sex import DogSex
from enums.listing_kind import ListingKind
from enums.lof_status import LofStatus
from services.collectors.chiens_de_france import litter_photos_of
from services.collectors.chiens_de_france_sites import (
    ChiensDeFranceSiteCollector,
    ListedDog,
    SiteCollectionPlan,
    SiteDirectoryPlan,
    SiteNewsPost,
    breed_page_of,
)
from services.collectors.raw_dog import RawBreederSiteFacts, RawBreederSiteLitter, RawSiteDirectoryEntry
from services.collectors.raw_listing import ColorReading, RawBreeder, RawListing
from tests.chiens_de_france_site_pages import (
    BROKEN_SITE_SLUG,
    DIRECTORY_LIST_URL,
    EMPTY_SITE_SLUG,
    OTHER_BREED_SITE_SLUG,
    RECORDED_PAGES_BY_PATH,
    RECORDED_SITE_SLUG,
    SINGLE_LITTER_SITE_SLUG,
    chiens_de_france_site_collector_serving,
    recorded_page,
    site_target,
)

RECORDED_SITE = site_target(RECORDED_SITE_SLUG)
SINGLE_LITTER_SITE = site_target(SINGLE_LITTER_SITE_SLUG)
SITE_URL = "https://elevage-a.chiens-de-france.com"
SINGLE_LITTER_SITE_URL = "https://elevage-e.chiens-de-france.com"
BREED_URL = f"{SITE_URL}/cocker-spaniel-anglais"
BREEDER = RawBreeder(source_id="elevage-a", affix="Du Clos de l'Élevage A", website=SITE_URL)
NEWS_PHOTO_URL = f"{SITE_URL}/media_cdf/photos/eleveurs/0/0/actualites/photo-de-test-50.jpg"
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
    "/cocker-spaniel-anglais/actualites",
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


RECORDED_LITTER: list[RawListing] = ChiensDeFranceSiteCollector.parse_litter_for_sale_page(
    parsed("litter_for_sale_495610.html"), RECORDED_SITE, f"{BREED_URL}/chiots-a-vendre/495610"
)


def test_litters_to_come_page_gives_one_litter_per_mating_with_its_date_and_parents() -> None:
    listings = ChiensDeFranceSiteCollector.parse_litters_to_come_page(parsed("litters_to_come.html"), RECORDED_SITE)

    assert [listing.external_id for listing in listings] == ["saillie-495662", "saillie-495668"]
    assert [listing.external_url for listing in listings] == [
        "https://www.chiens-de-france.com/saillie/495662",
        "https://www.chiens-de-france.com/saillie/495668",
    ]
    assert [listing.breeder_site_page_url for listing in listings] == [
        f"{BREED_URL}/saillie/495662",
        f"{BREED_URL}/saillie/495668",
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


def test_page_of_a_single_litter_for_sale_gives_that_litter_by_its_canonical_address() -> None:
    litter_ids = ChiensDeFranceSiteCollector.parse_litters_for_sale_page(parsed("single_litter_for_sale_493883.html"))

    assert litter_ids == ["493883"]


def test_puppy_shown_by_a_thumbnail_gets_the_full_size_photo_it_opens_and_a_puppy_without_photo_none() -> None:
    listings = ChiensDeFranceSiteCollector.parse_litter_for_sale_page(
        parsed("single_litter_for_sale_493883.html"),
        SINGLE_LITTER_SITE,
        f"{SINGLE_LITTER_SITE_URL}/cocker-spaniel-anglais/chiots-a-vendre/493883",
    )

    assert [listing.photos for listing in listings] == [
        (f"{SINGLE_LITTER_SITE_URL}/media_cdf/photos/eleveurs/0/0/portees/photo-de-test-20.jpg",),
        (),
        (f"{SINGLE_LITTER_SITE_URL}/media_cdf/photos/eleveurs/0/0/portees/photo-de-test-21.jpg",),
    ]


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
    assert listings[0].breeder_site_page_url == f"{page_url}#:~:text=2199888"
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


def test_litter_for_sale_page_gives_each_puppy_the_day_its_title_says_the_puppies_may_leave() -> None:
    listings = ChiensDeFranceSiteCollector.parse_litter_for_sale_page(
        parsed("litter_for_sale_495610.html"), RECORDED_SITE, f"{BREED_URL}/chiots-a-vendre/495610"
    )
    single_litter_listings = ChiensDeFranceSiteCollector.parse_litter_for_sale_page(
        parsed("single_litter_for_sale_493883.html"),
        SINGLE_LITTER_SITE,
        f"{SINGLE_LITTER_SITE_URL}/cocker-spaniel-anglais/chiots-a-vendre/493883",
    )

    assert {(listing.birth_date, listing.available_from) for listing in listings} == {
        (date(2026, 8, 28), date(2026, 10, 30))
    }
    assert {(listing.birth_date, listing.available_from) for listing in single_litter_listings} == {
        (date(2026, 8, 9), date(2026, 11, 2))
    }


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


def test_dog_page_showing_a_gallery_gives_the_photo_it_shares_then_the_photos_of_its_gallery() -> None:
    listed_female = ListedDog("1479070", f"{BREED_URL}/chien/1479070", "Chien de test 41", None, None)

    dog = ChiensDeFranceSiteCollector.parse_dog_page(parsed("dog_1479070.html"), RECORDED_SITE, listed_female)

    assert (dog.full_name, dog.sex, dog.identifier, dog.rating) == (
        "Chien de test 41",
        DogSex.FEMALE,
        "250000000000007",
        1,
    )
    assert dog.photos == (
        f"{SITE_URL}/media_cdf/photos/chiens/2026_11/photo-de-test-41.jpg",
        "https://www.chiens-de-france.com/photo/eleveurs/0/0/album/photo-de-test-42.jpg",
        "https://www.chiens-de-france.com/photo/eleveurs/0/0/album/photo-de-test-43.jpg",
    )


def test_dog_page_without_photo_takes_the_photo_of_its_list() -> None:
    list_photo_url = f"{SITE_URL}/media_cdf/photos/chiens/2026_11/photo-de-test-46.jpg"
    listed_stud = ListedDog("1386355", f"{BREED_URL}/chien/1386355", "Père de test 11", None, list_photo_url)
    tree = LexborHTMLParser(
        "<article class='article-main'><h2>PÈRE DE TEST 11</h2><h3>mâle né le 04/12/2022</h3></article>"
    )

    dog = ChiensDeFranceSiteCollector.parse_dog_page(tree, RECORDED_SITE, listed_stud)

    assert dog.photos == (list_photo_url,)


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
        f"{BREED_URL}/actualites",
        f"{BREED_URL}/chiots-vendus",
        f"{BREED_URL}/chiens/femelles",
        f"{BREED_URL}/chiens/etalons",
        f"{BREED_URL}/chien/1212400",
    ]
    assert collection.failed_sites == []


def test_collect_gives_the_puppies_of_a_litter_the_colour_a_post_of_the_site_tells() -> None:
    plan = SiteCollectionPlan(sites=(RECORDED_SITE,))

    collection = chiens_de_france_site_collector_serving().collect(plan)

    puppy_ads = [listing for listing in collection.listings if listing.kind == ListingKind.PUPPY_AD]
    assert {puppy_ad.colors for puppy_ad in puppy_ads} == {
        (ColorReading(CoatColor.NOIR_ET_FEU, ColorConfidence.CERTAIN),)
    }
    assert {puppy_ad.color_text for puppy_ad in puppy_ads} == {"Chiots LOF Noirs feu disponibles à la réservation"}


def test_news_that_cannot_be_read_do_not_stop_the_reading_of_the_site() -> None:
    def answer(request: httpx.Request) -> httpx.Response:
        """
        Serve the recorded pages of the site, and an error for its news.

        Args:
            request: The collector's request.

        Returns:
            The page, a 500 for the news or a 404.
        """
        if request.url.path.endswith("/actualites"):
            return httpx.Response(500)
        file_name = RECORDED_PAGES_BY_PATH.get(request.url.path)
        return httpx.Response(200, text=recorded_page(file_name)) if file_name else httpx.Response(404)

    collector = ChiensDeFranceSiteCollector(
        http_client=httpx.Client(transport=httpx.MockTransport(answer)),
        sleep=lambda _seconds: None,
        monotonic_clock=lambda: 0.0,
    )

    collection = collector.collect(SiteCollectionPlan(sites=(RECORDED_SITE,)))

    puppy_ads = [listing for listing in collection.listings if listing.kind == ListingKind.PUPPY_AD]
    assert collection.failed_sites == []
    assert len(puppy_ads) == 4
    assert {puppy_ad.colors for puppy_ad in puppy_ads} == {()}
    assert [dog.external_id for dog in collection.dogs] == ["1212400"]


def test_news_page_gives_each_post_with_its_title_the_text_under_it_its_day_and_its_photo() -> None:
    news_posts = ChiensDeFranceSiteCollector.parse_news_page(parsed("news.html"))

    assert news_posts == [
        SiteNewsPost("Chiots LOF Noirs feu disponibles à la réservation", "", date(2026, 9, 2), NEWS_PHOTO_URL),
        SiteNewsPost(
            "Une belle journée d'exposition",
            "Texte de test de l'actualité.",
            date(2026, 6, 14),
            f"{SITE_URL}/media_cdf/photos/eleveurs/0/0/actualites/photo-de-test-51.jpg",
        ),
    ]


def test_a_puppy_whose_ad_shows_no_photo_takes_the_photos_of_the_posts_about_its_litter() -> None:
    litter_without_photo = [replace(puppy_ad, photos=()) for puppy_ad in RECORDED_LITTER[:2]]
    later_photo_url = f"{SITE_URL}/media_cdf/photos/eleveurs/0/0/actualites/photo-de-test-52.jpg"
    news_posts = [
        SiteNewsPost("Les bébés sont nés", "", date(2026, 8, 29), NEWS_PHOTO_URL),
        SiteNewsPost("Les chiots ont trois semaines", "", date(2026, 9, 18), later_photo_url),
        SiteNewsPost("Une belle journée d'exposition", "", date(2026, 9, 20), "https://example.test/exposition.jpg"),
    ]

    puppy_ads = ChiensDeFranceSiteCollector.puppy_ads_told_by_news([litter_without_photo], news_posts)
    puppy_ads_with_photos = ChiensDeFranceSiteCollector.puppy_ads_told_by_news([RECORDED_LITTER], news_posts)

    assert {puppy_ad.photos for puppy_ad in puppy_ads} == {(later_photo_url, NEWS_PHOTO_URL)}
    assert puppy_ads_with_photos == RECORDED_LITTER


def test_a_post_speaks_of_the_last_litter_born_before_it_and_the_last_post_has_the_last_word() -> None:
    older_litter = [replace(puppy_ad, birth_date=date(2026, 7, 19)) for puppy_ad in RECORDED_LITTER[:2]]
    news_posts = [
        SiteNewsPost("Nos bébés sont nés", "Quatre chiots dorés", date(2026, 8, 29)),
        SiteNewsPost("Chiots noirs feu disponibles", "", date(2026, 9, 2)),
    ]

    puppy_ads = ChiensDeFranceSiteCollector.puppy_ads_told_by_news([older_litter, RECORDED_LITTER], news_posts)

    assert [puppy_ad.colors for puppy_ad in puppy_ads[:2]] == [(), ()]
    assert {puppy_ad.colors for puppy_ad in puppy_ads[2:]} == {
        (ColorReading(CoatColor.NOIR_ET_FEU, ColorConfidence.CERTAIN),)
    }


def test_a_post_naming_several_colours_gives_the_puppies_possible_colours() -> None:
    news_posts = [SiteNewsPost("Naissance", "Des chiots golden et des chiots noir et feu", date(2026, 8, 30))]

    puppy_ads = ChiensDeFranceSiteCollector.puppy_ads_told_by_news([RECORDED_LITTER], news_posts)

    assert {puppy_ad.colors for puppy_ad in puppy_ads} == {
        (
            ColorReading(CoatColor.GOLD, ColorConfidence.AMBIGUOUS),
            ColorReading(CoatColor.NOIR_ET_FEU, ColorConfidence.AMBIGUOUS),
        )
    }


def test_a_post_tells_no_colour_before_the_birth_long_after_it_or_when_it_is_not_about_puppies() -> None:
    news_posts = [
        SiteNewsPost("Chiots golden attendus", "", date(2026, 8, 20)),
        SiteNewsPost("Chiots golden disponibles", "", date(2026, 12, 1)),
        SiteNewsPost("Notre étalon noir et feu est disponible pour saillie", "", date(2026, 9, 2)),
        SiteNewsPost("Les chiots grandissent bien", "", date(2026, 9, 5)),
    ]

    puppy_ads = ChiensDeFranceSiteCollector.puppy_ads_told_by_news([RECORDED_LITTER], news_posts)

    assert puppy_ads == RECORDED_LITTER


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
                RawBreederSiteLitter(
                    date(2026, 8, 28), "Père de test 11", "Mère de test 12 Du Clos de l'Élevage A", "495610"
                ),
                RawBreederSiteLitter(
                    date(2026, 7, 19), "Père de test 13", "Chien de test 1 Du Clos de l'Élevage A", "494507"
                ),
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


def test_site_whose_puppy_list_sends_to_its_single_litter_gives_the_puppies_of_that_litter() -> None:
    plan = SiteCollectionPlan(sites=(SINGLE_LITTER_SITE,))

    collection = chiens_de_france_site_collector_serving().collect(plan)

    puppy_ads = [listing for listing in collection.listings if listing.kind == ListingKind.PUPPY_AD]
    assert [puppy_ad.external_id for puppy_ad in puppy_ads] == ["chiot-2192294", "chiot-2192298", "chiot-2192299"]
    assert [(puppy_ad.male_count, puppy_ad.female_count) for puppy_ad in puppy_ads] == [(1, 0), (0, 1), (0, 1)]
    assert [puppy_ad.puppies_available for puppy_ad in puppy_ads] == [0, 0, 0]
    assert {puppy_ad.birth_date for puppy_ad in puppy_ads} == {date(2026, 8, 9)}
    assert {puppy_ad.dam_name for puppy_ad in puppy_ads} == {"Mère de test 35 Du Clos de l'Élevage E"}
    assert collection.failed_sites == []


def test_site_whose_future_litters_send_to_its_single_mating_gives_that_litter_to_come() -> None:
    plan = SiteCollectionPlan(sites=(SINGLE_LITTER_SITE,))

    collection = chiens_de_france_site_collector_serving().collect(plan)

    litters_to_come = [listing for listing in collection.listings if listing.kind == ListingKind.LITTER_EXPECTED]
    assert [litter.external_id for litter in litters_to_come] == ["saillie-496471"]
    assert litters_to_come[0].external_url == "https://www.chiens-de-france.com/saillie/496471"
    assert litters_to_come[0].breeder_site_page_url == f"{SINGLE_LITTER_SITE_URL}/cocker-spaniel-anglais/saillie/496471"
    assert litters_to_come[0].mating_date == date(2026, 6, 7)
    assert (litters_to_come[0].sire_name, litters_to_come[0].dam_name) == (
        "Père de test 34",
        "Mère de test 35 Du Clos de l'Élevage E",
    )


def test_a_site_that_sends_the_breed_to_another_gives_nothing_of_that_other_breed() -> None:
    plan = SiteCollectionPlan(sites=(site_target(OTHER_BREED_SITE_SLUG),))

    collection = chiens_de_france_site_collector_serving().collect(plan)

    assert (collection.listings, collection.dogs, collection.raw_pages, collection.failed_sites) == ([], [], [], [])
    assert [facts.cover_photo_url for facts in collection.site_facts] == [None]


def test_an_image_without_a_file_is_no_photo() -> None:
    page = LexborHTMLParser(
        f"""
        <div class="boximg">
          <img src="{SITE_URL}/media_cdf/photos/eleveurs/326/65148/portees/">
          <img src="{SITE_URL}/media_cdf/photos/eleveurs/326/65148/portees/chiot-1.jpg">
        </div>
        <article class="article-main"><img src="{SITE_URL}/media_cdf/photos/eleveurs/326/65148/presentations/"></article>
        """
    )

    assert litter_photos_of(page) == (f"{SITE_URL}/media_cdf/photos/eleveurs/326/65148/portees/chiot-1.jpg",)
    assert ChiensDeFranceSiteCollector.home_cover_photo(page) is None


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


def test_the_home_of_a_site_leads_to_the_pages_of_the_breed_and_any_other_address_stays() -> None:
    breed_slug = "cocker-spaniel-anglais"

    assert breed_page_of(SITE_URL, breed_slug) == BREED_URL
    assert breed_page_of(f"{SITE_URL}/", breed_slug) == BREED_URL
    assert breed_page_of(f"{SITE_URL}/cavalier-king-charles", breed_slug) == f"{SITE_URL}/cavalier-king-charles"
    assert breed_page_of("https://www.chiens-de-france.com", breed_slug) == "https://www.chiens-de-france.com"
    assert breed_page_of("https://www.ferme-des-tests.fr", breed_slug) == "https://www.ferme-des-tests.fr"
    assert breed_page_of(SITE_URL, "") == SITE_URL
    assert breed_page_of(None, breed_slug) is None


def test_the_menu_of_a_site_gives_its_social_accounts() -> None:
    assert ChiensDeFranceSiteCollector.parse_social_links(parsed("litters_born.html")) == {
        "facebook": "https://www.facebook.com/elevage.a.test"
    }
    assert ChiensDeFranceSiteCollector.parse_social_links(parsed("litters_to_come.html")) == {}


def test_litters_born_page_gives_each_litter_of_the_year_with_its_date_and_parents() -> None:
    litters = ChiensDeFranceSiteCollector.parse_litters_born_page(parsed("litters_born.html"))

    assert litters == [
        RawBreederSiteLitter(date(2026, 8, 28), "Père de test 11", "Mère de test 12 Du Clos de l'Élevage A", "495610"),
        RawBreederSiteLitter(date(2026, 7, 19), "Père de test 13", "Chien de test 1 Du Clos de l'Élevage A", "494507"),
    ]


def test_the_name_of_a_puppy_gives_its_colour_but_not_the_one_of_its_collar() -> None:
    page = (
        recorded_page("litter_for_sale_495610.html")
        .replace("Chiot de test 2", "Femelle noire et feu")
        .replace("Chiot de test 3", "Mâle collier bleu")
    )
    site = site_target(RECORDED_SITE_SLUG)

    puppy_ads = ChiensDeFranceSiteCollector.parse_litter_for_sale_page(LexborHTMLParser(page), site, "page")
    named_in_colour, named_by_its_collar = puppy_ads[0], puppy_ads[1]

    assert named_in_colour.colors == (ColorReading(CoatColor.NOIR_ET_FEU, ColorConfidence.CERTAIN),)
    assert named_in_colour.color_text == "Femelle noire et feu"
    assert (named_by_its_collar.colors, named_by_its_collar.color_text) == ((), None)


def test_a_post_does_not_change_the_colour_the_name_of_a_puppy_gives() -> None:
    puppy_named_in_colour = replace(
        RECORDED_LITTER[0], colors=(ColorReading(CoatColor.NOIR_ET_FEU, ColorConfidence.CERTAIN),)
    )
    post = SiteNewsPost("Chiots golden disponibles", "", date(2026, 9, 1))

    told = ChiensDeFranceSiteCollector.puppy_ads_told_by_news([[puppy_named_in_colour]], [post])

    assert told[0].colors == (ColorReading(CoatColor.NOIR_ET_FEU, ColorConfidence.CERTAIN),)


def test_collect_reads_the_page_of_a_parent_of_a_litter_the_site_does_not_list() -> None:
    requests: list[httpx.Request] = []

    def answer(request: httpx.Request) -> httpx.Response:
        """
        Serve the single litter of ``elevage-e``, which lists no dog, and the page of the father of that litter.

        Args:
            request: The collector's request.

        Returns:
            The page, or a 404.
        """
        requests.append(request)
        if request.url.path in ("/cocker-spaniel-anglais/chiots", "/cocker-spaniel-anglais/chiots-a-vendre/493883"):
            return httpx.Response(200, text=recorded_page("single_litter_for_sale_493883.html"))
        if request.url.path == "/cocker-spaniel-anglais/chien/1374851":
            return httpx.Response(200, text=recorded_page("dog_1212400.html"))
        return httpx.Response(404)

    collector = ChiensDeFranceSiteCollector(
        http_client=httpx.Client(transport=httpx.MockTransport(answer)),
        sleep=lambda _seconds: None,
        monotonic_clock=lambda: 0.0,
    )

    collection = collector.collect(SiteCollectionPlan(sites=(SINGLE_LITTER_SITE,)))

    read_paths = [request.url.path for request in requests]
    assert "/cocker-spaniel-anglais/chien/1374851" in read_paths
    assert "/cocker-spaniel-anglais/chien/1299945" in read_paths
    assert [(dog.external_id, dog.role, bool(dog.photos)) for dog in collection.dogs] == [
        ("1374851", DogRole.REPRODUCER, True)
    ]


def test_only_the_recent_litters_the_site_no_longer_offers_are_read_again() -> None:
    litters_born = ChiensDeFranceSiteCollector.parse_litters_born_page(parsed("litters_born.html"))

    recent_ones = ChiensDeFranceSiteCollector.recent_litter_ids_no_longer_offered(
        litters_born, ["495610"], date(2026, 7, 1)
    )
    after_the_window = ChiensDeFranceSiteCollector.recent_litter_ids_no_longer_offered(
        litters_born, ["495610"], date(2026, 8, 1)
    )
    without_a_window = ChiensDeFranceSiteCollector.recent_litter_ids_no_longer_offered(litters_born, [], None)

    assert (recent_ones, after_the_window, without_a_window) == (["494507"], [], [])


def test_collect_reads_the_page_of_a_recent_litter_moved_to_the_litters_born() -> None:
    requests: list[httpx.Request] = []
    one_litter_for_sale = f'<a href="{SITE_URL}/cocker-spaniel-anglais/chiots-a-vendre/495610">Chiots</a>'

    def answer(request: httpx.Request) -> httpx.Response:
        """
        Serve the recorded site, whose « Chiots disponibles » now offers a single litter of the two born.

        Args:
            request: The collector's request.

        Returns:
            The page, or a 404.
        """
        requests.append(request)
        if request.url.path == "/cocker-spaniel-anglais/chiots":
            return httpx.Response(200, text=one_litter_for_sale)
        file_name = RECORDED_PAGES_BY_PATH.get(request.url.path)
        return httpx.Response(200, text=recorded_page(file_name)) if file_name else httpx.Response(404)

    collector = ChiensDeFranceSiteCollector(
        http_client=httpx.Client(transport=httpx.MockTransport(answer)),
        sleep=lambda _seconds: None,
        monotonic_clock=lambda: 0.0,
    )

    collector.collect(SiteCollectionPlan(sites=(RECORDED_SITE,), oldest_birth_read=date(2026, 7, 1)))

    read_paths = [request.url.path for request in requests]
    assert read_paths.count("/cocker-spaniel-anglais/chiots-a-vendre/494507") == 1
    assert read_paths.count("/cocker-spaniel-anglais/chiots-a-vendre/495610") == 1


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
