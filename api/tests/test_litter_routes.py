"""Litter, follow-up and source routes, on litters collected from the synthetic fixture."""

import json
from pathlib import Path
from typing import Any

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from models.listing import Listing
from models.user import User
from seeders.run_seeders import SeederRunner
from services.auth_service import AuthService
from services.collection_runner import collection_runner
from services.collectors.centrale_canine import CentraleCanineCollector
from services.push_service import PushResult, PushService

FIXTURE = Path(__file__).parent / "fixtures" / "centrale_canine" / "litters_35_page_0.json"


@pytest.fixture
def collected(db: Session, monkeypatch: pytest.MonkeyPatch) -> dict[str, str]:
    """Seed, collect the fixture once (pushes stubbed), and return the bearer header of the user."""
    monkeypatch.setattr(PushService, "send", lambda *_args, **_kwargs: PushResult(delivered=1))
    SeederRunner.run(db)
    page: dict[str, Any] = json.loads(FIXTURE.read_text(encoding="utf-8"))
    collector = CentraleCanineCollector(
        http_client=httpx.Client(transport=httpx.MockTransport(lambda _request: httpx.Response(200, json=page))),
        sleep=lambda _seconds: None,
    )
    collection_runner.run_centrale_canine(db, collector)
    user = db.query(User).one()
    return {"Authorization": f"Bearer {AuthService.create_access_token(user.email)}"}


def group_id_of(db: Session, external_id: str) -> int:
    """The litter group of a fixture listing."""
    group_id = db.query(Listing).filter(Listing.external_id == external_id).one().litter_group_id
    assert group_id is not None
    return group_id


def test_home_list_is_sorted_by_score_and_filtered(client: TestClient, collected: dict[str, str], db: Session) -> None:
    cards = client.get("/api/v1/litters", headers=collected).json()
    preferred = client.get("/api/v1/litters", params={"tier": "preferred"}, headers=collected).json()
    expected = client.get("/api/v1/litters", params={"kind": "litter_expected"}, headers=collected).json()

    assert len(cards) == 4
    assert cards[0]["id"] == group_id_of(db, "9000001")
    assert [card["score"] for card in cards] == sorted((card["score"] for card in cards), reverse=True)
    assert len(preferred) == 2
    assert [card["id"] for card in expected] == [group_id_of(db, "9000002")]
    assert cards[0]["name"] == "Portée de TEST Mère A"
    assert cards[0]["place"] == "Ille-et-Vilaine"


def test_detail_explains_the_score(client: TestClient, collected: dict[str, str], db: Session) -> None:
    detail = client.get(f"/api/v1/litters/{group_id_of(db, '9000001')}", headers=collected).json()

    assert detail["tier"] == "preferred"
    assert detail["reasons"][0] == {"text": "Gold, ta couleur préférée", "points": 40}
    assert detail["sire"] == {"name": "TEST Père A", "rating": 4}
    assert detail["breeder"]["is_selected_breeding"] is True
    assert detail["listings"][0]["external_url"] == "https://www.centrale-canine.fr/portee/9000001"
    assert detail["follow_up"] is None


def test_follow_and_note_a_litter(client: TestClient, collected: dict[str, str], db: Session) -> None:
    litter_id = group_id_of(db, "9000002")

    followed = client.put(f"/api/v1/litters/{litter_id}/follow-up", json={"status": "to_contact"}, headers=collected)
    note = client.post(
        f"/api/v1/litters/{litter_id}/notes", json={"text": "Appel : liste d'attente ouverte."}, headers=collected
    )
    follow_ups = client.get("/api/v1/follow-ups", headers=collected).json()

    assert followed.json()["follow_up"]["status"] == "to_contact"
    assert note.status_code == 201
    assert follow_ups[0]["litter"]["id"] == litter_id
    assert follow_ups[0]["last_note"]["text"] == "Appel : liste d'attente ouverte."


def test_confirming_a_colour_turns_the_bundle_into_a_certain_colour(
    client: TestClient, collected: dict[str, str], db: Session
) -> None:
    litter_id = group_id_of(db, "9000003")

    detail = client.patch(
        f"/api/v1/litters/{litter_id}/colors", json={"colors": ["noir_et_feu"]}, headers=collected
    ).json()

    assert detail["colors"] == [{"color": "noir_et_feu", "confidence": "confirmed"}]
    assert detail["tier"] == "acceptable"
    assert detail["reasons"][0]["text"] == "Noir et feu, une couleur acceptable"


def test_sources_report_their_last_run(client: TestClient, collected: dict[str, str]) -> None:
    statuses = {status["source"]: status for status in client.get("/api/v1/sources", headers=collected).json()}

    assert statuses["centrale_canine"]["last_status"] == "ok"
    assert statuses["centrale_canine"]["listings_seen"] == 4
    assert statuses["chiens_de_france"]["is_collected"] is False
    assert client.post("/api/v1/sources/chiens_de_france/run", headers=collected).status_code == 501


def test_unknown_litter_is_a_404(client: TestClient, collected: dict[str, str]) -> None:
    assert client.get("/api/v1/litters/9999", headers=collected).status_code == 404
