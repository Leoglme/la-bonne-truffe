"""SplitLitterMerger on hand-made groups: a litter left in two groups, a group left under a former breeder."""

from datetime import date

from sqlalchemy.orm import Session

from enums.listing_kind import ListingKind
from enums.listing_source import ListingSource
from enums.match_tier import MatchTier
from models.breeder import Breeder
from models.follow_up import FollowUp
from models.listing import Listing
from models.listing_match import ListingMatch
from models.litter_group import LitterGroup
from models.search_profile import SearchProfile
from models.user import User
from services.litter_grouping import litter_grouping_service
from services.split_litter_merger import split_litter_merger
from tests.hand_made_listings import NOW, add_listing, seeded_breeder

BORN_ON = date(2026, 10, 28)
MATED_ON = date(2026, 8, 26)
DAM = "Tahiti Robyroc du Domaine de la Pruneraie"


def in_a_group_of_its_own(db: Session, listing: Listing) -> LitterGroup:
    """
    Put a listing alone in a new group, as an earlier run that could not place it did.

    Args:
        db: Database session.
        listing: The listing, not grouped yet.

    Returns:
        Its group, flushed.
    """
    group = LitterGroup(breed_id=listing.breed_id, breeder_id=listing.breeder_id)
    db.add(group)
    db.flush()
    listing.litter_group_id = group.id
    db.flush()
    return group


def test_a_mating_kept_apart_from_its_born_litter_joins_it(db: Session) -> None:
    breeder = seeded_breeder(db)
    declared_birth = add_listing(
        db, breeder, ListingSource.CENTRALE_CANINE, "4174001", ListingKind.LITTER_BORN, DAM, BORN_ON
    )
    mating_on_the_site = add_listing(
        db,
        breeder,
        ListingSource.CHIENS_DE_FRANCE,
        "saillie-496471",
        ListingKind.LITTER_EXPECTED,
        "Tahiti Du Domaine De La Pruneraie",
        mating_date=MATED_ON,
    )
    born_group = in_a_group_of_its_own(db, declared_birth)
    mating_group = in_a_group_of_its_own(db, mating_on_the_site)

    removed_group_ids = split_litter_merger.merge(db)

    assert removed_group_ids == [mating_group.id]
    assert mating_on_the_site.litter_group_id == declared_birth.litter_group_id == born_group.id
    assert db.get(LitterGroup, mating_group.id) is None


def test_the_followed_group_is_the_one_kept_and_what_was_notified_is_not_sent_again(db: Session) -> None:
    breeder = seeded_breeder(db)
    user = User(name="Compte de test", email="suivi@example.test", hashed_password="x")
    db.add(user)
    db.flush()
    profile = SearchProfile(user_id=user.id, name="Profil de test")
    db.add(profile)
    db.flush()
    declared_birth = add_listing(
        db, breeder, ListingSource.CENTRALE_CANINE, "4174001", ListingKind.LITTER_BORN, DAM, BORN_ON
    )
    puppy_ad = add_listing(db, breeder, ListingSource.CHIENS_DE_FRANCE, "chiot-1", ListingKind.PUPPY_AD, None, BORN_ON)
    older_group = in_a_group_of_its_own(db, declared_birth)
    followed_group = in_a_group_of_its_own(db, puppy_ad)
    db.add(FollowUp(user_id=user.id, litter_group_id=followed_group.id))
    db.add_all(
        [
            ListingMatch(
                litter_group_id=older_group.id,
                profile_id=profile.id,
                tier=MatchTier.PREFERRED,
                notified_events={"new_preferred": "2026-10-29T08:00:00"},
            ),
            ListingMatch(
                litter_group_id=followed_group.id,
                profile_id=profile.id,
                tier=MatchTier.ACCEPTABLE,
                notified_events={"born": "2026-10-30T08:00:00"},
            ),
        ]
    )
    db.flush()

    removed_group_ids = split_litter_merger.merge(db)

    assert removed_group_ids == [older_group.id]
    assert declared_birth.litter_group_id == followed_group.id
    kept_match = db.query(ListingMatch).one()
    assert kept_match.litter_group_id == followed_group.id
    assert set(kept_match.notified_events) == {"new_preferred", "born"}


def test_two_litters_declared_apart_by_one_source_stay_apart(db: Session) -> None:
    breeder = seeded_breeder(db)
    first_litter = add_listing(
        db, breeder, ListingSource.CENTRALE_CANINE, "4174001", ListingKind.LITTER_BORN, None, BORN_ON
    )
    second_litter = add_listing(
        db, breeder, ListingSource.CENTRALE_CANINE, "4174002", ListingKind.LITTER_BORN, None, date(2026, 10, 30)
    )
    ad_of_the_second = add_listing(
        db, breeder, ListingSource.CHIENS_DE_FRANCE, "chiot-1", ListingKind.PUPPY_AD, None, date(2026, 10, 30)
    )
    first_litter.litter_number, second_litter.litter_number = "LOF-1", "LOF-2"
    first_group = in_a_group_of_its_own(db, first_litter)
    second_group = in_a_group_of_its_own(db, second_litter)
    ad_of_the_second.litter_group_id = first_group.id
    db.flush()

    removed_group_ids = split_litter_merger.merge(db)

    assert removed_group_ids == []
    assert (first_litter.litter_group_id, second_litter.litter_group_id) == (first_group.id, second_group.id)


def test_an_ad_that_fits_two_litters_of_its_breeder_joins_neither(db: Session) -> None:
    breeder = seeded_breeder(db)
    first_litter = add_listing(
        db, breeder, ListingSource.CENTRALE_CANINE, "4174001", ListingKind.LITTER_BORN, "Mère 1", BORN_ON
    )
    second_litter = add_listing(
        db, breeder, ListingSource.CENTRALE_CANINE, "4174002", ListingKind.LITTER_BORN, "Mère 2", date(2026, 10, 30)
    )
    ad_naming_no_mother = add_listing(
        db, breeder, ListingSource.COEUR_DE_COCKER, "annonce-1", ListingKind.PUPPY_AD, None, date(2026, 10, 29)
    )
    for listing in (first_litter, second_litter, ad_naming_no_mother):
        in_a_group_of_its_own(db, listing)

    assert split_litter_merger.merge(db) == []


def test_a_group_left_under_a_former_breeder_goes_to_the_breeder_of_its_listings(db: Session) -> None:
    real_breeder = seeded_breeder(db)
    real_breeder.scc_breeder_id = "12345"
    breeder_made_for_an_ad = Breeder(display_name="Elevage de test")
    db.add(breeder_made_for_an_ad)
    db.flush()
    declared_birth = add_listing(
        db, real_breeder, ListingSource.CENTRALE_CANINE, "4174001", ListingKind.LITTER_BORN, DAM, BORN_ON
    )
    ad = add_listing(db, real_breeder, ListingSource.COEUR_DE_COCKER, "annonce-1", ListingKind.PUPPY_AD, None, BORN_ON)
    born_group = in_a_group_of_its_own(db, declared_birth)
    group_of_the_ad = in_a_group_of_its_own(db, ad)
    group_of_the_ad.breeder_id = breeder_made_for_an_ad.id
    former_breeder_id = breeder_made_for_an_ad.id
    db.flush()

    removed_group_ids = split_litter_merger.merge(db)

    assert removed_group_ids == [group_of_the_ad.id]
    assert ad.litter_group_id == born_group.id
    assert db.query(Breeder).filter(Breeder.id == former_breeder_id).one_or_none() is None
    assert db.get(Breeder, real_breeder.id) is not None


def test_the_puppy_ads_of_one_litter_each_left_in_a_group_all_join_the_declared_litter(db: Session) -> None:
    breeder = seeded_breeder(db)
    declared_birth = add_listing(
        db, breeder, ListingSource.CENTRALE_CANINE, "4174001", ListingKind.LITTER_BORN, DAM, BORN_ON
    )
    ads = [
        add_listing(db, breeder, ListingSource.COEUR_DE_COCKER, f"annonce-{rank}", ListingKind.PUPPY_AD, None, BORN_ON)
        for rank in range(4)
    ]
    born_group = in_a_group_of_its_own(db, declared_birth)
    groups_of_the_ads = [in_a_group_of_its_own(db, ad) for ad in ads]

    removed_group_ids = split_litter_merger.merge(db)

    assert removed_group_ids == [group.id for group in groups_of_the_ads]
    assert {ad.litter_group_id for ad in ads} == {born_group.id}
    assert db.query(LitterGroup).count() == 1


def test_a_database_grouped_by_the_rules_has_nothing_to_join(db: Session) -> None:
    breeder = seeded_breeder(db)
    add_listing(db, breeder, ListingSource.CENTRALE_CANINE, "4174001", ListingKind.LITTER_BORN, "Mère 1", BORN_ON)
    add_listing(db, breeder, ListingSource.CHIENS_DE_FRANCE, "chiot-1", ListingKind.PUPPY_AD, "Mère 1", BORN_ON)
    add_listing(db, breeder, ListingSource.CHIENS_DE_FRANCE, "chiot-2", ListingKind.PUPPY_AD, "Mère 2", BORN_ON)
    add_listing(
        db, breeder, ListingSource.CENTRALE_CANINE, "4174002", ListingKind.LITTER_EXPECTED, "Mère 3", None, MATED_ON
    )
    litter_grouping_service.regroup(db, NOW)
    groups_before = db.query(LitterGroup).count()

    assert split_litter_merger.merge(db) == []
    assert db.query(LitterGroup).count() == groups_before
