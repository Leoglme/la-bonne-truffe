"""ChiotsDeFranceCollector: real (anonymized) pages, the France listing, crossbreeds, withdrawn ads."""

from datetime import date, datetime

import httpx

from core.config import settings
from enums.listing_kind import ListingKind
from enums.lof_status import LofStatus
from services.collectors.chiots_de_france import ChiotsDeFranceCollector, ListedLitterAd
from services.collectors.html_source import HtmlBreedTarget, HtmlCollectionPlan, HtmlDepartmentTarget
from services.collectors.raw_listing import RawBreeder
from tests.chiots_de_france_pages import chiots_de_france_collector_serving, recorded_page

AD_URL = "https://www.chiots-de-france.com/detail-annonce-cocker-spaniel-anglais_{}_5.html"
LISTED_AD_OF_BREEDER_A = ListedLitterAd("annonce-486970", AD_URL.format(486970), "35", is_lof=True)
PLAN = HtmlCollectionPlan(
    breeds=(HtmlBreedTarget(breed_id=1, source_slug="cocker-spaniel-anglais"),),
    departments=(HtmlDepartmentTarget("35", "Bretagne"), HtmlDepartmentTarget("72", "Pays de la Loire")),
)


def test_listing_page_lists_the_ads_with_their_department_and_leaves_the_type_ads_out() -> None:
    listed_ads = ChiotsDeFranceCollector.parse_listing_page(recorded_page("listing_france.html"))

    assert [(ad.external_id, ad.department_code, ad.is_lof) for ad in listed_ads] == [
        ("annonce-494858", "50", True),
        ("annonce-487726", "72", True),
        ("annonce-486970", "35", True),
    ]


def test_ad_page_gives_a_born_litter_with_its_available_puppies_and_breeder() -> None:
    listing = ChiotsDeFranceCollector.parse_ad_page(recorded_page("ad_486970.html"), 1, LISTED_AD_OF_BREEDER_A)

    assert (listing.kind, listing.lof_status) == (ListingKind.LITTER_BORN, LofStatus.LOF)
    assert listing.birth_date == date(2026, 8, 28)
    assert (listing.male_count, listing.female_count, listing.puppies_available) == (1, 0, 1)
    assert listing.price_cents == 140000
    assert (listing.zip_code, listing.city, listing.department_code) == ("35140", "Saint-Aubin-du-Cormier", "35")
    assert (listing.sire_name, listing.dam_name) == ("Père de test 11", "Mère de test 12")
    assert listing.published_at == datetime(2026, 10, 4)
    assert listing.photos and all("/portees/" in photo for photo in listing.photos)
    assert listing.breeder == RawBreeder(
        source_id="elevage-a",
        affix="Du Clos de l'Élevage A",
        siren="000000001",
        zip_code="35140",
        city="Saint-Aubin-du-Cormier",
    )


def test_ad_without_price_keeps_its_price_unknown_and_its_lof_from_the_card() -> None:
    listing = ChiotsDeFranceCollector.parse_ad_page(
        recorded_page("ad_487726.html"), 1, ListedLitterAd("annonce-487726", AD_URL.format(487726), "72", is_lof=False)
    )

    assert listing.price_cents is None
    assert (listing.male_count, listing.female_count) == (0, 1)
    assert listing.lof_status == LofStatus.NON_LOF
    assert listing.breeder is not None
    assert (listing.breeder.source_id, listing.breeder.siren) == ("elevage-f", "000000006")


def test_collect_reads_the_france_listing_then_the_ads_of_the_profile_departments() -> None:
    requests: list[httpx.Request] = []

    collection = chiots_de_france_collector_serving(requests).collect(PLAN)

    assert [request.url.path for request in requests] == [
        "/chiots/cocker-spaniel-anglais/france",
        "/detail-annonce-cocker-spaniel-anglais_487726_5.html",
        "/detail-annonce-cocker-spaniel-anglais_486970_5.html",
    ]
    assert requests[0].headers["User-Agent"] == settings.honest_user_agent
    assert [listing.external_id for listing in collection.listings] == ["annonce-487726", "annonce-486970"]
    assert collection.collected_department_codes == {"35", "72"}


def test_ad_withdrawn_meanwhile_is_skipped() -> None:
    withdrawn_path = "/detail-annonce-cocker-spaniel-anglais_487726_5.html"

    collection = chiots_de_france_collector_serving(withdrawn_paths=frozenset({withdrawn_path})).collect(PLAN)

    assert [listing.external_id for listing in collection.listings] == ["annonce-486970"]
