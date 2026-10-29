"""Relay of the Centrale Canine by the desktop app, its curl played by the recorded pages."""

import json
from typing import Any

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from core.clock import naive_utc_now
from enums.listing_source import ListingSource
from enums.source_run_status import SourceRunStatus
from models.source_run import SourceRun
from models.user import User
from seeders.run_seeders import SeederRunner
from services.auth_service import AuthService
from services.centrale_canine_relay import CentraleCanineRelay
from services.collectors.centrale_canine import ALL_DEPARTMENTS_FILTER, SCC_BROWSER_USER_AGENT
from services.collectors.relayed_pages_transport import RelayedPagesTransport
from services.push_service import PushResult, PushService
from tests.centrale_canine_pages import EMPTY_PAGE, RECORDED_DEPARTMENT_TERM_ID, load_recorded_pages

RELAY_URL = "/api/v1/sources/centrale_canine/relay"
RELAY_REQUEST_URL = "/api/v1/sources/centrale_canine/relay-request"


@pytest.fixture
def relay_headers(db: Session, monkeypatch: pytest.MonkeyPatch) -> dict[str, str]:
    """
    Seed, let the desktop app relay the Centrale Canine (a fresh relay, pushes stubbed), and return the
    bearer header of the user.
    """
    monkeypatch.setattr(PushService, "send", lambda *_args, **_kwargs: PushResult(delivered=1))
    relayed_sources = frozenset({ListingSource.CENTRALE_CANINE})
    monkeypatch.setattr("api.v1.routes.sources.DESKTOP_RELAYED_SOURCES", relayed_sources)
    monkeypatch.setattr("services.source_status_service.DESKTOP_RELAYED_SOURCES", relayed_sources)
    monkeypatch.setattr("api.v1.routes.sources.centrale_canine_relay", CentraleCanineRelay())
    SeederRunner.run(db)
    user = db.query(User).one()
    return {"Authorization": f"Bearer {AuthService.create_access_token(user.email)}"}


def read_like_the_desktop_app(page_requests: list[dict[str, Any]], pages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Answer each page request as the curl of the desktop app would: the recorded pages for Ille-et-Vilaine,
    an empty page for any other department.

    Args:
        page_requests: Pages the API asked for.
        pages: Recorded pages, by page number.

    Returns:
        The relayed responses.
    """
    responses: list[dict[str, Any]] = []
    for page_request in page_requests:
        url = httpx.URL(page_request["url"])
        page_number = int(url.path.rsplit("/", 1)[1])
        is_recorded_department = url.params.get("department") in (RECORDED_DEPARTMENT_TERM_ID, ALL_DEPARTMENTS_FILTER)
        page = pages[page_number] if is_recorded_department and page_number < len(pages) else EMPTY_PAGE
        responses.append({"url": page_request["url"], "status_code": 200, "body": json.dumps(page)})
    return responses


def centrale_canine_status_of(answer: dict[str, Any]) -> dict[str, Any]:
    """The Centrale Canine status of an answer that ends a run."""
    return next(status for status in answer["source_statuses"] if status["source"] == "centrale_canine")


def test_a_relay_reads_the_pages_the_api_asks_for_then_runs(client: TestClient, relay_headers: dict[str, str]) -> None:
    pages = load_recorded_pages()

    first_answer = client.post(RELAY_URL, json={}, headers=relay_headers).json()
    relay_token = first_answer["relay_token"]
    responses = read_like_the_desktop_app(first_answer["page_requests"], pages)
    second_answer = client.post(
        RELAY_URL, json={"relay_token": relay_token, "responses": responses}, headers=relay_headers
    ).json()
    responses += read_like_the_desktop_app(second_answer["page_requests"], pages)
    last_answer = client.post(
        RELAY_URL, json={"relay_token": relay_token, "responses": responses}, headers=relay_headers
    ).json()

    assert first_answer["state"] == "pages_needed"
    assert len(first_answer["page_requests"]) == 9
    assert first_answer["page_requests"][0]["headers"]["User-Agent"] == SCC_BROWSER_USER_AGENT
    assert second_answer["state"] == "pages_needed"
    assert len(second_answer["page_requests"]) == 1
    assert f"/chiots-de-la-race/1?department={RECORDED_DEPARTMENT_TERM_ID}&" in second_answer["page_requests"][0]["url"]
    assert last_answer["state"] == "run_finished"
    assert centrale_canine_status_of(last_answer)["last_status"] == "ok"
    assert centrale_canine_status_of(last_answer)["listings_seen"] == 19
    assert centrale_canine_status_of(last_answer)["is_collected_by_desktop_app"] is True


def test_a_recent_run_is_not_due_unless_asked_from_the_sources_page(
    client: TestClient, relay_headers: dict[str, str], db: Session
) -> None:
    db.add(SourceRun(source=ListingSource.CENTRALE_CANINE, started_at=naive_utc_now(), status=SourceRunStatus.OK))
    db.commit()

    scheduled_answer = client.post(RELAY_URL, json={}, headers=relay_headers).json()
    requested_answer = client.post(RELAY_URL, json={"is_requested_by_user": True}, headers=relay_headers).json()

    assert scheduled_answer["state"] == "not_due"
    assert requested_answer["state"] == "pages_needed"


def test_a_run_asked_from_the_phone_starts_at_the_next_check_of_a_computer(
    client: TestClient, relay_headers: dict[str, str], db: Session
) -> None:
    db.add(SourceRun(source=ListingSource.CENTRALE_CANINE, started_at=naive_utc_now(), status=SourceRunStatus.OK))
    db.commit()

    request_response = client.post(RELAY_REQUEST_URL, headers=relay_headers)
    next_check_answer = client.post(RELAY_URL, json={}, headers=relay_headers).json()

    assert request_response.status_code == 204
    assert next_check_answer["state"] == "pages_needed"


def test_a_run_cannot_be_asked_when_the_server_reads_the_centrale_canine_itself(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.post(RELAY_REQUEST_URL, headers=auth_headers)

    assert response.status_code == 409


def test_a_second_computer_waits_while_the_first_one_relays(client: TestClient, relay_headers: dict[str, str]) -> None:
    first_computer_answer = client.post(RELAY_URL, json={}, headers=relay_headers).json()
    second_computer_answer = client.post(RELAY_URL, json={}, headers=relay_headers).json()

    assert first_computer_answer["state"] == "pages_needed"
    assert second_computer_answer["state"] == "busy"


def test_a_page_refused_on_the_computer_ends_in_a_failed_run(client: TestClient, relay_headers: dict[str, str]) -> None:
    first_answer = client.post(RELAY_URL, json={}, headers=relay_headers).json()
    refused_page = {
        "url": first_answer["page_requests"][0]["url"],
        "status_code": 403,
        "body": "<html>Just a moment...</html>",
        "cloudflare_mitigation": "challenge",
    }

    last_answer = client.post(
        RELAY_URL, json={"relay_token": first_answer["relay_token"], "responses": [refused_page]}, headers=relay_headers
    ).json()

    assert last_answer["state"] == "run_finished"
    assert centrale_canine_status_of(last_answer)["last_status"] == "error"
    assert "cf-mitigated=challenge" in centrale_canine_status_of(last_answer)["error_message"]


def test_an_expired_relay_token_is_refused(client: TestClient, relay_headers: dict[str, str]) -> None:
    response = client.post(RELAY_URL, json={"relay_token": "expired-token"}, headers=relay_headers)

    assert response.status_code == 409


def test_the_relay_is_refused_when_the_server_reads_the_centrale_canine_itself(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.post(RELAY_URL, json={}, headers=auth_headers)

    assert response.status_code == 409


def test_the_server_does_not_run_a_source_the_desktop_app_reads(
    client: TestClient, relay_headers: dict[str, str]
) -> None:
    response = client.post("/api/v1/sources/centrale_canine/run", headers=relay_headers)

    assert response.status_code == 409


def test_a_page_the_computer_did_not_read_fails_instead_of_looking_empty() -> None:
    request = httpx.Request(
        "GET", "https://www.centrale-canine.fr/api/breed/le-chien-de-race--cocker/chiots-de-la-race/0"
    )

    with pytest.raises(httpx.ConnectError):
        RelayedPagesTransport([]).handle_request(request)
