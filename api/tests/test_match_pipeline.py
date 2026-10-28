"""A run end to end on the recorded pages: matching, news window, pushes, birth, digest, source alert, profile save."""

from datetime import datetime
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from enums.match_tier import MatchTier
from enums.notification_kind import NotificationKind
from models.digest_entry import DigestEntry
from models.listing import Listing
from models.listing_match import ListingMatch
from models.litter_group import LitterGroup
from models.notification import Notification
from models.search_profile import SearchProfile
from models.user import User
from seeders.run_seeders import SeederRunner
from services.auth_service import AuthService
from services.collection_runner import collection_runner
from services.notifier import notifier_service
from services.push_service import PushResult, PushService
from tests.centrale_canine_pages import (
    collector_serving,
    litter_in,
    load_recorded_pages,
    mark_published_an_hour_ago,
    refusing_collector,
    remove_litter,
    turn_gold,
)

EXPECTED_LITTER_ID = "4337070"
BIRTH_ON_27_OCTOBER_2026 = 1793102400
RECENT_GOLD_LITTER_ID = "4333817"
RECENT_BUNDLE_LITTER_ID = "4320577"


def pages_before_the_recent_litters() -> list[dict[str, Any]]:
    """The recorded pages without the two litters that a later run finds just published."""
    pages = load_recorded_pages()
    remove_litter(pages, RECENT_GOLD_LITTER_ID)
    remove_litter(pages, RECENT_BUNDLE_LITTER_ID)
    return pages


def pages_with_the_recent_litters() -> list[dict[str, Any]]:
    """The recorded pages, a gold litter and a colour bundle published an hour ago."""
    pages = load_recorded_pages()
    mark_published_an_hour_ago(pages, RECENT_GOLD_LITTER_ID)
    mark_published_an_hour_ago(pages, RECENT_BUNDLE_LITTER_ID)
    return pages


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


def match_of(db: Session, external_id: str) -> ListingMatch:
    """The match of the group holding a listing."""
    listing = db.query(Listing).filter(Listing.external_id == external_id).one()
    return db.query(ListingMatch).filter(ListingMatch.litter_group_id == listing.litter_group_id).one()


def test_first_run_records_the_litters_published_long_ago_without_a_push(db: Session, pushed_bodies: list[str]) -> None:
    SeederRunner.run(db)

    report = collection_runner.run_centrale_canine(db, collector_serving(load_recorded_pages()))

    assert len(report.grouping.new_group_ids) == 19
    assert match_of(db, "4236807").tier == MatchTier.PREFERRED
    assert match_of(db, "4320577").tier == MatchTier.ACCEPTABLE
    assert match_of(db, "4198846").tier == MatchTier.IGNORED
    assert "new_preferred" in match_of(db, "4236807").notified_events
    assert pushed_bodies == []
    assert db.query(DigestEntry).count() == 0
    assert db.query(Notification).count() == 0


def test_first_run_of_a_source_sends_nothing_even_for_a_litter_published_an_hour_ago(
    db: Session, pushed_bodies: list[str]
) -> None:
    SeederRunner.run(db)

    collection_runner.run_centrale_canine(db, collector_serving(pages_with_the_recent_litters()))

    assert pushed_bodies == []
    assert db.query(DigestEntry).count() == 0
    assert "new_preferred" in match_of(db, RECENT_GOLD_LITTER_ID).notified_events


def test_a_litter_published_in_the_last_days_is_pushed_or_kept_for_the_evening(
    db: Session, pushed_bodies: list[str]
) -> None:
    SeederRunner.run(db)
    collection_runner.run_centrale_canine(db, collector_serving(pages_before_the_recent_litters()))

    collection_runner.run_centrale_canine(db, collector_serving(pages_with_the_recent_litters()))

    assert len(pushed_bodies) == 1
    assert pushed_bodies[0].startswith(
        "Nouvelle portée, née le 8 octobre (Ille-et-Vilaine) : une portée gold, 4 mâles et 1 femelle."
    )
    assert db.query(Notification).filter(Notification.kind == NotificationKind.NEW_PREFERRED).count() == 1
    assert db.query(DigestEntry).count() == 1


def test_a_second_identical_run_notifies_nothing(db: Session, pushed_bodies: list[str]) -> None:
    SeederRunner.run(db)
    collection_runner.run_centrale_canine(db, collector_serving(pages_before_the_recent_litters()))
    collection_runner.run_centrale_canine(db, collector_serving(pages_with_the_recent_litters()))

    collection_runner.run_centrale_canine(db, collector_serving(pages_with_the_recent_litters()))

    assert len(pushed_bodies) == 1
    assert db.query(DigestEntry).count() == 1


def test_birth_of_a_preferred_litter_is_pushed_even_when_published_long_ago(
    db: Session, pushed_bodies: list[str]
) -> None:
    SeederRunner.run(db)
    expected_pages = load_recorded_pages()
    turn_gold(expected_pages, EXPECTED_LITTER_ID)
    collection_runner.run_centrale_canine(db, collector_serving(expected_pages))
    born_pages = load_recorded_pages()
    turn_gold(born_pages, EXPECTED_LITTER_ID)
    litter_in(born_pages, EXPECTED_LITTER_ID).update(
        {
            "n_is_borned": True,
            "n_birth_date": [BIRTH_ON_27_OCTOBER_2026],
            "n_male_number": [1],
            "n_female_number": [4],
            "n_litter_status": [2],
        }
    )

    report = collection_runner.run_centrale_canine(db, collector_serving(born_pages))

    group = db.query(LitterGroup).join(Listing).filter(Listing.external_id == EXPECTED_LITTER_ID).one()
    assert report.grouping.born_group_ids == [group.id]
    assert len(pushed_bodies) == 1
    assert pushed_bodies[0].startswith("Née le 27 octobre (Ille-et-Vilaine) : une portée gold, 1 mâle et 4 femelles.")
    assert db.query(Notification).filter(Notification.kind == NotificationKind.BORN).count() == 1


def test_evening_digest_is_sent_once_at_the_digest_hour(db: Session, pushed_bodies: list[str]) -> None:
    SeederRunner.run(db)
    collection_runner.run_centrale_canine(db, collector_serving(pages_before_the_recent_litters()))
    bundle_only_pages = load_recorded_pages()
    remove_litter(bundle_only_pages, RECENT_GOLD_LITTER_ID)
    mark_published_an_hour_ago(bundle_only_pages, RECENT_BUNDLE_LITTER_ID)
    collection_runner.run_centrale_canine(db, collector_serving(bundle_only_pages))

    assert notifier_service.send_due_evening_digests(db, datetime(2026, 10, 28, 17, 0)) == 0
    assert notifier_service.send_due_evening_digests(db, datetime(2026, 10, 28, 18, 0)) == 1
    assert notifier_service.send_due_evening_digests(db, datetime(2026, 10, 28, 18, 30)) == 0
    assert pushed_bodies == [
        "Récap du soir : 1 portée acceptable : une portée noir ou noir et feu ou marron ou marron et feu"
        " (à confirmer) (Ille-et-Vilaine)."
    ]


def test_three_failed_runs_alert_once_per_outage(db: Session, pushed_bodies: list[str]) -> None:
    SeederRunner.run(db)

    for _ in range(4):
        collection_runner.run_centrale_canine(db, refusing_collector())

    alerts = db.query(Notification).filter(Notification.kind == NotificationKind.SOURCE_DOWN).all()
    assert len(alerts) == 1
    assert alerts[0].body.startswith("La Centrale Canine ne répond plus depuis 3 relevés.")


def test_saving_the_criteria_reevaluates_without_pushing_even_an_upgrade(
    db: Session, client: TestClient, pushed_bodies: list[str]
) -> None:
    SeederRunner.run(db)
    db.query(SearchProfile).one().color_preferences = {"gold": "acceptable", "noir_et_feu": "acceptable"}
    db.commit()
    collection_runner.run_centrale_canine(db, collector_serving(load_recorded_pages()))
    user = db.query(User).one()
    headers = {"Authorization": f"Bearer {AuthService.create_access_token(user.email)}"}
    profile = client.get("/api/v1/profiles", headers=headers).json()[0]
    profile["color_preferences"]["gold"] = "preferred"
    profile["color_preferences"]["noir_et_feu"] = "ignored"

    response = client.put(f"/api/v1/profiles/{profile['id']}", json=profile, headers=headers)

    assert response.status_code == 200
    db.expire_all()
    assert match_of(db, "4236807").tier == MatchTier.PREFERRED
    assert "upgraded" in match_of(db, "4236807").notified_events
    assert match_of(db, "4320577").tier == MatchTier.IGNORED
    assert pushed_bodies == []


def test_profile_save_refuses_an_unknown_department(db: Session, client: TestClient) -> None:
    SeederRunner.run(db)
    user = db.query(User).one()
    headers = {"Authorization": f"Bearer {AuthService.create_access_token(user.email)}"}
    profile = client.get("/api/v1/profiles", headers=headers).json()[0]
    profile["department_codes"] = ["35", "99"]

    response = client.put(f"/api/v1/profiles/{profile['id']}", json=profile, headers=headers)

    assert response.status_code == 422
    assert db.query(SearchProfile).one().department_codes[1] == "56"
