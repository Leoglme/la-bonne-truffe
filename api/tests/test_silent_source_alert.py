"""The « source silencieuse » alert: once per silence of a source the Windows app relays, ended by a successful run."""

from datetime import timedelta

import pytest
from sqlalchemy.orm import Session

from core.clock import naive_utc_now
from enums.listing_source import ListingSource
from enums.notification_kind import NotificationKind
from enums.source_run_status import SourceRunStatus
from models.notification import Notification
from models.source_run import SourceRun
from models.user import User
from services.notifier import SILENCE_BEFORE_ALERT, notifier_service
from services.push_service import PushResult, PushService
from worker import CollectionWorker


@pytest.fixture(autouse=True)
def stubbed_push(monkeypatch: pytest.MonkeyPatch) -> None:
    """Never reach a push service."""
    monkeypatch.setattr(PushService, "send", lambda *_args, **_kwargs: PushResult(delivered=1))


def record_successful_run(db: Session, hours_ago: float) -> None:
    """Write a successful Centrale Canine run that finished some hours ago."""
    finished_at = naive_utc_now() - timedelta(hours=hours_ago)
    db.add(
        SourceRun(
            source=ListingSource.CENTRALE_CANINE,
            started_at=finished_at - timedelta(minutes=1),
            finished_at=finished_at,
            status=SourceRunStatus.OK,
        )
    )
    db.commit()


def silent_alert_count(db: Session) -> int:
    """Alerts of silence kept in the bell history."""
    return db.query(Notification).filter(Notification.kind == NotificationKind.SOURCE_SILENT).count()


def test_a_source_never_run_is_alerted_once(db: Session, user: User) -> None:
    first = notifier_service.alert_if_source_silent(db, ListingSource.CENTRALE_CANINE, naive_utc_now())
    second = notifier_service.alert_if_source_silent(db, ListingSource.CENTRALE_CANINE, naive_utc_now())
    alert = db.query(Notification).filter(Notification.kind == NotificationKind.SOURCE_SILENT).one()

    assert (first, second) == (True, False)
    assert alert.user_id == user.id
    assert alert.body == (
        "La Centrale Canine n’a pas été relevée depuis 3 h : aucun PC allumé avec l’app Windows, ou l’app déconnectée."
    )
    assert alert.url == "/"


def test_a_recent_successful_run_keeps_quiet(db: Session, user: User) -> None:
    record_successful_run(db, hours_ago=1)

    assert notifier_service.alert_if_source_silent(db, ListingSource.CENTRALE_CANINE, naive_utc_now()) is False
    assert silent_alert_count(db) == 0


def test_a_long_silence_is_alerted_once_until_the_next_successful_run(db: Session, user: User) -> None:
    record_successful_run(db, hours_ago=SILENCE_BEFORE_ALERT.total_seconds() / 3600 + 1)

    assert notifier_service.alert_if_source_silent(db, ListingSource.CENTRALE_CANINE, naive_utc_now()) is True
    assert notifier_service.alert_if_source_silent(db, ListingSource.CENTRALE_CANINE, naive_utc_now()) is False
    assert silent_alert_count(db) == 1

    record_successful_run(db, hours_ago=0)
    assert notifier_service.alert_if_source_silent(db, ListingSource.CENTRALE_CANINE, naive_utc_now()) is False

    later = naive_utc_now() + SILENCE_BEFORE_ALERT + timedelta(minutes=5)
    assert notifier_service.alert_if_source_silent(db, ListingSource.CENTRALE_CANINE, later) is True
    assert silent_alert_count(db) == 2


def test_a_source_in_error_is_silent_too(db: Session, user: User) -> None:
    failed_at = naive_utc_now() - timedelta(minutes=30)
    db.add(
        SourceRun(
            source=ListingSource.CENTRALE_CANINE,
            started_at=failed_at,
            finished_at=failed_at,
            status=SourceRunStatus.ERROR,
            error_message="403",
        )
    )
    db.commit()

    assert notifier_service.alert_if_source_silent(db, ListingSource.CENTRALE_CANINE, naive_utc_now()) is True


def test_the_worker_watches_the_relayed_sources(db: Session, user: User, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("worker.SessionLocal", lambda: db)
    worker = CollectionWorker(
        collected_sources=frozenset({ListingSource.CHIENS_DE_FRANCE}),
        relayed_sources=frozenset({ListingSource.CENTRALE_CANINE}),
    )

    worker.alert_silent_sources()

    assert silent_alert_count(db) == 1
