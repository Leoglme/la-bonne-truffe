"""ListingIngestionService: the breeder of a listing from one run to the next, and the litters too old to follow."""

from dataclasses import replace
from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session

from core.clock import naive_utc_now
from enums.listing_kind import ListingKind
from enums.listing_source import ListingSource
from enums.lof_status import LofStatus
from models.breed import Breed
from models.breeder import Breeder
from models.listing import Listing
from models.listing_change import ListingChange
from seeders.run_seeders import SeederRunner
from services.collectors.breeder_contact_parser import BreederContactParser
from services.collectors.chiots_de_france import ChiotsDeFranceCollector, ListedLitterAd
from services.collectors.html_source import HtmlBreedTarget, HtmlCollectionPlan, HtmlDepartmentTarget
from services.collectors.raw_listing import RawBreeder, RawListing
from services.listing_ingestion import BORN_LITTER_ACTIVE_DAYS, listing_ingestion_service
from tests.chiots_de_france_pages import recorded_page
from tests.coeur_de_cocker_pages import coeur_de_cocker_collector_serving

PRIVATE_SELLER_AD = ListedLitterAd(
    "annonce-487726",
    "https://www.chiots-de-france.com/detail-annonce-cocker-spaniel-anglais_487726_5.html",
    "72",
    is_lof=True,
)


def private_seller_ad(db: Session) -> RawListing:
    """The seeds, and the Chiots de France ad of a private seller, born on the first of October 2026."""
    SeederRunner.run(db)
    breed = db.query(Breed).one()
    ad = ChiotsDeFranceCollector.parse_ad_page(recorded_page("ad_487726.html"), breed.id, PRIVATE_SELLER_AD)
    return replace(ad, birth_date=date(2026, 10, 1))


def test_breeder_known_only_by_its_ad_stays_the_same_from_one_run_to_the_next(db: Session) -> None:
    ad = replace(private_seller_ad(db), breeder=RawBreeder(source_id="elevage-f", zip_code="72000", city="Le Mans"))

    listing_ingestion_service.ingest(db, ListingSource.CHIOTS_DE_FRANCE, [ad], {"72"}, naive_utc_now())
    first_breeder_id = db.query(Listing).one().breeder_id
    listing_ingestion_service.ingest(db, ListingSource.CHIOTS_DE_FRANCE, [ad], {"72"}, naive_utc_now())

    assert first_breeder_id is not None
    assert db.query(Listing).one().breeder_id == first_breeder_id
    assert db.query(Breeder).count() == 1


def test_an_ad_never_rewrites_the_affix_the_centrale_canine_wrote(db: Session) -> None:
    centrale_canine_ad = replace(
        private_seller_ad(db), breeder=RawBreeder(source_id="85379", affix="Du Clos de test A")
    )
    chiens_de_france_ad = replace(
        centrale_canine_ad, breeder=RawBreeder(source_id="elevage-a", affix="Du Clos De Test A")
    )

    listing_ingestion_service.ingest(db, ListingSource.CENTRALE_CANINE, [centrale_canine_ad], {"72"}, naive_utc_now())
    listing_ingestion_service.ingest(db, ListingSource.CHIENS_DE_FRANCE, [chiens_de_france_ad], {"72"}, naive_utc_now())

    assert db.query(Breeder).one().affix == "Du Clos de test A"


def test_the_centrale_canine_rewrites_the_affix_an_ad_wrote_first(db: Session) -> None:
    chiens_de_france_ad = replace(
        private_seller_ad(db), breeder=RawBreeder(source_id="elevage-a", affix="Du Clos De Test A")
    )
    centrale_canine_ad = replace(chiens_de_france_ad, breeder=RawBreeder(source_id="85379", affix="Du Clos de test A"))

    listing_ingestion_service.ingest(db, ListingSource.CHIENS_DE_FRANCE, [chiens_de_france_ad], {"72"}, naive_utc_now())
    first_affix = db.query(Breeder).one().affix
    listing_ingestion_service.ingest(db, ListingSource.CENTRALE_CANINE, [centrale_canine_ad], {"72"}, naive_utc_now())

    assert first_affix == "Du Clos De Test A"
    assert db.query(Breeder).one().affix == "Du Clos de test A"


def test_a_litter_born_too_long_ago_turns_inactive_once_and_stays_so_while_its_ad_is_online(db: Session) -> None:
    ad = private_seller_ad(db)
    fresh_run = datetime(2026, 10, 30, 12, 0)
    late_run = fresh_run + timedelta(days=BORN_LITTER_ACTIVE_DAYS + 1)

    listing_ingestion_service.ingest(db, ListingSource.CHIOTS_DE_FRANCE, [ad], {"72"}, fresh_run)
    aging_summary = listing_ingestion_service.ingest(db, ListingSource.CHIOTS_DE_FRANCE, [ad], {"72"}, late_run)
    listing_ingestion_service.ingest(db, ListingSource.CHIOTS_DE_FRANCE, [ad], {"72"}, late_run + timedelta(hours=1))

    listing = db.query(Listing).one()
    activity_changes = db.query(ListingChange).filter(ListingChange.field == "is_active").all()
    assert listing.is_active is False
    assert aging_summary.deactivated_listing_ids == [listing.id]
    assert [(change.old_value, change.new_value) for change in activity_changes] == [("true", "false")]


def test_a_litter_already_too_old_when_first_seen_is_stored_inactive(db: Session) -> None:
    ad = private_seller_ad(db)
    late_run = datetime(2026, 10, 1, 12, 0) + timedelta(days=BORN_LITTER_ACTIVE_DAYS + 1)

    listing_ingestion_service.ingest(db, ListingSource.CHIOTS_DE_FRANCE, [ad], {"72"}, late_run)

    assert db.query(Listing).one().is_active is False
    assert db.query(ListingChange).count() == 0


def test_a_coeur_de_cocker_ad_joins_the_breeder_of_the_centrale_canine_by_affix_and_department(db: Session) -> None:
    SeederRunner.run(db)
    breed = db.query(Breed).one()
    known_breeder = Breeder(
        affix="De test A",
        affix_normalized=BreederContactParser.affix_key("De test A"),
        department_code="35",
        scc_breeder_id="85379",
    )
    db.add(known_breeder)
    db.commit()
    plan = HtmlCollectionPlan(
        breeds=(HtmlBreedTarget(breed_id=breed.id, source_slug="Cocker Anglais"),),
        departments=(HtmlDepartmentTarget("35", "Bretagne"),),
    )
    ad = next(
        listing
        for listing in coeur_de_cocker_collector_serving().collect(plan).listings
        if listing.external_id == "annonce-6258"
    )

    listing_ingestion_service.ingest(db, ListingSource.COEUR_DE_COCKER, [ad], {"35"}, naive_utc_now())

    assert db.query(Listing).one().breeder_id == known_breeder.id
    assert db.query(Breeder).count() == 1


def test_a_reading_of_the_main_site_keeps_the_page_the_breeder_site_gave_without_counting_a_change(db: Session) -> None:
    SeederRunner.run(db)
    breed = db.query(Breed).one()
    main_site_url = "https://www.chiens-de-france.com/chiot/2199888"
    site_page_url = (
        "https://elevage-a.chiens-de-france.com/cocker-spaniel-anglais/chiots-a-vendre/495610#:~:text=2199888"
    )
    main_site_ad = RawListing(
        source=ListingSource.CHIENS_DE_FRANCE,
        external_id="chiot-2199888",
        breed_id=breed.id,
        kind=ListingKind.PUPPY_AD,
        lof_status=LofStatus.LOF,
        external_url=main_site_url,
    )
    site_ad = replace(main_site_ad, breeder_site_page_url=site_page_url)

    listing_ingestion_service.ingest(db, ListingSource.CHIENS_DE_FRANCE, [site_ad], set(), naive_utc_now())
    summary = listing_ingestion_service.ingest(
        db, ListingSource.CHIENS_DE_FRANCE, [main_site_ad], set(), naive_utc_now()
    )

    listing = db.query(Listing).one()
    assert (listing.external_url, listing.breeder_site_page_url) == (main_site_url, site_page_url)
    assert summary.changed_listing_ids == []


def test_a_reading_without_the_departure_day_keeps_the_day_an_earlier_reading_gave(db: Session) -> None:
    SeederRunner.run(db)
    breed = db.query(Breed).one()
    ad_without_day = RawListing(
        source=ListingSource.CHIENS_DE_FRANCE,
        external_id="chiot-1",
        breed_id=breed.id,
        kind=ListingKind.PUPPY_AD,
        lof_status=LofStatus.LOF,
        birth_date=date(2026, 11, 12),
    )
    ad_with_day = replace(ad_without_day, available_from=date(2027, 1, 23))

    listing_ingestion_service.ingest(db, ListingSource.CHIENS_DE_FRANCE, [ad_with_day], set(), naive_utc_now())
    listing_ingestion_service.ingest(db, ListingSource.CHIENS_DE_FRANCE, [ad_without_day], set(), naive_utc_now())

    assert db.query(Listing).one().available_from == date(2027, 1, 23)
