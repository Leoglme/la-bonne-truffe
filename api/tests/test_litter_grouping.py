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
