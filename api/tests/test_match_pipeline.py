"""A run end to end: grouping, matching, immediate pushes, birth, evening digest, source alert, profile save."""

import json
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx
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
from services.collectors.centrale_canine import CentraleCanineCollector
from services.notifier import notifier_service
from services.push_service import PushResult, PushService

FIXTURE = Path(__file__).parent / "fixtures" / "centrale_canine" / "litters_35_page_0.json"


def load_page() -> dict[str, Any]:
    """The synthetic page of the fixtures."""
    page: dict[str, Any] = json.loads(FIXTURE.read_text(encoding="utf-8"))
    return page


def collector_serving(
    page_for_request: Callable[[], dict[str, Any]], status_code: int = 200
) -> CentraleCanineCollector:
    """A collector whose every request gets the given page and status, without waiting."""
    return CentraleCanineCollector(
        http_client=httpx.Client(
            transport=httpx.MockTransport(lambda _request: httpx.Response(status_code, json=page_for_request()))
        ),
        sleep=lambda _seconds: None,
    )


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


def test_first_run_pushes_preferred_litters_and_queues_acceptable_ones(db: Session, pushed_bodies: list[str]) -> None:
    SeederRunner.run(db)

    report = collection_runner.run_centrale_canine(db, collector_serving(load_page))

    assert len(report.grouping.new_group_ids) == 4
    assert match_of(db, "9000001").tier == MatchTier.PREFERRED
    assert match_of(db, "9000002").tier == MatchTier.PREFERRED
    assert match_of(db, "9000003").tier == MatchTier.ACCEPTABLE
    assert match_of(db, "9000004").tier == MatchTier.ACCEPTABLE
    assert len(pushed_bodies) == 2
    assert any(
        body.startswith("Nouvelle portée, née le 27 octobre (Ille-et-Vilaine) : une portée gold")
        for body in pushed_bodies
    )
    assert any(body.startswith("À naître (Ille-et-Vilaine) : une portée gold déclarée") for body in pushed_bodies)
    assert db.query(DigestEntry).count() == 2
    assert db.query(Notification).filter(Notification.kind == NotificationKind.NEW_PREFERRED).count() == 2


def test_a_second_identical_run_notifies_nothing(db: Session, pushed_bodies: list[str]) -> None:
    SeederRunner.run(db)
    collection_runner.run_centrale_canine(db, collector_serving(load_page))

    collection_runner.run_centrale_canine(db, collector_serving(load_page))

    assert len(pushed_bodies) == 2
    assert db.query(DigestEntry).count() == 2


def test_birth_of_a_preferred_expected_litter_is_pushed_with_its_sexes(db: Session, pushed_bodies: list[str]) -> None:
    SeederRunner.run(db)
    collection_runner.run_centrale_canine(db, collector_serving(load_page))
    born_page = load_page()
    born_page["litters"]["node"]["2"]["n9000002"].update(
        {"n_is_borned": True, "n_birth_date": 1792918800, "n_male_number": 1, "n_female_number": 4}
    )

    report = collection_runner.run_centrale_canine(db, collector_serving(lambda: born_page))

    group = db.query(LitterGroup).join(Listing).filter(Listing.external_id == "9000002").one()
    assert report.grouping.born_group_ids == [group.id]
    assert pushed_bodies[-1].startswith("Née le ")
    assert "une portée gold, 1 mâle et 4 femelles. Dispo vers le " in pushed_bodies[-1]
    assert db.query(Notification).filter(Notification.kind == NotificationKind.BORN).count() == 1


def test_evening_digest_is_sent_once_at_the_digest_hour(db: Session, pushed_bodies: list[str]) -> None:
    SeederRunner.run(db)
    collection_runner.run_centrale_canine(db, collector_serving(load_page))

    assert notifier_service.send_due_evening_digests(db, datetime(2026, 10, 28, 17, 0)) == 0
    assert notifier_service.send_due_evening_digests(db, datetime(2026, 10, 28, 18, 0)) == 1
    assert notifier_service.send_due_evening_digests(db, datetime(2026, 10, 28, 18, 30)) == 0
    assert pushed_bodies[-1].startswith("Récap du soir : 2 portées acceptables, dont 1 ")


def test_three_failed_runs_alert_once_per_outage(db: Session, pushed_bodies: list[str]) -> None:
    SeederRunner.run(db)
    refused = collector_serving(dict, status_code=403)

    for _ in range(4):
        collection_runner.run_centrale_canine(db, refused)

    alerts = db.query(Notification).filter(Notification.kind == NotificationKind.SOURCE_DOWN).all()
    assert len(alerts) == 1
    assert alerts[0].body.startswith("La Centrale Canine ne répond plus depuis 3 relevés.")


def test_saving_the_criteria_reevaluates_without_pushing(
    db: Session, client: TestClient, pushed_bodies: list[str]
) -> None:
    SeederRunner.run(db)
    collection_runner.run_centrale_canine(db, collector_serving(load_page))
    user = db.query(User).one()
    headers = {"Authorization": f"Bearer {AuthService.create_access_token(user.email)}"}
    profile = client.get("/api/v1/profiles", headers=headers).json()[0]
    profile["color_preferences"]["noir_et_feu"] = "ignored"
    profile["color_preferences"]["noir"] = "ignored"
    profile["color_preferences"]["marron"] = "ignored"
    profile["color_preferences"]["marron_et_feu"] = "ignored"

    response = client.put(f"/api/v1/profiles/{profile['id']}", json=profile, headers=headers)

    assert response.status_code == 200
    db.expire_all()
    assert match_of(db, "9000003").tier == MatchTier.IGNORED
    assert len(pushed_bodies) == 2


def test_profile_save_refuses_an_unknown_department(db: Session, client: TestClient) -> None:
    SeederRunner.run(db)
    user = db.query(User).one()
    headers = {"Authorization": f"Bearer {AuthService.create_access_token(user.email)}"}
    profile = client.get("/api/v1/profiles", headers=headers).json()[0]
    profile["department_codes"] = ["35", "99"]

    response = client.put(f"/api/v1/profiles/{profile['id']}", json=profile, headers=headers)

    assert response.status_code == 422
    assert db.query(SearchProfile).one().department_codes[1] == "56"
