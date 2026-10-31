"""One relay chains the litters, the breeder directory and the dog pages under the same token (docs/05)."""

import json
from typing import Any

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from enums.listing_source import ListingSource
from models.breeder import Breeder
from models.dog import Dog
from models.user import User
from seeders.run_seeders import SeederRunner
from services.auth_service import AuthService
from services.centrale_canine_relay import CentraleCanineRelay
from services.collectors.centrale_canine import ALL_DEPARTMENTS_FILTER
from services.collectors.scc_breeders import CLUB_API_PATH
from services.push_service import PushResult, PushService
from tests.centrale_canine_pages import EMPTY_PAGE, RECORDED_DEPARTMENT_TERM_ID, load_recorded_pages
from tests.scc_breeder_pages import BREEDER_F_ID, answer_directory_request
from tests.scc_dog_pages import GOLD_FATHER_DOG_ID, GOLD_PUPPY_IDS, answer_dog_request

RELAY_URL = "/api/v1/sources/centrale_canine/relay"
CHAINED_SOURCES = frozenset({ListingSource.CENTRALE_CANINE, ListingSource.SCC_BREEDERS, ListingSource.SCC_DOGS})
MAXIMUM_ROUNDS = 12


@pytest.fixture
def chained_relay_headers(db: Session, monkeypatch: pytest.MonkeyPatch) -> dict[str, str]:
    """Seed, let the desktop app relay the three Centrale Canine sources (pushes stubbed), and return the header."""
    monkeypatch.setattr(PushService, "send", lambda *_args, **_kwargs: PushResult(delivered=1))
    monkeypatch.setattr("api.v1.routes.sources.DESKTOP_RELAYED_SOURCES", CHAINED_SOURCES)
    monkeypatch.setattr("services.source_status_service.DESKTOP_RELAYED_SOURCES", CHAINED_SOURCES)
    monkeypatch.setattr("api.v1.routes.sources.centrale_canine_relay", CentraleCanineRelay())
    SeederRunner.run(db)
    user = db.query(User).one()
    return {"Authorization": f"Bearer {AuthService.create_access_token(user.email)}"}


def answer_like_the_desktop_app(page_requests: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Answer each page request as the curl of the desktop app would: the recorded litter pages for
    Ille-et-Vilaine, the directory and club pages of the tests, the litter and dog pages of the tests.

    Args:
        page_requests: Pages the API asked for.

    Returns:
        The relayed responses.
    """
    litter_pages = load_recorded_pages()
    responses: list[dict[str, Any]] = []
    for page_request in page_requests:
        url = httpx.URL(page_request["url"])
        if "/chiots-de-la-race/" in url.path:
            page_number = int(url.path.rsplit("/", 1)[1])
            is_recorded = url.params.get("department") in (RECORDED_DEPARTMENT_TERM_ID, ALL_DEPARTMENTS_FILTER)
            page = litter_pages[page_number] if is_recorded and page_number < len(litter_pages) else EMPTY_PAGE
            responses.append({"url": page_request["url"], "status_code": 200, "body": json.dumps(page)})
            continue
        request = httpx.Request("GET", url)
        is_directory = "/eleveurs/" in url.path or url.path.startswith(CLUB_API_PATH)
        response = answer_directory_request(request) if is_directory else answer_dog_request(request)
        responses.append({"url": page_request["url"], "status_code": response.status_code, "body": response.text})
    return responses


def relay_until_done(
    client: TestClient, headers: dict[str, str], is_requested_by_user: bool = False
) -> tuple[list[str], list[str], dict[str, Any]]:
    """
    Relay round after round until the API has nothing more to ask.

    Args:
        client: The API.
        headers: Bearer header.
        is_requested_by_user: « Relever maintenant », which takes every source whatever its last run.

    Returns:
        The source of each round, the first URL asked in each round, and the last answer.
    """
    answer = client.post(RELAY_URL, json={"is_requested_by_user": is_requested_by_user}, headers=headers).json()
    relay_token = answer["relay_token"]
    sources: list[str] = []
    first_urls: list[str] = []
    for _round in range(MAXIMUM_ROUNDS):
        if answer["state"] != "pages_needed":
            break
        sources.append(answer["source"])
        first_urls.append(answer["page_requests"][0]["url"])
        responses = answer_like_the_desktop_app(answer["page_requests"])
        answer = client.post(
            RELAY_URL, json={"relay_token": relay_token, "responses": responses}, headers=headers
        ).json()
    return sources, first_urls, answer


def test_the_relay_reads_the_litters_then_the_directory_then_the_dogs_under_one_token(
    client: TestClient, db: Session, chained_relay_headers: dict[str, str]
) -> None:
    sources, first_urls, last_answer = relay_until_done(client, chained_relay_headers)

    statuses = {status["source"]: status for status in last_answer["source_statuses"]}
    assert last_answer["state"] == "run_finished"
    assert last_answer["source"] == "scc_dogs"
    assert list(dict.fromkeys(sources)) == ["centrale_canine", "scc_breeders", "scc_dogs"]
    assert "/chiots-de-la-race/0?" in first_urls[0]
    assert "/eleveurs/0?department=" in first_urls[sources.index("scc_breeders")]
    assert "/api/litter/" in first_urls[sources.index("scc_dogs")]
    assert statuses["centrale_canine"]["last_status"] == "ok"
    assert (statuses["scc_breeders"]["last_status"], statuses["scc_breeders"]["listings_seen"]) == ("ok", 3)
    assert statuses["scc_dogs"]["last_status"] == "ok"
    assert all(statuses[source]["is_collected_by_desktop_app"] for source in ("scc_breeders", "scc_dogs"))
    assert db.query(Breeder).filter(Breeder.scc_breeder_id == BREEDER_F_ID).count() == 1
    assert db.query(Dog).filter(Dog.external_id.in_([GOLD_FATHER_DOG_ID, *GOLD_PUPPY_IDS])).count() == 4


def test_nothing_is_due_right_after_a_full_relay_unless_asked(
    client: TestClient, db: Session, chained_relay_headers: dict[str, str]
) -> None:
    relay_until_done(client, chained_relay_headers)

    scheduled_answer = client.post(RELAY_URL, json={}, headers=chained_relay_headers).json()
    requested_answer = client.post(RELAY_URL, json={"is_requested_by_user": True}, headers=chained_relay_headers).json()

    assert scheduled_answer["state"] == "not_due"
    assert (requested_answer["state"], requested_answer["source"]) == ("pages_needed", "centrale_canine")


def test_a_relay_asked_by_the_user_reads_the_directory_again_even_when_recent(
    client: TestClient, db: Session, chained_relay_headers: dict[str, str]
) -> None:
    relay_until_done(client, chained_relay_headers)

    sources, _first_urls, last_answer = relay_until_done(client, chained_relay_headers, is_requested_by_user=True)

    assert last_answer["state"] == "run_finished"
    assert list(dict.fromkeys(sources)) == ["centrale_canine", "scc_breeders", "scc_dogs"]
