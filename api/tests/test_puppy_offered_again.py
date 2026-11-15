"""A puppy offered again, reserved then set free or back online, is told at once on a followed or preferred
litter (docs/04, ``available_again``)."""

from dataclasses import replace
from datetime import date, datetime, timedelta

import pytest
from sqlalchemy.orm import Session

from enums.coat_color import CoatColor
from enums.color_confidence import ColorConfidence
from enums.follow_up_status import FollowUpStatus
from enums.listing_kind import ListingKind
from enums.listing_source import ListingSource
from enums.lof_status import LofStatus
from enums.notification_kind import NotificationKind
from models.breed import Breed
from models.follow_up import FollowUp
from models.listing import Listing
from models.litter_group import LitterGroup
from models.notification import Notification
from models.user import User
from seeders.run_seeders import SeederRunner
from services.collection_runner import CollectionRunner
from services.collectors.raw_listing import ColorReading, RawBreeder, RawListing
from services.listing_ingestion import IngestionSummary, listing_ingestion_service
from services.litter_grouping import litter_grouping_service
from services.matching.match_refresh import match_refresh_service
from services.push_service import PushResult, PushService

FIRST_RUN = datetime(2026, 11, 10, 9, 20)
ONE_HOUR = timedelta(hours=1)
BREEDER = RawBreeder(source_id="elevage-a", affix="De Kerlann", zip_code="35600", city="Redon")


@pytest.fixture
def pushed_titles(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Titles handed to the push service, which delivers to one device without network."""
    titles: list[str] = []

    def deliver(
        _self: PushService, _db: Session, _user_id: int, title: str, _body: str, _url: str, tag: str | None = None
    ) -> PushResult:
        """Record the push as delivered."""
        titles.append(title)
        return PushResult(delivered=1)

    monkeypatch.setattr(PushService, "send", deliver)
    return titles


def puppy_ad(db: Session, puppy_number: int, color: CoatColor, puppies_available: int) -> RawListing:
    """
    A LOF puppy ad of Ille-et-Vilaine as the list of Chiens de France gives it.

    Args:
        db: Database session, for the seeded breed.
        puppy_number: Number of the puppy on the source.
        color: Its colour, told for sure.
        puppies_available: 1 while it is offered, 0 once reserved.

    Returns:
        The listing read.
    """
    return RawListing(
        source=ListingSource.CHIENS_DE_FRANCE,
        external_id=f"chiot-{puppy_number}",
        breed_id=db.query(Breed).one().id,
        kind=ListingKind.PUPPY_AD,
        lof_status=LofStatus.LOF,
        birth_date=date(2026, 10, 20),
        male_count=1,
        female_count=0,
        puppies_available=puppies_available,
        colors=(ColorReading(color, ColorConfidence.CERTAIN),),
        department_code="35",
        breeder=BREEDER,
    )


def collect(db: Session, ads: list[RawListing], now: datetime, should_notify: bool = True) -> IngestionSummary:
    """
    Store a reading of the list, then regroup, evaluate and notify as a collection run does.

    Args:
        db: Database session.
        ads: The ads the list shows.
        now: Run time.
        should_notify: Whether the events are sent.

    Returns:
        The summary of the ingestion.
    """
    summary = listing_ingestion_service.ingest(db, ListingSource.CHIENS_DE_FRANCE, ads, {"35"}, now)
    grouping = litter_grouping_service.regroup(db, now)
    match_refresh_service.refresh(
        db,
        now,
        set(grouping.born_group_ids),
        should_notify=should_notify,
        fewer_puppies_group_ids=set(grouping.fewer_puppies_group_ids),
        puppy_offered_again_group_ids=CollectionRunner._groups_of(db, summary.offered_again_listing_ids),
    )
    return summary


def follow_the_litter(db: Session) -> None:
    """Put the only litter of the database in the follow-ups of the seeded user."""
    litter_group_id = db.query(LitterGroup).one().id
    db.add(FollowUp(user_id=db.query(User).one().id, litter_group_id=litter_group_id, status=FollowUpStatus.CONTACTED))
    db.commit()


def test_a_reserved_puppy_set_free_or_an_ad_back_online_is_offered_again_and_a_first_reading_is_not(
    db: Session,
) -> None:
    SeederRunner.run(db)
    offered = puppy_ad(db, 1, CoatColor.GOLD, 1)
    reserved = puppy_ad(db, 2, CoatColor.GOLD, 0)

    first = listing_ingestion_service.ingest(db, ListingSource.CHIENS_DE_FRANCE, [offered, reserved], {"35"}, FIRST_RUN)
    unchanged = listing_ingestion_service.ingest(
        db, ListingSource.CHIENS_DE_FRANCE, [offered, reserved], {"35"}, FIRST_RUN + ONE_HOUR
    )
    set_free = listing_ingestion_service.ingest(
        db, ListingSource.CHIENS_DE_FRANCE, [replace(reserved, puppies_available=1)], {"35"}, FIRST_RUN + 2 * ONE_HOUR
    )
    listing_ingestion_service.ingest(db, ListingSource.CHIENS_DE_FRANCE, [], {"35"}, FIRST_RUN + 3 * ONE_HOUR)
    back_online = listing_ingestion_service.ingest(
        db, ListingSource.CHIENS_DE_FRANCE, [offered], {"35"}, FIRST_RUN + 4 * ONE_HOUR
    )

    first_puppy = db.query(Listing).filter(Listing.external_id == "chiot-1").one()
    second_puppy = db.query(Listing).filter(Listing.external_id == "chiot-2").one()
    assert (first.offered_again_listing_ids, unchanged.offered_again_listing_ids) == ([], [])
    assert set_free.offered_again_listing_ids == [second_puppy.id]
    assert back_online.offered_again_listing_ids == [first_puppy.id]


def test_a_puppy_set_free_on_a_followed_litter_is_pushed_at_once_each_time(
    db: Session, pushed_titles: list[str]
) -> None:
    SeederRunner.run(db)
    offered = puppy_ad(db, 1, CoatColor.BLEU_ROUAN, 1)
    reserved = puppy_ad(db, 2, CoatColor.BLEU_ROUAN, 0)
    collect(db, [offered, reserved], FIRST_RUN, should_notify=False)
    follow_the_litter(db)

    collect(db, [offered, replace(reserved, puppies_available=1)], FIRST_RUN + ONE_HOUR)
    collect(db, [offered, reserved], FIRST_RUN + 2 * ONE_HOUR)
    collect(db, [offered, replace(reserved, puppies_available=1)], FIRST_RUN + 3 * ONE_HOUR)

    assert pushed_titles == [
        "Un chiot se libère · De Kerlann",
        "Plus qu’un chiot · De Kerlann",
        "Un chiot se libère · De Kerlann",
    ]
    set_free = db.query(Notification).filter(Notification.kind == NotificationKind.AVAILABLE_AGAIN).first()
    assert set_free is not None
    assert set_free.body == (
        "Un chiot de la portée née le 20 octobre (Ille-et-Vilaine) est de nouveau disponible : 2 chiots à réserver, "
        "appelle vite."
    )


def test_a_puppy_set_free_on_a_preferred_litter_nobody_follows_is_pushed_and_on_an_ignored_one_is_not(
    db: Session, pushed_titles: list[str]
) -> None:
    SeederRunner.run(db)
    gold_reserved = puppy_ad(db, 1, CoatColor.GOLD, 0)
    roan_reserved = replace(
        puppy_ad(db, 2, CoatColor.BLEU_ROUAN, 0),
        birth_date=date(2026, 9, 1),
        breeder=RawBreeder(source_id="elevage-b", affix="Du Val d'Oust", zip_code="35000", city="Rennes"),
    )
    collect(db, [gold_reserved, roan_reserved], FIRST_RUN, should_notify=False)

    collect(
        db,
        [replace(gold_reserved, puppies_available=1), replace(roan_reserved, puppies_available=1)],
        FIRST_RUN + timedelta(days=5),
    )

    assert pushed_titles == ["Un chiot se libère · De Kerlann"]


def test_a_litter_told_as_preferred_for_the_first_time_is_not_told_again_for_its_puppy_set_free(
    db: Session, pushed_titles: list[str]
) -> None:
    SeederRunner.run(db)
    gold_reserved = puppy_ad(db, 1, CoatColor.GOLD, 0)
    collect(db, [gold_reserved], FIRST_RUN, should_notify=False)

    collect(db, [replace(gold_reserved, puppies_available=1)], FIRST_RUN + ONE_HOUR)

    assert pushed_titles == ["Portée préférée · De Kerlann"]
