"""WhoofCollector: the real (anonymized) listing, its JSON, the puppies left, the coats, the pages."""

from datetime import date, datetime
from typing import Any

import httpx
import pytest
from sqlalchemy.orm import Session

from core.config import settings
from enums.coat_color import CoatColor
from enums.color_confidence import ColorConfidence
from enums.listing_kind import ListingKind
from enums.listing_source import ListingSource
from enums.lof_status import LofStatus
from models.litter_group import LitterGroup
from seeders.run_seeders import SeederRunner
from services.collection_runner import collection_runner
from services.collectors.html_source import HtmlBreedTarget, HtmlCollectionPlan, HtmlDepartmentTarget
from services.collectors.polite_http_client import SourceReadError
from services.collectors.raw_listing import ColorReading
from services.collectors.whoof import WhoofCollector
from services.matching.snapshot_builder import LitterSnapshotBuilder
from tests.stored_listings import listing_of
from tests.whoof_pages import listing_with, recorded_ads, recorded_listing, whoof_collector_serving

PLAN = HtmlCollectionPlan(
    breeds=(HtmlBreedTarget(breed_id=1, source_slug="cocker-spaniel-anglais"),),
    departments=(HtmlDepartmentTarget("35", "Bretagne"), HtmlDepartmentTarget("53", "Pays de la Loire")),
)


def ad_of(ad_id: int) -> dict[str, Any]:
    """The recorded ad of an identifier."""
    return next(ad for ad in recorded_ads() if ad["id"] == ad_id)


def coat(values: list[str], **marks: bool) -> dict[str, Any]:
    """A coat of the given colour values and marks."""
    return {"colors": [{"value": value, "label": value.capitalize()} for value in values], "modifications": marks}


def test_listing_page_gives_its_ads_and_its_last_page() -> None:
    ads, last_page_number = WhoofCollector.parse_listing_page(recorded_listing())

    assert [ad["id"] for ad in ads] == [519, 833, 843]
    assert last_page_number == 1


def test_ad_gives_the_puppies_left_their_lof_parents_and_their_breeder() -> None:
    listing = WhoofCollector.listing_of_ad(ad_of(833), 1)

    assert listing is not None
    assert (listing.source, listing.external_id, listing.kind) == (
        ListingSource.WHOOF,
        "annonce-833",
        ListingKind.PUPPY_AD,
    )
    assert listing.lof_status == LofStatus.LOF
    assert listing.birth_date == date(2026, 6, 1)
    assert (listing.male_count, listing.female_count, listing.puppies_available) == (2, 0, 2)
    assert listing.price_cents == 160000
    assert (listing.zip_code, listing.city, listing.department_code) == ("53000", "Laval", "53")
    assert (listing.sire_rating, listing.dam_rating) == (1, 1)
    assert listing.colors == (ColorReading(CoatColor.BLEU_ROUAN, ColorConfidence.CERTAIN),)
    assert listing.published_at == datetime(2026, 7, 9, 10, 1, 36)
    assert listing.external_url == "https://whoof.fr/annonces/elevage-de-test-w/chiot-cocker-anglais-bleu"
    assert listing.breeder is not None
    assert (listing.breeder.source_id, listing.breeder.siren) == ("elevage-de-test-w", "000000011")


def test_an_adoption_in_progress_leaves_no_puppy_and_a_ticked_coat_is_tricolour() -> None:
    listing = WhoofCollector.listing_of_ad(ad_of(843), 1)

    assert listing is not None
    assert listing.puppies_available == 0
    assert listing.colors == (ColorReading(CoatColor.TRICOLORE, ColorConfidence.CERTAIN),)


@pytest.mark.parametrize(
    ("ad_coat", "expected_color"),
    [
        (coat(["roux"]), CoatColor.GOLD),
        (coat(["dore"]), CoatColor.GOLD),
        (coat(["noir"]), CoatColor.NOIR),
        (coat(["noir"], black_fawn=True), CoatColor.NOIR_ET_FEU),
        (coat(["chocolat"], fawn=True), CoatColor.MARRON_ET_FEU),
        (coat(["chocolat", "blanc"], white_variegations=True), CoatColor.PARTICOLORE),
        (coat(["blanc", "orange"], roaned=True), CoatColor.ORANGE_ROUAN),
    ],
)
def test_a_coat_names_its_colour_only_when_it_is_certain(ad_coat: dict[str, Any], expected_color: CoatColor) -> None:
    listing = WhoofCollector.listing_of_ad({**ad_of(833), "coat": ad_coat}, 1)

    assert listing is not None
    assert listing.colors == (ColorReading(expected_color, ColorConfidence.CERTAIN),)


def test_an_unknown_coat_or_a_missing_birth_certificate_stays_unknown() -> None:
    listing = WhoofCollector.listing_of_ad(
        {**ad_of(833), "coat": coat(["gris", "beige"]), "documents": {"birth_certificate": False}}, 1
    )

    assert listing is not None
    assert listing.colors == ()
    assert listing.lof_status == LofStatus.UNKNOWN


def test_another_kind_of_ad_is_left_out() -> None:
    assert WhoofCollector.listing_of_ad({**ad_of(833), "type": "upcoming_litter"}, 1) is None


def test_collect_reads_the_listing_and_keeps_the_ads_of_the_profile_departments() -> None:
    requests: list[httpx.Request] = []

    collection = whoof_collector_serving(requests=requests).collect(PLAN)

    assert [str(request.url) for request in requests] == [
        "https://whoof.fr/race/cocker-spaniel-anglais/annonces?page=1"
    ]
    assert requests[0].headers["User-Agent"] == settings.honest_user_agent
    assert [listing.external_id for listing in collection.listings] == ["annonce-833", "annonce-843"]
    assert collection.collected_department_codes == {"35", "53"}


def test_collect_reads_every_page_of_the_listing() -> None:
    first_ad, second_ad, third_ad = recorded_ads()
    requests: list[httpx.Request] = []
    collector = whoof_collector_serving(
        {1: listing_with([first_ad, second_ad], 2), 2: listing_with([third_ad], 2)}, requests
    )

    collection = collector.collect(PLAN)

    assert [request.url.params["page"] for request in requests] == ["1", "2"]
    assert [listing.external_id for listing in collection.listings] == ["annonce-833", "annonce-843"]


def test_a_page_without_its_data_fails_the_run() -> None:
    collector = whoof_collector_serving({1: "<html><body>Maintenance</body></html>"})

    with pytest.raises(SourceReadError):
        collector.collect(PLAN)


def test_a_run_groups_the_ads_of_one_litter_and_counts_the_puppies_left(db: Session) -> None:
    SeederRunner.run(db)

    report = collection_runner.run_html_source(db, ListingSource.WHOOF, whoof_collector_serving())

    assert report.source_run.status == "ok"
    assert listing_of(db, "annonce-833").litter_group_id == listing_of(db, "annonce-843").litter_group_id
    group = db.get(LitterGroup, listing_of(db, "annonce-833").litter_group_id)
    assert group is not None
    assert group.puppies_available == 2
    snapshot = LitterSnapshotBuilder.build(db, group)
    assert snapshot is not None
    assert (snapshot.male_count, snapshot.female_count, snapshot.department_code) == (2, 0, "53")
