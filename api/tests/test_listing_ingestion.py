"""ListingIngestionService: the breeder of a listing from one run to the next, and the litters too old to follow."""

from dataclasses import replace
from datetime import date, datetime, timedelta

import pytest
from sqlalchemy.orm import Session

from core.clock import naive_utc_now
from enums.coat_color import CoatColor
from enums.color_confidence import ColorConfidence
from enums.listing_kind import ListingKind
from enums.listing_source import ListingSource
from enums.lof_status import LofStatus
from models.breed import Breed
from models.breeder import Breeder
from models.listing import Listing
from models.listing_change import ListingChange
from models.litter_group import LitterGroup
from seeders.run_seeders import SeederRunner
from services import listing_ingestion
from services.collectors.breeder_contact_parser import BreederContactParser
from services.collectors.chiots_de_france import ChiotsDeFranceCollector, ListedLitterAd
from services.collectors.html_source import HtmlBreedTarget, HtmlCollectionPlan, HtmlDepartmentTarget
from services.collectors.raw_listing import ColorReading, RawBreeder, RawListing
from services.listing_ingestion import BORN_LITTER_ACTIVE_DAYS, listing_ingestion_service
from services.litter_grouping import LEGAL_HANDOVER_DAYS, litter_grouping_service
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


def test_a_mating_whose_litter_was_due_long_ago_stays_inactive_until_a_birth_is_declared(
    db: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(listing_ingestion, "UNDECLARED_LITTER_ACTIVE_DAYS", LEGAL_HANDOVER_DAYS)
    mating = replace(
        private_seller_ad(db), kind=ListingKind.LITTER_EXPECTED, birth_date=None, mating_date=date(2026, 8, 1)
    )
    due_day = datetime(2026, 10, 3, 12, 0)
    last_run_it_counts = due_day + timedelta(days=LEGAL_HANDOVER_DAYS)
    late_run = last_run_it_counts + timedelta(days=1)

    listing_ingestion_service.ingest(db, ListingSource.CHIOTS_DE_FRANCE, [mating], {"72"}, last_run_it_counts)
    was_active_while_it_could_be_to_come = db.query(Listing).one().is_active
    listing_ingestion_service.ingest(db, ListingSource.CHIOTS_DE_FRANCE, [mating], {"72"}, late_run)
    was_active_once_overdue = db.query(Listing).one().is_active
    declared_born = replace(mating, kind=ListingKind.LITTER_BORN, birth_date=date(2026, 10, 5))
    listing_ingestion_service.ingest(db, ListingSource.CHIOTS_DE_FRANCE, [declared_born], {"72"}, late_run)

    assert (was_active_while_it_could_be_to_come, was_active_once_overdue) == (True, False)
    assert db.query(Listing).one().is_active is True


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


def test_a_reading_that_says_nothing_of_the_colour_keeps_the_colours_an_earlier_one_gave(db: Session) -> None:
    ad_without_colour = replace(private_seller_ad(db), colors=(), color_text=None)
    ad_with_its_colour = replace(
        ad_without_colour,
        colors=(ColorReading(CoatColor.NOIR_ET_FEU, ColorConfidence.CERTAIN),),
        color_text="Chiots noirs feu disponibles",
    )

    listing_ingestion_service.ingest(db, ListingSource.CHIOTS_DE_FRANCE, [ad_with_its_colour], {"72"}, naive_utc_now())
    listing_ingestion_service.ingest(db, ListingSource.CHIOTS_DE_FRANCE, [ad_without_colour], {"72"}, naive_utc_now())

    listing = db.query(Listing).one()
    assert listing.colors == [{"color": "noir_et_feu", "confidence": "certain"}]
    assert listing.color_text == "Chiots noirs feu disponibles"
    assert db.query(ListingChange).filter(ListingChange.field == "colors").count() == 0


def test_an_ad_that_only_links_the_site_of_a_known_breeder_joins_that_breeder(db: Session) -> None:
    site_url = "https://elevage-a.chiens-de-france.com"
    ad_of_a_seller_known_by_its_site = replace(
        private_seller_ad(db), breeder=RawBreeder(source_id="annonce-487726", website=site_url)
    )
    known_breeder = Breeder(affix="Du Clos de test A", chiens_de_france_site_url=site_url)
    db.add(known_breeder)
    db.commit()

    listing_ingestion_service.ingest(
        db, ListingSource.CHIOTS_DE_FRANCE, [ad_of_a_seller_known_by_its_site], {"72"}, naive_utc_now()
    )

    assert db.query(Breeder).count() == 1
    assert db.query(Listing).one().breeder_id == known_breeder.id


def test_an_ad_stored_under_a_nameless_breeder_moves_to_its_real_breeder_and_leaves_its_litter(db: Session) -> None:
    site_url = "https://elevage-a.chiens-de-france.com"
    ad = replace(private_seller_ad(db), breeder=RawBreeder(source_id="annonce-487726", website=site_url))
    listing_ingestion_service.ingest(db, ListingSource.CHIOTS_DE_FRANCE, [ad], {"72"}, naive_utc_now())
    litter_grouping_service.regroup(db, naive_utc_now())
    nameless_breeder_id = db.query(Listing).one().breeder_id
    db.query(Breeder).filter(Breeder.id == nameless_breeder_id).update({"chiens_de_france_site_url": None})
    real_breeder = Breeder(affix="Du Clos de test A", chiens_de_france_site_url=site_url)
    db.add(real_breeder)
    db.commit()
    lone_group_id = db.query(Listing).one().litter_group_id

    listing_ingestion_service.ingest(db, ListingSource.CHIOTS_DE_FRANCE, [ad], {"72"}, naive_utc_now())

    listing = db.query(Listing).one()
    assert (listing.breeder_id, listing.litter_group_id) == (real_breeder.id, None)
    assert db.get(Breeder, nameless_breeder_id) is None
    lone_group = db.get(LitterGroup, lone_group_id)
    assert lone_group is not None and lone_group.breeder_id == real_breeder.id
