"""Shared links: created by the user, opened without an account, private data left out, expired after 30 days."""

from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from core.clock import naive_utc_now
from core.config import settings
from models.listing import Listing
from models.litter_share import LitterShare
from models.user import User
from seeders.run_seeders import SeederRunner
from services.auth_service import AuthService
from services.collection_runner import collection_runner
from services.push_service import PushResult, PushService
from tests.centrale_canine_pages import collector_serving, load_recorded_pages

GOLD_LITTER_ID = "4333817"


@pytest.fixture
def collected(db: Session, monkeypatch: pytest.MonkeyPatch) -> dict[str, str]:
    """Seed, collect the recorded pages once (pushes stubbed), and return the bearer header of the user."""
    monkeypatch.setattr(PushService, "send", lambda *_args, **_kwargs: PushResult(delivered=1))
    SeederRunner.run(db)
    collection_runner.run_centrale_canine(db, collector_serving(load_recorded_pages()))
    user = db.query(User).one()
    return {"Authorization": f"Bearer {AuthService.create_access_token(user.email)}"}


def gold_group_id(db: Session) -> int:
    """The litter group of the recorded gold litter."""
    group_id = db.query(Listing).filter(Listing.external_id == GOLD_LITTER_ID).one().litter_group_id
    assert group_id is not None
    return group_id


def test_a_shared_litter_opens_without_an_account_and_leaves_out_the_private_data(
    client: TestClient, collected: dict[str, str], db: Session
) -> None:
    litter_id = gold_group_id(db)
    client.put(f"/api/v1/litters/{litter_id}/follow-up", json={"status": "contacted"}, headers=collected)

    created = client.post(
        f"/api/v1/litters/{litter_id}/shares", json={"message": "  On appelle demain ?  "}, headers=collected
    )
    url = created.json()["url"]
    page = client.get(f"/api/v1/shares/{url.rsplit('/', 1)[-1]}")

    assert created.status_code == 201
    assert url.startswith(f"{settings.web_base_url.rstrip('/')}/partage/")
    assert page.status_code == 200
    body = page.json()
    assert body["sharer_name"] == db.query(User).one().name
    assert body["message"] == "On appelle demain ?"
    assert body["litter"]["id"] == litter_id
    assert body["litter"]["breeder"] is not None
    assert (body["litter"]["score"], body["litter"]["reasons"], body["litter"]["follow_up"]) == (None, [], None)


def test_an_unknown_link_is_a_404_and_an_expired_one_a_410(
    client: TestClient, collected: dict[str, str], db: Session
) -> None:
    created = client.post(f"/api/v1/litters/{gold_group_id(db)}/shares", json={}, headers=collected).json()
    share = db.query(LitterShare).one()
    share.expires_at = naive_utc_now() - timedelta(minutes=1)
    db.commit()

    assert created["url"].endswith(share.token)
    assert client.get("/api/v1/shares/lien-inconnu").status_code == 404
    assert client.get(f"/api/v1/shares/{share.token}").status_code == 410


def test_sharing_needs_an_account_and_an_existing_litter(
    client: TestClient, collected: dict[str, str], db: Session
) -> None:
    assert client.post(f"/api/v1/litters/{gold_group_id(db)}/shares", json={}).status_code == 401
    assert client.post("/api/v1/litters/9999/shares", json={}, headers=collected).status_code == 404
