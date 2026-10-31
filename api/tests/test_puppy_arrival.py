"""The puppy found: « C’est lui ! » pauses the search, the preparations are kept, and the search resumes."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from core.clock import naive_utc_now
from enums.match_event_kind import MatchEventKind
from models.digest_entry import DigestEntry
from models.listing import Listing
from models.litter_group import LitterGroup
from models.search_profile import SearchProfile
from models.user import User
from seeders.run_seeders import SeederRunner
from services.auth_service import AuthService
from services.collection_runner import collection_runner
from services.matching.snapshot_builder import LitterSnapshotBuilder
from services.notifier import notifier_service
from services.push_service import PushResult, PushService
from tests.centrale_canine_pages import collector_serving, load_recorded_pages

GOLD_LITTER_ID = "4333817"


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


@pytest.fixture
def collected(db: Session, pushed_bodies: list[str]) -> dict[str, str]:
    """Seed, collect the recorded pages once, forget the pushes of that run, and return the bearer header."""
    SeederRunner.run(db)
    collection_runner.run_centrale_canine(db, collector_serving(load_recorded_pages()))
    pushed_bodies.clear()
    user = db.query(User).one()
    return {"Authorization": f"Bearer {AuthService.create_access_token(user.email)}"}


def gold_group_id(db: Session) -> int:
    """The litter group of the recorded gold litter."""
    group_id = db.query(Listing).filter(Listing.external_id == GOLD_LITTER_ID).one().litter_group_id
    assert group_id is not None
    return group_id


def test_the_puppy_found_keeps_its_preparations_until_the_search_resumes(
    client: TestClient, collected: dict[str, str], db: Session
) -> None:
    litter_id = gold_group_id(db)

    started = client.put(
        "/api/v1/puppy-arrival", json={"litter_group_id": litter_id, "arrival_on": "2026-12-22"}, headers=collected
    )
    ticked = client.put(
        "/api/v1/puppy-arrival/checklist", json={"done_items": ["panier", "gamelles", "panier"]}, headers=collected
    )
    moved = client.put(
        "/api/v1/puppy-arrival", json={"litter_group_id": litter_id, "arrival_on": "2026-12-24"}, headers=collected
    )
    resumed = client.delete("/api/v1/puppy-arrival", headers=collected)

    assert started.status_code == 200
    assert started.json()["litter_group_id"] == litter_id
    assert ticked.json()["done_items"] == ["panier", "gamelles"]
    assert (moved.json()["arrival_on"], moved.json()["done_items"]) == ("2026-12-24", ["panier", "gamelles"])
    assert resumed.status_code == 204
    assert client.get("/api/v1/puppy-arrival", headers=collected).json() is None


def test_no_litter_alert_goes_out_while_the_puppy_is_found(
    client: TestClient, collected: dict[str, str], db: Session, pushed_bodies: list[str]
) -> None:
    litter_id = gold_group_id(db)
    profile = db.query(SearchProfile).one()
    db.add(
        DigestEntry(
            user_id=profile.user_id,
            litter_group_id=litter_id,
            event_kind=MatchEventKind.NEW_ACCEPTABLE,
            created_at=naive_utc_now(),
        )
    )
    db.commit()

    client.put(
        "/api/v1/puppy-arrival", json={"litter_group_id": litter_id, "arrival_on": "2026-12-22"}, headers=collected
    )
    group = db.get(LitterGroup, litter_id)
    assert group is not None
    snapshot = LitterSnapshotBuilder.build(db, group)
    assert snapshot is not None
    handled = notifier_service.dispatch(
        db, profile, snapshot, [MatchEventKind.NEW_PREFERRED, MatchEventKind.NEW_ACCEPTABLE], False, naive_utc_now()
    )

    assert handled == [MatchEventKind.NEW_PREFERRED, MatchEventKind.NEW_ACCEPTABLE]
    assert pushed_bodies == []
    assert db.query(DigestEntry).filter(DigestEntry.sent_at.is_(None)).count() == 0


def test_an_unknown_litter_or_a_checklist_without_a_puppy_is_a_404(
    client: TestClient, collected: dict[str, str]
) -> None:
    assert (
        client.put(
            "/api/v1/puppy-arrival", json={"litter_group_id": 9999, "arrival_on": "2026-12-22"}, headers=collected
        ).status_code
        == 404
    )
    assert client.put("/api/v1/puppy-arrival/checklist", json={"done_items": []}, headers=collected).status_code == 404
