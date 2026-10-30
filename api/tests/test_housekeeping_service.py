"""Nightly housekeeping: raw pages of long-gone listings and old field changes go, the rest stays."""

from datetime import timedelta

import pytest
from sqlalchemy.orm import Session

from core.clock import naive_utc_now
from models.listing import Listing
from models.listing_change import ListingChange
from seeders.run_seeders import SeederRunner
from services.collection_runner import collection_runner
from services.housekeeping_service import LISTING_DATA_RETENTION, housekeeping_service
from services.push_service import PushResult, PushService
from tests.centrale_canine_pages import collector_serving, load_recorded_pages


@pytest.fixture
def listings(db: Session, monkeypatch: pytest.MonkeyPatch) -> list[Listing]:
    """Seed and collect the recorded pages once (pushes stubbed), and return the stored listings."""
    monkeypatch.setattr(PushService, "send", lambda *_args, **_kwargs: PushResult(delivered=1))
    SeederRunner.run(db)
    collection_runner.run_centrale_canine(db, collector_serving(load_recorded_pages()))
    return db.query(Listing).order_by(Listing.id).all()


def record_change(db: Session, listing: Listing, days_ago: int) -> int:
    """Write a field change seen some days ago on a listing, and return its id."""
    change = ListingChange(
        listing_id=listing.id,
        field="price_cents",
        old_value=None,
        new_value="120000",
        changed_at=naive_utc_now() - timedelta(days=days_ago),
    )
    db.add(change)
    db.commit()
    return change.id


def test_a_listing_gone_for_three_months_loses_its_raw_page(db: Session, listings: list[Listing]) -> None:
    gone_listing, fresh_listing = listings[0], listings[1]
    gone_listing.is_active = False
    gone_listing.last_seen_at = naive_utc_now() - LISTING_DATA_RETENTION - timedelta(days=1)
    db.commit()

    report = housekeeping_service.purge_old_listing_data(db, naive_utc_now())
    db.expire_all()

    assert report.raw_pages_cleared == 1
    assert gone_listing.raw_json is None
    assert fresh_listing.raw_json is not None


def test_a_listing_gone_recently_or_still_online_keeps_its_raw_page(db: Session, listings: list[Listing]) -> None:
    gone_recently, still_online = listings[0], listings[1]
    gone_recently.is_active = False
    gone_recently.last_seen_at = naive_utc_now() - timedelta(days=30)
    still_online.last_seen_at = naive_utc_now() - LISTING_DATA_RETENTION - timedelta(days=1)
    db.commit()

    report = housekeeping_service.purge_old_listing_data(db, naive_utc_now())
    db.expire_all()

    assert report.raw_pages_cleared == 0
    assert gone_recently.raw_json is not None
    assert still_online.raw_json is not None


def test_old_changes_are_deleted_and_recent_ones_kept(db: Session, listings: list[Listing]) -> None:
    old_change_id = record_change(db, listings[0], days_ago=100)
    recent_change_id = record_change(db, listings[0], days_ago=10)

    report = housekeeping_service.purge_old_listing_data(db, naive_utc_now())
    remaining_ids = {change.id for change in db.query(ListingChange).all()}

    assert report.changes_deleted == 1
    assert old_change_id not in remaining_ids
    assert recent_change_id in remaining_ids
