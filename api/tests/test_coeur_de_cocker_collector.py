"""CoeurDeCockerCollector: the real (anonymized) JSON, the puppies kept, their status, colour and price."""

from datetime import date, datetime

import httpx
import pytest

from core.config import settings
from enums.coat_color import CoatColor
from enums.color_confidence import ColorConfidence
from enums.listing_kind import ListingKind
from enums.listing_source import ListingSource
from enums.lof_status import LofStatus
from services.collectors.html_source import HtmlBreedTarget, HtmlCollectionPlan, HtmlDepartmentTarget
from services.collectors.polite_http_client import SourceReadError
from services.collectors.raw_listing import ColorReading
from tests.coeur_de_cocker_pages import coeur_de_cocker_collector_serving

PLAN = HtmlCollectionPlan(
    breeds=(HtmlBreedTarget(breed_id=1, source_slug="Cocker Anglais"),),
    departments=(HtmlDepartmentTarget("35", "Bretagne"), HtmlDepartmentTarget("56", "Bretagne")),
)


def test_collect_reads_the_json_once_and_keeps_the_puppies_of_the_profile_departments() -> None:
    requests: list[httpx.Request] = []

    collection = coeur_de_cocker_collector_serving(requests=requests).collect(PLAN)

    assert [str(request.url) for request in requests] == ["https://coeurdecocker.fr/wp-json/cdc/v1/adoption/annonces"]
    assert requests[0].headers["User-Agent"] == settings.honest_user_agent
    assert [listing.external_id for listing in collection.listings] == ["annonce-6258", "annonce-6171"]
    assert collection.collected_department_codes == {"35", "56"}


def test_a_puppy_still_to_adopt_gives_its_sex_its_status_and_its_breeder() -> None:
    listing = coeur_de_cocker_collector_serving().collect(PLAN).listings[0]

    assert (listing.source, listing.kind, listing.lof_status) == (
        ListingSource.COEUR_DE_COCKER,
        ListingKind.PUPPY_AD,
        LofStatus.NON_LOF,
    )
    assert (listing.male_count, listing.female_count, listing.puppies_available) == (1, 0, 1)
    assert listing.birth_date == date(2026, 7, 15)
    assert (listing.colors, listing.color_text) == ((), "Autre")
    assert listing.price_cents == 80000
    assert listing.department_code == "35"
    assert listing.published_at == datetime(2026, 8, 27, 11, 26, 25)
    assert listing.external_url == "https://coeurdecocker.fr/adoption/chien/chiot-de-test-1/"
    assert len(listing.photos) == 2
    assert listing.breeder is not None
    assert listing.breeder.source_id == "elevage-de-test-a"


def test_an_adopted_lof_puppy_leaves_none_and_gives_its_colour_and_price() -> None:
    listing = coeur_de_cocker_collector_serving().collect(PLAN).listings[1]

    assert listing.lof_status == LofStatus.LOF
    assert listing.puppies_available == 0
    assert listing.colors == (ColorReading(CoatColor.BLEU_ROUAN, ColorConfidence.CERTAIN),)
    assert listing.price_cents == 140000


def test_a_plan_without_breed_reads_nothing() -> None:
    requests: list[httpx.Request] = []

    collection = coeur_de_cocker_collector_serving(requests=requests).collect(
        HtmlCollectionPlan(breeds=(), departments=PLAN.departments)
    )

    assert requests == []
    assert collection.listings == []


@pytest.mark.parametrize("body", ["<html>Maintenance</html>", '{"code": "rest_no_route"}'])
def test_an_answer_that_is_not_the_list_of_ads_fails_the_run(body: str) -> None:
    with pytest.raises(SourceReadError):
        coeur_de_cocker_collector_serving(body=body).collect(PLAN)
