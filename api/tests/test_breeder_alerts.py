"""Alerts on the followed breeders: a mating or a birth pushed once, never twice, the reminders and the digest."""

from datetime import UTC, date, datetime, timedelta
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from core.clock import naive_utc_now, naive_utc_of_french_time
from enums.breeder_event_kind import BreederEventKind
from enums.notification_kind import NotificationKind
from models.breeder import Breeder
from models.breeder_follow import BreederFollow, BreederFollowEvent
from models.listing import Listing
from models.notification import Notification
from models.user import User
from seeders.run_seeders import SeederRunner
from services.auth_service import AuthService
from services.collection_runner import collection_runner
from services.notifier import notifier_service
from services.push_service import PushResult, PushService
from tests.centrale_canine_pages import (
    collector_serving,
    load_recorded_pages,
    mark_published_an_hour_ago,
    remove_litter,
)

BREEDERS_URL = "/api/v1/breeders"

# Élevage A (266172): nine litters, among them a mating not born yet.
FIRST_BREEDER_OLD_LITTER_ID = "4163707"
FIRST_BREEDER_BORN_LITTER_ID = "4320820"
FIRST_BREEDER_EXPECTED_LITTER_ID = "4337070"

# Élevage D (74617): the gold litters, pushed for themselves.
GOLD_BREEDER_OLD_LITTER_ID = "4298826"
GOLD_BREEDER_BORN_LITTER_ID = "4333817"


@pytest.fixture
def pushed(monkeypatch: pytest.MonkeyPatch) -> list[tuple[str, str]]:
    """Titles and bodies handed to the push service, which delivers to one device without network."""
    pushes: list[tuple[str, str]] = []

    def deliver(
        _self: PushService, _db: Session, _user_id: int, title: str, body: str, _url: str, tag: str | None = None
    ) -> PushResult:
        """Record the push as delivered."""
        pushes.append((title, body))
        return PushResult(delivered=1)

    monkeypatch.setattr(PushService, "send", deliver)
    return pushes


@pytest.fixture
def headers(db: Session, pushed: list[tuple[str, str]]) -> dict[str, str]:
    """Seed and return the bearer header of the user."""
    SeederRunner.run(db)
    user = db.query(User).one()
    return {"Authorization": f"Bearer {AuthService.create_access_token(user.email)}"}


def first_run_without(db: Session, *litter_ids: str) -> None:
    """The first run, silent, on the recorded pages without the given litters."""
    pages = load_recorded_pages()
    for litter_id in litter_ids:
        remove_litter(pages, litter_id)
    collection_runner.run_centrale_canine(db, collector_serving(pages))


def next_run_with_fresh(db: Session, *litter_ids: str) -> None:
    """A later run on every recorded page, the given litters just published."""
    pages = load_recorded_pages()
    for litter_id in litter_ids:
        mark_published_an_hour_ago(pages, litter_id)
    collection_runner.run_centrale_canine(db, collector_serving(pages))


def breeder_of_litter(db: Session, external_id: str) -> Breeder:
    """The breeder of a recorded litter, as stored."""
    listing = db.query(Listing).filter(Listing.external_id == external_id).one()
    assert listing.breeder_id is not None
    breeder = db.get(Breeder, listing.breeder_id)
    assert breeder is not None
    return breeder


def follow(client: TestClient, headers: dict[str, str], breeder_id: int, **settings: Any) -> dict[str, Any]:
    """Follow a breeder as the app does, with the given settings over the defaults."""
    response = client.put(f"{BREEDERS_URL}/{breeder_id}/follow", json=settings, headers=headers)
    assert response.status_code == 200
    return dict(response.json())


def name_of(breeder: Breeder) -> str:
    """The breeder as the pushes name it."""
    return breeder.affix or breeder.display_name or ""


def events(db: Session) -> list[tuple[BreederEventKind, bool]]:
    """Every breeder event recorded, with whether it is settled."""
    return [
        (event.kind, event.sent_at is not None)
        for event in db.query(BreederFollowEvent).order_by(BreederFollowEvent.id)
    ]


def test_a_birth_at_a_followed_breeder_is_pushed_once(
    client: TestClient, db: Session, headers: dict[str, str], pushed: list[tuple[str, str]]
) -> None:
    first_run_without(db, FIRST_BREEDER_BORN_LITTER_ID)
    breeder = breeder_of_litter(db, FIRST_BREEDER_OLD_LITTER_ID)
    follow(client, headers, breeder.id)

    next_run_with_fresh(db, FIRST_BREEDER_BORN_LITTER_ID)
    next_run_with_fresh(db, FIRST_BREEDER_BORN_LITTER_ID)

    births = db.query(Notification).filter(Notification.kind == NotificationKind.BREEDER_BIRTH).all()
    assert [birth.title for birth in births] == [f"Portée née · {name_of(breeder)}"]
    assert [title for title, _body in pushed if title.startswith("Portée née")] == [births[0].title]
    assert events(db) == [(BreederEventKind.BIRTH, True)]


def test_a_mating_at_a_followed_breeder_is_pushed(
    client: TestClient, db: Session, headers: dict[str, str], pushed: list[tuple[str, str]]
) -> None:
    first_run_without(db, FIRST_BREEDER_EXPECTED_LITTER_ID)
    breeder = breeder_of_litter(db, FIRST_BREEDER_OLD_LITTER_ID)
    follow(client, headers, breeder.id)

    next_run_with_fresh(db, FIRST_BREEDER_EXPECTED_LITTER_ID)

    matings = db.query(Notification).filter(Notification.kind == NotificationKind.BREEDER_NEW_MATING).all()
    assert [mating.title for mating in matings] == [f"Saillie déclarée · {name_of(breeder)}"]
    assert events(db) == [(BreederEventKind.NEW_MATING, True)]


def test_a_litter_pushed_for_itself_is_not_pushed_again_for_its_breeder(
    client: TestClient, db: Session, headers: dict[str, str], pushed: list[tuple[str, str]]
) -> None:
    first_run_without(db, GOLD_BREEDER_BORN_LITTER_ID)
    breeder = breeder_of_litter(db, GOLD_BREEDER_OLD_LITTER_ID)
    follow(client, headers, breeder.id)

    next_run_with_fresh(db, GOLD_BREEDER_BORN_LITTER_ID)

    kinds = [notification.kind for notification in db.query(Notification).order_by(Notification.id)]
    assert NotificationKind.NEW_PREFERRED in kinds
    assert NotificationKind.BREEDER_BIRTH not in kinds
    assert events(db) == [(BreederEventKind.BIRTH, True)]


def test_an_event_turned_off_is_settled_and_never_comes_back(
    client: TestClient, db: Session, headers: dict[str, str], pushed: list[tuple[str, str]]
) -> None:
    first_run_without(db, FIRST_BREEDER_BORN_LITTER_ID)
    breeder = breeder_of_litter(db, FIRST_BREEDER_OLD_LITTER_ID)
    follow(client, headers, breeder.id, notify_birth=False)

    next_run_with_fresh(db, FIRST_BREEDER_BORN_LITTER_ID)
    follow(client, headers, breeder.id, notify_birth=True)
    next_run_with_fresh(db, FIRST_BREEDER_BORN_LITTER_ID)

    assert db.query(Notification).filter(Notification.kind == NotificationKind.BREEDER_BIRTH).count() == 0
    assert events(db) == [(BreederEventKind.BIRTH, True)]


def test_a_due_reminder_on_a_breeder_is_pushed_once(
    client: TestClient, db: Session, headers: dict[str, str], pushed: list[tuple[str, str]]
) -> None:
    first_run_without(db)
    breeder = breeder_of_litter(db, FIRST_BREEDER_OLD_LITTER_ID)
    reminder = (datetime.now(UTC) - timedelta(minutes=1)).isoformat()
    follow(client, headers, breeder.id, status="to_contact", next_reminder_at=reminder)

    first_count = notifier_service.send_due_breeder_follow_reminders(db, naive_utc_now())
    second_count = notifier_service.send_due_breeder_follow_reminders(db, naive_utc_now())

    reminder_push = db.query(Notification).filter(Notification.kind == NotificationKind.BREEDER_FOLLOW_REMINDER).one()
    assert (first_count, second_count) == (1, 0)
    assert reminder_push.title == f"Rappel · appeler {name_of(breeder)}"
    assert reminder_push.url == f"/eleveurs/{breeder.id}"
    assert db.query(BreederFollow).one().reminder_sent_at is not None


def test_new_photos_at_a_followed_breeder_are_told_in_the_evening_digest(
    client: TestClient, db: Session, headers: dict[str, str], pushed: list[tuple[str, str]]
) -> None:
    first_run_without(db)
    breeder = breeder_of_litter(db, FIRST_BREEDER_OLD_LITTER_ID)
    follow(client, headers, breeder.id)
    listing = db.query(Listing).filter(Listing.external_id == FIRST_BREEDER_OLD_LITTER_ID).one()
    db.add(
        BreederFollowEvent(
            follow_id=db.query(BreederFollow).one().id,
            litter_group_id=listing.litter_group_id,
            kind=BreederEventKind.NEW_PHOTOS,
            created_at=datetime(2026, 12, 1, 8, 0),
            sent_at=None,
        )
    )
    db.commit()

    digest_count = notifier_service.send_due_evening_digests(db, naive_utc_of_french_time(date(2026, 12, 1), 20))
    again_count = notifier_service.send_due_evening_digests(db, naive_utc_of_french_time(date(2026, 12, 2), 20))

    digest = db.query(Notification).filter(Notification.kind == NotificationKind.EVENING_DIGEST).one()
    assert (digest_count, again_count) == (1, 0)
    assert f"{name_of(breeder)} a ajouté des photos à la portée" in digest.body
    assert events(db) == [(BreederEventKind.NEW_PHOTOS, True)]
