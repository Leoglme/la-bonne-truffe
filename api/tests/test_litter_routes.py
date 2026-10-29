"""Litter, follow-up and source routes, on the litters of the recorded pages."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from enums.listing_source import ListingSource
from models.listing import Listing
from models.user import User
from seeders.run_seeders import SeederRunner
from services.auth_service import AuthService
from services.collection_runner import collection_runner
from services.push_service import PushResult, PushService
from tests.centrale_canine_pages import collector_serving, load_recorded_pages, turn_gold

GOLD_LITTER_ID = "4333817"
EXPECTED_LITTER_ID = "4337070"
COLOR_BUNDLE_LITTER_ID = "4320577"


@pytest.fixture
def collected(db: Session, monkeypatch: pytest.MonkeyPatch) -> dict[str, str]:
    """
    Seed, collect the recorded pages once (pushes stubbed), and return the bearer header of the user.
    The expected litter 4337070 is turned gold, so that « À naître » lists one.
    """
    monkeypatch.setattr(PushService, "send", lambda *_args, **_kwargs: PushResult(delivered=1))
    SeederRunner.run(db)
    pages = load_recorded_pages()
    turn_gold(pages, EXPECTED_LITTER_ID)
    collection_runner.run_centrale_canine(db, collector_serving(pages))
    user = db.query(User).one()
    return {"Authorization": f"Bearer {AuthService.create_access_token(user.email)}"}


def group_id_of(db: Session, external_id: str) -> int:
    """The litter group of a recorded listing."""
    group_id = db.query(Listing).filter(Listing.external_id == external_id).one().litter_group_id
    assert group_id is not None
    return group_id


def test_home_list_is_sorted_by_score_and_filtered(client: TestClient, collected: dict[str, str], db: Session) -> None:
    cards = client.get("/api/v1/litters", headers=collected).json()
    preferred = client.get("/api/v1/litters", params={"tier": "preferred"}, headers=collected).json()
    expected = client.get("/api/v1/litters", params={"kind": "litter_expected"}, headers=collected).json()

    assert len(cards) == 9
    assert [card["score"] for card in cards] == sorted((card["score"] for card in cards), reverse=True)
    assert len(preferred) == 7
    assert [card["id"] for card in expected] == [group_id_of(db, EXPECTED_LITTER_ID)]
    gold_card = next(card for card in cards if card["id"] == group_id_of(db, GOLD_LITTER_ID))
    assert (gold_card["name"], gold_card["place"]) == ("Du Clos de l'Élevage D", "Saint-Aubin-du-Cormier")


def test_a_visit_returns_the_previous_one(client: TestClient, collected: dict[str, str]) -> None:
    first_visit = client.post("/api/v1/litters/visit", headers=collected).json()
    second_visit = client.post("/api/v1/litters/visit", headers=collected).json()

    assert first_visit == {"previous_visit_at": None}
    assert second_visit["previous_visit_at"] is not None


def test_detail_explains_the_score(client: TestClient, collected: dict[str, str], db: Session) -> None:
    detail = client.get(f"/api/v1/litters/{group_id_of(db, GOLD_LITTER_ID)}", headers=collected).json()

    assert detail["tier"] == "preferred"
    assert detail["reasons"][0] == {"text": "Gold, ta couleur préférée", "points": 40}
    assert detail["sire"] == {"name": "Père de test 23", "rating": 1}
    assert detail["breeder"]["phone_e164"] == "+33600000004"
    assert detail["breeder"]["is_selected_breeding"] is False
    assert detail["listings"][0]["external_url"] == "https://www.centrale-canine.fr/portee/2834593"
    assert detail["follow_up"] is None


def test_follow_and_note_a_litter(client: TestClient, collected: dict[str, str], db: Session) -> None:
    litter_id = group_id_of(db, EXPECTED_LITTER_ID)

    followed = client.put(f"/api/v1/litters/{litter_id}/follow-up", json={"status": "to_contact"}, headers=collected)
    note = client.post(
        f"/api/v1/litters/{litter_id}/notes", json={"text": "Appel : liste d'attente ouverte."}, headers=collected
    )
    follow_ups = client.get("/api/v1/follow-ups", headers=collected).json()

    assert followed.json()["follow_up"]["status"] == "to_contact"
    assert note.status_code == 201
    assert follow_ups[0]["litter"]["id"] == litter_id
    assert follow_ups[0]["last_note"]["text"] == "Appel : liste d'attente ouverte."


def test_delete_a_note(client: TestClient, collected: dict[str, str], db: Session) -> None:
    litter_id = group_id_of(db, EXPECTED_LITTER_ID)
    note_id = client.post(
        f"/api/v1/litters/{litter_id}/notes", json={"text": "Rappeler jeudi."}, headers=collected
    ).json()["id"]

    deleted = client.delete(f"/api/v1/litters/{litter_id}/notes/{note_id}", headers=collected)
    deleted_again = client.delete(f"/api/v1/litters/{litter_id}/notes/{note_id}", headers=collected)
    detail = client.get(f"/api/v1/litters/{litter_id}", headers=collected).json()

    assert deleted.status_code == 204
    assert deleted_again.status_code == 404
    assert detail["follow_up"]["notes"] == []


def test_stop_following_a_litter(client: TestClient, collected: dict[str, str], db: Session) -> None:
    litter_id = group_id_of(db, EXPECTED_LITTER_ID)
    client.put(f"/api/v1/litters/{litter_id}/follow-up", json={"status": "contacted"}, headers=collected)
    client.post(f"/api/v1/litters/{litter_id}/notes", json={"text": "Liste d'attente."}, headers=collected)

    detail = client.delete(f"/api/v1/litters/{litter_id}/follow-up", headers=collected).json()
    follow_ups = client.get("/api/v1/follow-ups", headers=collected).json()

    assert detail["follow_up"] is None
    assert follow_ups == []


def test_confirming_a_colour_turns_the_bundle_into_a_certain_colour(
    client: TestClient, collected: dict[str, str], db: Session
) -> None:
    litter_id = group_id_of(db, COLOR_BUNDLE_LITTER_ID)

    detail = client.patch(
        f"/api/v1/litters/{litter_id}/colors", json={"colors": ["noir_et_feu"]}, headers=collected
    ).json()

    assert detail["colors"] == [{"color": "noir_et_feu", "confidence": "confirmed"}]
    assert detail["tier"] == "acceptable"
    assert detail["reasons"][0]["text"] == "Noir et feu, une couleur acceptable"


def test_sources_report_their_last_run(client: TestClient, collected: dict[str, str]) -> None:
    statuses = {status["source"]: status for status in client.get("/api/v1/sources", headers=collected).json()}

    assert statuses["centrale_canine"]["last_status"] == "ok"
    assert statuses["centrale_canine"]["listings_seen"] == 19
    assert all(status["is_collected"] for status in statuses.values())
    assert statuses["chiots_de_france"]["last_status"] is None


def test_a_skipped_source_is_not_collected_and_cannot_be_run(
    client: TestClient, auth_headers: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    collected_sources = frozenset({ListingSource.CHIENS_DE_FRANCE, ListingSource.CHIOTS_DE_FRANCE})
    monkeypatch.setattr("services.source_status_service.COLLECTED_SOURCES", collected_sources)
    monkeypatch.setattr("api.v1.routes.sources.COLLECTED_SOURCES", collected_sources)

    statuses = {status["source"]: status for status in client.get("/api/v1/sources", headers=auth_headers).json()}
    run_response = client.post("/api/v1/sources/centrale_canine/run", headers=auth_headers)

    assert statuses["centrale_canine"]["is_collected"] is False
    assert statuses["chiens_de_france"]["is_collected"] is True
    assert run_response.status_code == 501


def test_unknown_litter_is_a_404(client: TestClient, collected: dict[str, str]) -> None:
    assert client.get("/api/v1/litters/9999", headers=collected).status_code == 404
