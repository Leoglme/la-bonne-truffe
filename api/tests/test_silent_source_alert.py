"""The « source silencieuse » alert: once per silence of a source the Windows app relays, in daytime only."""

from datetime import date, datetime, timedelta

import pytest
from sqlalchemy.orm import Session

from core.clock import naive_utc_of_french_time
from enums.listing_source import ListingSource
from enums.notification_kind import NotificationKind
from enums.source_run_status import SourceRunStatus
from models.notification import Notification
from models.source_run import SourceRun
from models.user import User
from services.notifier import SILENCE_BEFORE_ALERT, notifier_service
from services.push_service import PushResult, PushService
from worker import CollectionWorker

TODAY = date(2026, 10, 30)
NOON = naive_utc_of_french_time(TODAY, 12) + timedelta(minutes=15)
LATE_EVENING = naive_utc_of_french_time(TODAY - timedelta(days=1), 23) + timedelta(minutes=5)


@pytest.fixture(autouse=True)
def stubbed_push(monkeypatch: pytest.MonkeyPatch) -> None:
    """Never reach a push service."""
    monkeypatch.setattr(PushService, "send", lambda *_args, **_kwargs: PushResult(delivered=1))


def record_successful_run(db: Session, finished_at: datetime) -> None:
    """Write a successful Centrale Canine run that finished at a time."""
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
    first = notifier_service.alert_if_source_silent(db, ListingSource.CENTRALE_CANINE, NOON)
    second = notifier_service.alert_if_source_silent(db, ListingSource.CENTRALE_CANINE, NOON)
    alert = db.query(Notification).filter(Notification.kind == NotificationKind.SOURCE_SILENT).one()

    assert (first, second) == (True, False)
    assert alert.user_id == user.id
    assert alert.body == (
        "La Centrale Canine n’a pas été relevée depuis 3 h : aucun PC allumé avec l’app Windows, ou l’app déconnectée."
    )
    assert alert.url == "/"


def test_a_recent_successful_run_keeps_quiet(db: Session, user: User) -> None:
    record_successful_run(db, NOON - timedelta(hours=1))

    assert notifier_service.alert_if_source_silent(db, ListingSource.CENTRALE_CANINE, NOON) is False
    assert silent_alert_count(db) == 0


def test_a_long_silence_is_alerted_once_until_the_next_successful_run(db: Session, user: User) -> None:
    record_successful_run(db, NOON - SILENCE_BEFORE_ALERT - timedelta(hours=1))

    assert notifier_service.alert_if_source_silent(db, ListingSource.CENTRALE_CANINE, NOON) is True
    assert notifier_service.alert_if_source_silent(db, ListingSource.CENTRALE_CANINE, NOON) is False
    assert silent_alert_count(db) == 1

    record_successful_run(db, NOON)
    assert notifier_service.alert_if_source_silent(db, ListingSource.CENTRALE_CANINE, NOON) is False

    later = NOON + SILENCE_BEFORE_ALERT + timedelta(minutes=5)
    assert notifier_service.alert_if_source_silent(db, ListingSource.CENTRALE_CANINE, later) is True
    assert silent_alert_count(db) == 2


def test_a_source_in_error_is_silent_too(db: Session, user: User) -> None:
    failed_at = NOON - timedelta(minutes=30)
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

    assert notifier_service.alert_if_source_silent(db, ListingSource.CENTRALE_CANINE, NOON) is True


def test_a_computer_off_for_the_night_is_no_silence(db: Session, user: User) -> None:
    record_successful_run(db, LATE_EVENING)
    two_in_the_morning = naive_utc_of_french_time(TODAY, 2) + timedelta(minutes=15)
    quarter_past_eight = naive_utc_of_french_time(TODAY, 8) + timedelta(minutes=15)
    quarter_past_eleven = naive_utc_of_french_time(TODAY, 11) + timedelta(minutes=15)

    assert notifier_service.alert_if_source_silent(db, ListingSource.CENTRALE_CANINE, two_in_the_morning) is False
    assert notifier_service.alert_if_source_silent(db, ListingSource.CENTRALE_CANINE, quarter_past_eight) is False
    assert notifier_service.alert_if_source_silent(db, ListingSource.CENTRALE_CANINE, quarter_past_eleven) is True
    assert silent_alert_count(db) == 1


def test_the_worker_watches_the_relayed_sources(db: Session, user: User, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("worker.SessionLocal", lambda: db)
    monkeypatch.setattr("worker.naive_utc_now", lambda: NOON)
    worker = CollectionWorker(
        collected_sources=frozenset({ListingSource.CHIENS_DE_FRANCE}),
        relayed_sources=frozenset({ListingSource.CENTRALE_CANINE}),
    )

    worker.alert_silent_sources()

    assert silent_alert_count(db) == 1
