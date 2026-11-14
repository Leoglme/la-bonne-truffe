"""The breeder routes: the list, the search, the detail, the follow and its notes, and a breeder added by hand."""

from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from models.breeder import Breeder
from models.user import User
from seeders.run_seeders import SeederRunner
from services.auth_service import AuthService
from services.collection_runner import collection_runner
from services.push_service import PushResult, PushService
from tests.centrale_canine_pages import collector_serving, load_recorded_pages
from tests.scc_dog_pages import dog_collector_serving

BREEDERS_URL = "/api/v1/breeders"
GOLD_BREEDER_SCC_ID = "74617"  # Élevage D: three gold litters
FIRST_BREEDER_SCC_ID = "266172"  # Élevage A: the most litters, two of them expected


@pytest.fixture
def collected(db: Session, monkeypatch: pytest.MonkeyPatch) -> dict[str, str]:
    """Seed, collect the recorded litters once (pushes stubbed), and return the bearer header of the user."""
    monkeypatch.setattr(PushService, "send", lambda *_args, **_kwargs: PushResult(delivered=1))
    SeederRunner.run(db)
    collection_runner.run_centrale_canine(db, collector_serving(load_recorded_pages()))
    user = db.query(User).one()
    return {"Authorization": f"Bearer {AuthService.create_access_token(user.email)}"}


def breeder_of(db: Session, scc_breeder_id: str) -> Breeder:
    """A recorded breeder, by its Centrale Canine identifier."""
    return db.query(Breeder).filter(Breeder.scc_breeder_id == scc_breeder_id).one()


def name_of(breeder: Breeder) -> str:
    """The breeder as the cards name it."""
    return breeder.affix or breeder.display_name or ""


def test_the_list_names_every_breeder_of_the_recorded_litters(
    client: TestClient, db: Session, collected: dict[str, str]
) -> None:
    cards = client.get(BREEDERS_URL, headers=collected).json()
    gold_cards = client.get(BREEDERS_URL, params={"filter": "gold"}, headers=collected).json()
    by_name = client.get(BREEDERS_URL, params={"sort": "name"}, headers=collected).json()

    assert len(cards) == 5
    assert {card["department_code"] for card in cards} == {"35"}
    assert cards[0]["department_name"] == "Ille-et-Vilaine"
    assert all(card["sources"] == ["centrale_canine"] for card in cards)
    assert all(card["is_followed"] is False and card["follow_status"] is None for card in cards)
    has_current_litter = [card["current_litter"] is not None for card in cards]
    assert has_current_litter == sorted(has_current_litter, reverse=True)
    assert sorted(card["gold_litters_count"] for card in gold_cards) == [3, 3]
    assert [card["name"] for card in by_name] == sorted(card["name"] for card in cards)
    first_breeder = next(card for card in cards if card["id"] == breeder_of(db, FIRST_BREEDER_SCC_ID).id)
    assert first_breeder["litters_count"] == 9
    assert first_breeder["last_litter_date"] is not None


def test_the_search_finds_a_breeder_by_a_piece_of_its_name_or_by_its_phone(
    client: TestClient, db: Session, collected: dict[str, str]
) -> None:
    gold_breeder = breeder_of(db, GOLD_BREEDER_SCC_ID)
    first_breeder = breeder_of(db, FIRST_BREEDER_SCC_ID)
    assert first_breeder.phone_e164 == "+33600000001"

    by_name = client.get(f"{BREEDERS_URL}/search", params={"q": name_of(gold_breeder)[-9:]}, headers=collected).json()
    by_phone = client.get(f"{BREEDERS_URL}/search", params={"q": "06 00 00 00 01"}, headers=collected).json()
    nothing = client.get(f"{BREEDERS_URL}/search", params={"q": "kerlann"}, headers=collected).json()
    blank = client.get(f"{BREEDERS_URL}/search", params={"q": "  "}, headers=collected).json()

    # Every word of the query is looked for on its own, and a lone letter is everywhere: the phrase ranks first.
    assert by_name["breeders"][0]["id"] == gold_breeder.id
    assert len(by_name["breeders"]) == 5
    assert [card["id"] for card in by_phone["breeders"]] == [first_breeder.id]
    assert nothing == {"breeders": [], "litters": []}
    assert blank == {"breeders": [], "litters": []}


def test_the_detail_tells_the_litters_the_colours_and_the_dogs_of_the_breeding(
    client: TestClient, db: Session, collected: dict[str, str]
) -> None:
    collection_runner.run_scc_dogs(db, dog_collector_serving())
    gold_breeder = breeder_of(db, GOLD_BREEDER_SCC_ID)

    detail = client.get(f"{BREEDERS_URL}/{gold_breeder.id}", headers=collected).json()
    unknown = client.get(f"{BREEDERS_URL}/999999", headers=collected)

    assert detail["name"] == name_of(gold_breeder)
    assert detail["scc_breeder_id"] == GOLD_BREEDER_SCC_ID
    assert len(detail["litters"]) == 3
    births = [
        (litter["is_active"], litter["birth_date"] or litter["expected_birth_date"] or "")
        for litter in detail["litters"]
    ]
    assert len(set(births)) == 3
    assert births == sorted(births, reverse=True)
    assert detail["color_shares"] == [{"color": "gold", "litters_count": 3}]
    assert detail["gold_litters_count"] == 3
    assert (detail["follow"], detail["is_followed"]) == (None, False)
    assert [(dog["name"], dog["role"], dog["e_locus"]) for dog in detail["reproducers"]] == [
        ("Mère Gold", "parent", None)
    ]
    assert unknown.status_code == 404
    assert unknown.json()["detail"] == "Éleveur introuvable"


def test_following_a_breeder_keeps_its_status_its_notes_and_its_reminder(
    client: TestClient, db: Session, collected: dict[str, str]
) -> None:
    breeder = breeder_of(db, GOLD_BREEDER_SCC_ID)
    reminder = (datetime.now(UTC) + timedelta(days=2)).replace(microsecond=0)

    followed = client.put(
        f"{BREEDERS_URL}/{breeder.id}/follow",
        json={"status": "contacted", "notify_birth": False, "next_reminder_at": reminder.isoformat()},
        headers=collected,
    ).json()
    note = client.post(f"{BREEDERS_URL}/{breeder.id}/notes", json={"text": "À rappeler mardi"}, headers=collected)
    followed_cards = client.get(BREEDERS_URL, params={"filter": "followed"}, headers=collected).json()
    detail = client.get(f"{BREEDERS_URL}/{breeder.id}", headers=collected).json()
    removed_note = client.delete(f"{BREEDERS_URL}/{breeder.id}/notes/{note.json()['id']}", headers=collected)
    unknown_note = client.delete(f"{BREEDERS_URL}/{breeder.id}/notes/999999", headers=collected)
    unfollowed = client.delete(f"{BREEDERS_URL}/{breeder.id}/follow", headers=collected).json()

    assert followed["is_followed"] is True
    assert followed["follow"]["status"] == "contacted"
    assert (followed["follow"]["notify_birth"], followed["follow"]["notify_new_mating"]) == (False, True)
    assert followed["follow"]["next_reminder_at"].startswith(reminder.strftime("%Y-%m-%dT%H:%M:%S"))
    assert note.status_code == 201
    assert note.json()["text"] == "À rappeler mardi"
    assert [(card["id"], card["follow_status"]) for card in followed_cards] == [(breeder.id, "contacted")]
    assert [entry["text"] for entry in detail["follow"]["notes"]] == ["À rappeler mardi"]
    assert removed_note.status_code == 204
    assert unknown_note.status_code == 404
    assert (unfollowed["follow"], unfollowed["is_followed"]) == (None, False)


def test_a_breeder_added_by_hand_is_followed_listed_and_found(
    client: TestClient, db: Session, collected: dict[str, str]
) -> None:
    payload = {
        "display_name": "Élevage des Landes de Test",
        "city": "rennes",
        "zip_code": "35000",
        "phone": "06 12 34 56 78",
        "links": [{"label": "Facebook", "url": "https://www.facebook.com/landesdetest"}],
        "notes": "Vu sur Facebook",
    }

    created = client.post(BREEDERS_URL, json=payload, headers=collected)
    detail = created.json()
    again = client.post(
        BREEDERS_URL, json={"display_name": "Élevage des Landes de Test", "zip_code": "35000"}, headers=collected
    )
    found = client.get(f"{BREEDERS_URL}/search", params={"q": "landes de test"}, headers=collected).json()
    updated = client.patch(
        f"{BREEDERS_URL}/{detail['id']}",
        json={"website": "https://landes-de-test.fr", "phone": "0611111111"},
        headers=collected,
    ).json()
    followed_cards = client.get(BREEDERS_URL, params={"filter": "followed"}, headers=collected).json()

    assert created.status_code == 201
    assert detail["name"] == "Des Landes de Test"
    assert (detail["is_manual"], detail["is_followed"], detail["follow"]["status"]) == (True, True, "to_contact")
    assert (detail["city"], detail["zip_code"], detail["department_code"]) == ("Rennes", "35000", "35")
    assert detail["phone_e164"] == "+33612345678"
    assert detail["links"] == [{"label": "Facebook", "url": "https://www.facebook.com/landesdetest"}]
    assert detail["notes"] == "Vu sur Facebook"
    assert again.status_code == 201
    assert again.json()["id"] == detail["id"]
    assert [card["id"] for card in found["breeders"]] == [detail["id"]]
    assert (updated["website"], updated["phone_e164"]) == ("https://landes-de-test.fr", "+33611111111")
    assert [card["id"] for card in followed_cards] == [detail["id"]]
    assert db.query(Breeder).filter(Breeder.is_manual.is_(True)).count() == 1
