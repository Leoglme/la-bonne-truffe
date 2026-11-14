"""LitterGroupingService on hand-made listings: puppy ads of one litter, matings dated apart, mothers."""

from datetime import date

from sqlalchemy.orm import Session

from enums.listing_kind import ListingKind
from enums.listing_source import ListingSource
from models.listing import Listing
from models.litter_group import LitterGroup
from services.litter_grouping import litter_grouping_service
from services.matching.snapshot_builder import LitterSnapshotBuilder
from tests.hand_made_listings import NOW, add_listing, seeded_breeder


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


def test_reserved_puppy_ads_no_longer_count_among_the_puppies(db: Session) -> None:
    breeder = seeded_breeder(db)
    born_on = date(2026, 9, 1)
    for_sale = add_listing(
        db, breeder, ListingSource.CHIENS_DE_FRANCE, "chiot-1", ListingKind.PUPPY_AD, "Mère 1", born_on, None, 1, 0, 1
    )
    add_listing(
        db, breeder, ListingSource.CHIENS_DE_FRANCE, "chiot-2", ListingKind.PUPPY_AD, "Mère 1", born_on, None, 0, 1, 0
    )
    add_listing(
        db, breeder, ListingSource.CHIENS_DE_FRANCE, "chiot-3", ListingKind.PUPPY_AD, "Mère 1", born_on, None, 0, 1, 0
    )

    litter_grouping_service.regroup(db, NOW)
    group = db.get(LitterGroup, for_sale.litter_group_id)
    assert group is not None
    offered = LitterSnapshotBuilder.build(db, group)
    for_sale.puppies_available = 0
    litter_grouping_service.regroup(db, NOW)
    all_gone = LitterSnapshotBuilder.build(db, group)

    assert offered is not None and all_gone is not None
    assert (offered.male_count, offered.female_count, offered.puppies_available) == (1, 0, 1)
    assert (all_gone.male_count, all_gone.female_count, all_gone.puppies_available) == (0, 0, 0)


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


def test_puppy_ads_born_the_very_day_of_a_single_litter_join_it_whatever_mother_they_name(db: Session) -> None:
    breeder = seeded_breeder(db)
    born_on = date(2026, 8, 9)
    declared = add_listing(
        db, breeder, ListingSource.CENTRALE_CANINE, "1", ListingKind.LITTER_BORN, "Saphir", born_on, None, 4, 2
    )
    add_listing(
        db, breeder, ListingSource.CENTRALE_CANINE, "2", ListingKind.LITTER_BORN, "Tacita", date(2026, 8, 4), None, 5, 4
    )
    expected = add_listing(
        db,
        breeder,
        ListingSource.CENTRALE_CANINE,
        "3",
        ListingKind.LITTER_EXPECTED,
        "Sentiment",
        None,
        date(2026, 6, 19),
    )
    litter_grouping_service.regroup(db, NOW)
    male = add_listing(
        db, breeder, ListingSource.CHIENS_DE_FRANCE, "chiot-1", ListingKind.PUPPY_AD, "Sentiment", born_on, None, 1, 0
    )
    female = add_listing(
        db, breeder, ListingSource.CHIENS_DE_FRANCE, "chiot-2", ListingKind.PUPPY_AD, "Sentiment", born_on, None, 0, 1
    )

    litter_grouping_service.regroup(db, NOW)

    assert {male.litter_group_id, female.litter_group_id} == {declared.litter_group_id}
    assert expected.litter_group_id != declared.litter_group_id
    group = db.get(LitterGroup, declared.litter_group_id)
    assert group is not None and group.is_grouping_probable


def test_an_ad_naming_another_mother_stays_apart_from_two_litters_born_its_day(db: Session) -> None:
    breeder = seeded_breeder(db)
    born_on = date(2026, 8, 9)
    first = add_listing(db, breeder, ListingSource.CENTRALE_CANINE, "1", ListingKind.LITTER_BORN, "Mère 1", born_on)
    second = add_listing(db, breeder, ListingSource.CENTRALE_CANINE, "2", ListingKind.LITTER_BORN, "Mère 2", born_on)
    litter_grouping_service.regroup(db, NOW)
    puppy_ad = add_listing(
        db, breeder, ListingSource.CHIENS_DE_FRANCE, "chiot-1", ListingKind.PUPPY_AD, "Mère 3", born_on, None, 1, 0
    )

    litter_grouping_service.regroup(db, NOW)

    assert puppy_ad.litter_group_id not in {first.litter_group_id, second.litter_group_id}


def test_a_litter_holding_ads_of_another_mother_on_the_same_source_is_another_litter(db: Session) -> None:
    breeder = seeded_breeder(db)
    born_on = date(2026, 8, 9)
    declared = add_listing(db, breeder, ListingSource.CENTRALE_CANINE, "1", ListingKind.LITTER_BORN, "Mère 1", born_on)
    litter_grouping_service.regroup(db, NOW)
    first_litter_ad = add_listing(
        db, breeder, ListingSource.CHIENS_DE_FRANCE, "chiot-1", ListingKind.PUPPY_AD, "Mère 1", born_on, None, 1, 0
    )
    litter_grouping_service.regroup(db, NOW)
    second_litter_ad = add_listing(
        db, breeder, ListingSource.CHIENS_DE_FRANCE, "chiot-2", ListingKind.PUPPY_AD, "Mère 2", born_on, None, 0, 1
    )

    litter_grouping_service.regroup(db, NOW)

    assert first_litter_ad.litter_group_id == declared.litter_group_id
    assert second_litter_ad.litter_group_id != declared.litter_group_id


def test_puppy_ads_born_near_the_birth_a_declared_mating_announces_join_it_and_make_it_born(db: Session) -> None:
    breeder = seeded_breeder(db)
    declared = add_listing(
        db, breeder, ListingSource.CENTRALE_CANINE, "1", ListingKind.LITTER_EXPECTED, "Tropik", None, date(2026, 8, 17)
    )
    litter_grouping_service.regroup(db, NOW)
    puppy_ad = add_listing(
        db,
        breeder,
        ListingSource.CHIENS_DE_FRANCE,
        "chiot-1",
        ListingKind.PUPPY_AD,
        "Tropik Des Vents D'Océan",
        date(2026, 10, 21),
        None,
        1,
        0,
    )

    result = litter_grouping_service.regroup(db, NOW)

    assert puppy_ad.litter_group_id == declared.litter_group_id
    assert result.born_group_ids == [declared.litter_group_id]
    group = db.get(LitterGroup, declared.litter_group_id)
    assert group is not None and group.birth_date == date(2026, 10, 21)


def test_a_puppy_ad_born_months_after_the_birth_a_mating_announces_is_another_litter(db: Session) -> None:
    breeder = seeded_breeder(db)
    declared = add_listing(
        db, breeder, ListingSource.CENTRALE_CANINE, "1", ListingKind.LITTER_EXPECTED, "Tropik", None, date(2026, 3, 2)
    )
    litter_grouping_service.regroup(db, NOW)
    puppy_ad = add_listing(
        db, breeder, ListingSource.CHIENS_DE_FRANCE, "chiot-1", ListingKind.PUPPY_AD, "Tropik", date(2026, 10, 21)
    )

    litter_grouping_service.regroup(db, NOW)

    assert puppy_ad.litter_group_id != declared.litter_group_id


def departure_day_after_regrouping(db: Session, listing: Listing) -> date | None:
    """
    Regroup the listings, then give the day the litter of a listing may leave.

    Args:
        db: Database session.
        listing: A listing of the litter.

    Returns:
        The departure day of its group.
    """
    litter_grouping_service.regroup(db, NOW)
    group = db.get(LitterGroup, listing.litter_group_id)
    assert group is not None
    return group.available_from


def test_a_litter_leaves_the_day_its_ads_announce_rather_than_at_the_legal_age(db: Session) -> None:
    breeder = seeded_breeder(db)
    born_on = date(2026, 11, 12)
    declared = add_listing(db, breeder, ListingSource.CENTRALE_CANINE, "1", ListingKind.LITTER_BORN, "Mère 1", born_on)

    assert departure_day_after_regrouping(db, declared) == date(2027, 1, 7)

    add_listing(
        db,
        breeder,
        ListingSource.CHIENS_DE_FRANCE,
        "chiot-1",
        ListingKind.PUPPY_AD,
        "Mère 1",
        born_on,
        available_from=date(2027, 1, 23),
    )

    assert departure_day_after_regrouping(db, declared) == date(2027, 1, 23)


def test_a_day_announced_before_the_legal_age_gives_way_to_the_legal_age(db: Session) -> None:
    breeder = seeded_breeder(db)
    puppy_ad = add_listing(
        db,
        breeder,
        ListingSource.CHIENS_DE_FRANCE,
        "chiot-1",
        ListingKind.PUPPY_AD,
        "Mère 1",
        date(2026, 11, 12),
        available_from=date(2026, 12, 20),
    )

    assert departure_day_after_regrouping(db, puppy_ad) == date(2027, 1, 7)


def test_the_day_of_an_ad_gone_offline_gives_way_to_the_day_the_ads_still_online_announce(db: Session) -> None:
    breeder = seeded_breeder(db)
    born_on = date(2026, 11, 12)
    sold_puppy_ad = add_listing(
        db,
        breeder,
        ListingSource.CHIENS_DE_FRANCE,
        "chiot-1",
        ListingKind.PUPPY_AD,
        "Mère 1",
        born_on,
        available_from=date(2027, 1, 23),
    )
    sold_puppy_ad.is_active = False
    add_listing(
        db,
        breeder,
        ListingSource.CHIENS_DE_FRANCE,
        "chiot-2",
        ListingKind.PUPPY_AD,
        "Mère 1",
        born_on,
        available_from=date(2027, 1, 30),
    )

    assert departure_day_after_regrouping(db, sold_puppy_ad) == date(2027, 1, 30)
