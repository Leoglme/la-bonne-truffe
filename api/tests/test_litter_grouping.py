"""LitterGroupingService on hand-made listings: puppy ads of one litter, matings dated apart, mothers."""

from datetime import date, datetime

from sqlalchemy.orm import Session

from enums.listing_kind import ListingKind
from enums.listing_source import ListingSource
from models.breed import Breed
from models.breeder import Breeder
from models.listing import Listing
from models.litter_group import LitterGroup
from seeders.run_seeders import SeederRunner
from services.litter_grouping import litter_grouping_service
from services.matching.snapshot_builder import LitterSnapshotBuilder

NOW = datetime(2026, 10, 28, 12, 0)


def add_listing(
    db: Session,
    breeder: Breeder,
    source: ListingSource,
    external_id: str,
    kind: ListingKind,
    dam_name: str | None,
    birth_date: date | None = None,
    mating_date: date | None = None,
    male_count: int | None = None,
    female_count: int | None = None,
    puppies_available: int | None = None,
    mating_number: str | None = None,
) -> Listing:
    """
    Store a listing of the cocker for a breeder.

    Args:
        db: Database session.
        breeder: Its breeder.
        source: Its source.
        external_id: Its identifier on the source.
        kind: Puppy ad, born or expected litter.
        dam_name: Name of the mother, if known.
        birth_date: Birth date, if known.
        mating_date: Mating date, if known.
        male_count: Males, if known.
        female_count: Females, if known.
        puppies_available: Puppies still offered, if the ad says.
        mating_number: Mating declaration number on the source, if given.

    Returns:
        The listing, flushed.
    """
    cocker = db.query(Breed).one()
    listing = Listing(
        source=source,
        external_id=external_id,
        breed_id=cocker.id,
        breeder_id=breeder.id,
        kind=kind,
        dam_name=dam_name,
        birth_date=birth_date,
        mating_date=mating_date,
        male_count=male_count,
        female_count=female_count,
        puppies_available=puppies_available,
        mating_number=mating_number,
        first_seen_at=NOW,
        last_seen_at=NOW,
    )
    db.add(listing)
    db.flush()
    return listing


def seeded_breeder(db: Session) -> Breeder:
    """The seeds, and one breeder."""
    SeederRunner.run(db)
    breeder = Breeder(display_name="Éleveur de test")
    db.add(breeder)
    db.flush()
    return breeder


def test_three_puppy_ads_of_one_litter_make_one_group_that_counts_its_puppies(db: Session) -> None:
    breeder = seeded_breeder(db)
    born_on = date(2026, 9, 1)
    second_male = add_listing(
        db, breeder, ListingSource.CHIENS_DE_FRANCE, "chiot-0", ListingKind.PUPPY_AD, "Mère 1", born_on, None, 1, 0
    )
    male = add_listing(
        db, breeder, ListingSource.CHIENS_DE_FRANCE, "chiot-1", ListingKind.PUPPY_AD, "Mère 1", born_on, None, 1, 0
    )
    female = add_listing(
        db, breeder, ListingSource.CHIENS_DE_FRANCE, "chiot-2", ListingKind.PUPPY_AD, "Mère 1", born_on, None, 0, 1
    )
    other_mother = add_listing(
        db, breeder, ListingSource.CHIENS_DE_FRANCE, "chiot-3", ListingKind.PUPPY_AD, "Mère 2", born_on, None, 1, 0
    )

    litter_grouping_service.regroup(db, NOW)

    assert second_male.litter_group_id == male.litter_group_id == female.litter_group_id
    assert other_mother.litter_group_id != male.litter_group_id
    group = db.get(LitterGroup, male.litter_group_id)
    assert group is not None
    snapshot = LitterSnapshotBuilder.build(db, group)
    assert snapshot is not None
    assert (snapshot.male_count, snapshot.female_count) == (2, 1)


def test_matings_dated_days_apart_by_two_sources_join_when_both_name_the_same_mother(db: Session) -> None:
    breeder = seeded_breeder(db)
    declared = add_listing(
        db,
        breeder,
        ListingSource.CENTRALE_CANINE,
        "1",
        ListingKind.LITTER_EXPECTED,
        "Vutha du Galain",
        None,
        date(2026, 9, 1),
    )
    announced = add_listing(
        db,
        breeder,
        ListingSource.CHIENS_DE_FRANCE,
        "saillie-1",
        ListingKind.LITTER_EXPECTED,
        "CH. VUTHA Du Galain Du Galain",
        None,
        date(2026, 8, 28),
    )

    litter_grouping_service.regroup(db, NOW)

    assert announced.litter_group_id == declared.litter_group_id


def test_matings_days_apart_stay_two_litters_while_a_mother_is_unknown(db: Session) -> None:
    breeder = seeded_breeder(db)
    declared = add_listing(
        db,
        breeder,
        ListingSource.CENTRALE_CANINE,
        "1",
        ListingKind.LITTER_EXPECTED,
        "Vutha du Galain",
        None,
        date(2026, 9, 1),
    )
    announced = add_listing(
        db,
        breeder,
        ListingSource.CHIENS_DE_FRANCE,
        "saillie-1",
        ListingKind.LITTER_EXPECTED,
        None,
        None,
        date(2026, 8, 28),
    )

    litter_grouping_service.regroup(db, NOW)

    assert announced.litter_group_id != declared.litter_group_id


def test_a_litter_ad_offering_fewer_puppies_is_reported_once_its_count_was_known(db: Session) -> None:
    breeder = seeded_breeder(db)
    litter_ad = add_listing(
        db,
        breeder,
        ListingSource.CHIOTS_DE_FRANCE,
        "annonce-1",
        ListingKind.LITTER_BORN,
        "Mère 1",
        date(2026, 9, 1),
        None,
        2,
        2,
        puppies_available=4,
    )

    first_regrouping = litter_grouping_service.regroup(db, NOW)
    litter_ad.puppies_available = 2
    second_regrouping = litter_grouping_service.regroup(db, NOW)
    third_regrouping = litter_grouping_service.regroup(db, NOW)

    group = db.get(LitterGroup, litter_ad.litter_group_id)
    assert group is not None
    assert group.puppies_available == 2
    assert first_regrouping.fewer_puppies_group_ids == []
    assert second_regrouping.fewer_puppies_group_ids == [group.id]
    assert third_regrouping.fewer_puppies_group_ids == []


def test_a_puppy_ad_reserved_or_gone_lowers_the_puppies_its_litter_offers(db: Session) -> None:
    breeder = seeded_breeder(db)
    puppy_ads = [
        add_listing(
            db,
            breeder,
            ListingSource.CHIENS_DE_FRANCE,
            f"chiot-{index}",
            ListingKind.PUPPY_AD,
            "Mère 1",
            date(2026, 9, 1),
            None,
            1,
            0,
            puppies_available=1,
        )
        for index in range(3)
    ]
    litter_grouping_service.regroup(db, NOW)

    puppy_ads[0].puppies_available = 0
    after_a_reservation = litter_grouping_service.regroup(db, NOW)
    puppy_ads[1].is_active = False
    after_an_ad_left = litter_grouping_service.regroup(db, NOW)

    group = db.get(LitterGroup, puppy_ads[0].litter_group_id)
    assert group is not None
    assert after_a_reservation.fewer_puppies_group_ids == after_an_ad_left.fewer_puppies_group_ids == [group.id]
    assert group.puppies_available == 1


def test_a_birth_declared_under_a_new_identifier_joins_its_mating(db: Session) -> None:
    breeder = seeded_breeder(db)
    mating = add_listing(
        db,
        breeder,
        ListingSource.CENTRALE_CANINE,
        "mating-1",
        ListingKind.LITTER_EXPECTED,
        "Mère de test",
        mating_date=date(2026, 8, 25),
        mating_number="2026032501",
    )
    litter_grouping_service.regroup(db, NOW)
    birth = add_listing(
        db,
        breeder,
        ListingSource.CENTRALE_CANINE,
        "birth-1",
        ListingKind.LITTER_BORN,
        "Mère de test",
        birth_date=date(2026, 10, 27),
        male_count=1,
        female_count=4,
        mating_number="2026032501",
    )

    result = litter_grouping_service.regroup(db, NOW)

    assert birth.litter_group_id == mating.litter_group_id
    assert result.born_group_ids == [mating.litter_group_id]


def test_two_matings_of_a_breeder_stay_apart(db: Session) -> None:
    breeder = seeded_breeder(db)
    first_mating = add_listing(
        db,
        breeder,
        ListingSource.CENTRALE_CANINE,
        "mating-1",
        ListingKind.LITTER_EXPECTED,
        "Première mère",
        mating_date=date(2026, 8, 25),
        mating_number="2026032501",
    )
    second_mating = add_listing(
        db,
        breeder,
        ListingSource.CENTRALE_CANINE,
        "mating-2",
        ListingKind.LITTER_EXPECTED,
        "Seconde mère",
        mating_date=date(2026, 8, 26),
        mating_number="2026032502",
    )

    litter_grouping_service.regroup(db, NOW)

    assert first_mating.litter_group_id != second_mating.litter_group_id
