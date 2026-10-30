"""Follow-up reminders: pushed once when their time comes, again when moved, never for a dismissed or a gone litter."""

from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from core.clock import naive_utc_now
from enums.notification_kind import NotificationKind
from models.listing import Listing
from models.litter_group import LitterGroup
from models.notification import Notification
from models.user import User
from seeders.run_seeders import SeederRunner
from services.auth_service import AuthService
from services.collection_runner import collection_runner
from services.notifier import notifier_service
from services.push_service import PushResult, PushService
from tests.centrale_canine_pages import collector_serving, load_recorded_pages


@pytest.fixture
def collected(db: Session, monkeypatch: pytest.MonkeyPatch) -> dict[str, str]:
    """Seed, collect the recorded pages once (pushes stubbed), and return the bearer header of the user."""
    monkeypatch.setattr(PushService, "send", lambda *_args, **_kwargs: PushResult(delivered=1))
    SeederRunner.run(db)
    collection_runner.run_centrale_canine(db, collector_serving(load_recorded_pages()))
    user = db.query(User).one()
    return {"Authorization": f"Bearer {AuthService.create_access_token(user.email)}"}


def any_litter_id(db: Session) -> int:
    """A litter group of the recorded pages."""
    listing = db.query(Listing).filter(Listing.litter_group_id.is_not(None)).first()
    assert listing is not None
    assert listing.litter_group_id is not None
    return listing.litter_group_id


def set_reminder(
    client: TestClient, headers: dict[str, str], litter_id: int, status: str, minutes_from_now: int
) -> None:
    """Follow the litter with a reminder some minutes from now, as the dashboard sends it."""
    reminder = (datetime.now(UTC) + timedelta(minutes=minutes_from_now)).isoformat()
    client.put(
        f"/api/v1/litters/{litter_id}/follow-up",
        json={"status": status, "next_reminder_at": reminder},
        headers=headers,
    )


def test_a_due_reminder_is_pushed_once(client: TestClient, collected: dict[str, str], db: Session) -> None:
    litter_id = any_litter_id(db)
    set_reminder(client, collected, litter_id, "to_contact", minutes_from_now=-1)

    first_count = notifier_service.send_due_follow_up_reminders(db, naive_utc_now())
    second_count = notifier_service.send_due_follow_up_reminders(db, naive_utc_now())
    reminder = db.query(Notification).filter(Notification.kind == NotificationKind.FOLLOW_UP_REMINDER).one()

    assert (first_count, second_count) == (1, 0)
    assert reminder.body.startswith("C’est l’heure d’appeler ")
    assert reminder.url == f"/portees/{litter_id}"


def test_a_future_reminder_waits(client: TestClient, collected: dict[str, str], db: Session) -> None:
    set_reminder(client, collected, any_litter_id(db), "to_contact", minutes_from_now=60)

    assert notifier_service.send_due_follow_up_reminders(db, naive_utc_now()) == 0


def test_a_moved_reminder_is_pushed_again(client: TestClient, collected: dict[str, str], db: Session) -> None:
    litter_id = any_litter_id(db)
    set_reminder(client, collected, litter_id, "to_contact", minutes_from_now=-10)
    notifier_service.send_due_follow_up_reminders(db, naive_utc_now())

    set_reminder(client, collected, litter_id, "to_contact", minutes_from_now=-1)

    assert notifier_service.send_due_follow_up_reminders(db, naive_utc_now()) == 1


def test_a_dismissed_litter_is_not_reminded(client: TestClient, collected: dict[str, str], db: Session) -> None:
    set_reminder(client, collected, any_litter_id(db), "dismissed", minutes_from_now=-1)

    assert notifier_service.send_due_follow_up_reminders(db, naive_utc_now()) == 0


def test_a_litter_gone_from_its_sources_is_not_reminded(
    client: TestClient, collected: dict[str, str], db: Session
) -> None:
    litter_id = any_litter_id(db)
    set_reminder(client, collected, litter_id, "to_contact", minutes_from_now=-1)
    group = db.get(LitterGroup, litter_id)
    assert group is not None
    group.is_active = False
    db.commit()

    first_count = notifier_service.send_due_follow_up_reminders(db, naive_utc_now())
    second_count = notifier_service.send_due_follow_up_reminders(db, naive_utc_now())

    assert (first_count, second_count) == (0, 0)
    assert db.query(Notification).filter(Notification.kind == NotificationKind.FOLLOW_UP_REMINDER).count() == 0
