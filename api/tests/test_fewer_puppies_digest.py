"""The evening digest tells when a followed litter offers fewer puppies, at every drop (docs/04, ``availability_change``)."""

from datetime import date, datetime

import pytest
from sqlalchemy.orm import Session

from enums.follow_up_status import FollowUpStatus
from enums.listing_kind import ListingKind
from enums.listing_source import ListingSource
from enums.lof_status import LofStatus
from models.breed import Breed
from models.breeder import Breeder
from models.digest_entry import DigestEntry
from models.follow_up import FollowUp
from models.listing import Listing
from models.user import User
from seeders.run_seeders import SeederRunner
from services.litter_grouping import litter_grouping_service
from services.matching.match_refresh import match_refresh_service
from services.notifier import notifier_service
from services.push_service import PushResult, PushService

FIRST_MORNING = datetime(2026, 10, 27, 9, 0)
SECOND_MORNING = datetime(2026, 10, 28, 9, 0)
SECOND_EVENING = datetime(2026, 10, 28, 18, 0)
THIRD_MORNING = datetime(2026, 10, 29, 9, 0)
THIRD_EVENING = datetime(2026, 10, 29, 18, 0)


@pytest.fixture
def pushed_bodies(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Bodies handed to the push service, which delivers to one device without network."""
    bodies: list[str] = []

    def deliver(
        _self: PushService, _db: Session, _user_id: int, _title: str, body: str, _url: str, tag: str | None = None
    ) -> PushResult:
        """Record the push as delivered."""
        bodies.append(body)
        return PushResult(delivered=1)

    monkeypatch.setattr(PushService, "send", deliver)
    return bodies


def add_born_litter_ad(
    db: Session, external_id: str, affix: str, color: str, puppies_available: int, seen_at: datetime
) -> Listing:
    """
    Store a LOF litter ad of Ille-et-Vilaine with its breeder, as Chiots de France gives it.

    Args:
        db: Database session.
        external_id: Identifier of the ad.
        affix: Affix of the breeder, the name the cards show.
        color: Canonical colour of the litter.
        puppies_available: Puppies still offered.
        seen_at: Run that first saw it.

    Returns:
        The listing, flushed.
    """
    breeder = Breeder(affix=affix)
    db.add(breeder)
    db.flush()
    listing = Listing(
        source=ListingSource.CHIOTS_DE_FRANCE,
        external_id=external_id,
        breed_id=db.query(Breed).one().id,
        breeder_id=breeder.id,
        kind=ListingKind.LITTER_BORN,
        lof_status=LofStatus.LOF,
        birth_date=date(2026, 9, 20),
        male_count=2,
        female_count=2,
        puppies_available=puppies_available,
        colors=[{"color": color, "confidence": "certain"}],
        department_code="35",
        first_seen_at=seen_at,
        last_seen_at=seen_at,
    )
    db.add(listing)
    db.flush()
    return listing


def collect(db: Session, now: datetime, should_notify: bool = True) -> None:
    """
    Regroup, then evaluate and notify, as a collection run does once the listings are stored.

    Args:
        db: Database session.
        now: Run time.
        should_notify: Whether the events are sent.
    """
    grouping = litter_grouping_service.regroup(db, now)
    match_refresh_service.refresh(
        db,
        now,
        set(grouping.born_group_ids),
        should_notify=should_notify,
        fewer_puppies_group_ids=set(grouping.fewer_puppies_group_ids),
    )


def gold_litter_offering_four_puppies(db: Session, is_followed: bool) -> Listing:
    """
    The seeds and a preferred gold litter of four puppies, already collected once without news.

    Args:
        db: Database session.
        is_followed: Whether the seeded user follows the litter.

    Returns:
        The litter ad.
    """
    SeederRunner.run(db)
    litter_ad = add_born_litter_ad(db, "annonce-1", "De Kerlann", "gold", 4, FIRST_MORNING)
    collect(db, FIRST_MORNING, should_notify=False)
    if is_followed and litter_ad.litter_group_id is not None:
        user = db.query(User).one()
        db.add(FollowUp(user_id=user.id, litter_group_id=litter_ad.litter_group_id, status=FollowUpStatus.CONTACTED))
        db.commit()
    return litter_ad


def test_a_followed_litter_offering_fewer_puppies_is_told_in_the_evening_digest_at_every_drop(
    db: Session, pushed_bodies: list[str]
) -> None:
    litter_ad = gold_litter_offering_four_puppies(db, is_followed=True)

    litter_ad.puppies_available = 2
    collect(db, SECOND_MORNING)
    first_digest_count = notifier_service.send_due_evening_digests(db, SECOND_EVENING)
    litter_ad.puppies_available = 1
    collect(db, THIRD_MORNING)
    second_digest_count = notifier_service.send_due_evening_digests(db, THIRD_EVENING)

    assert (first_digest_count, second_digest_count) == (1, 1)
    assert pushed_bodies == [
        "Récap du soir : De Kerlann, plus que 2 chiots disponibles.",
        "Récap du soir : De Kerlann, plus qu’un chiot disponible.",
    ]
    assert db.query(DigestEntry).count() == 1


def test_the_digest_tells_the_new_acceptable_litters_then_the_followed_ones_offering_fewer_puppies(
    db: Session, pushed_bodies: list[str]
) -> None:
    litter_ad = gold_litter_offering_four_puppies(db, is_followed=True)

    litter_ad.puppies_available = 0
    add_born_litter_ad(db, "annonce-2", "Du Val d'Oust", "noir_et_feu", 3, SECOND_MORNING)
    collect(db, SECOND_MORNING)
    notifier_service.send_due_evening_digests(db, SECOND_EVENING)

    assert pushed_bodies == [
        "Récap du soir : 1 portée acceptable : une portée noir et feu (Ille-et-Vilaine)."
        " De Kerlann, plus aucun chiot disponible."
    ]


def test_a_litter_not_followed_offering_fewer_puppies_stays_out_of_the_digest(
    db: Session, pushed_bodies: list[str]
) -> None:
    litter_ad = gold_litter_offering_four_puppies(db, is_followed=False)

    litter_ad.puppies_available = 2
    collect(db, SECOND_MORNING)

    assert db.query(DigestEntry).count() == 0
    assert notifier_service.send_due_evening_digests(db, SECOND_EVENING) == 0
    assert pushed_bodies == []
