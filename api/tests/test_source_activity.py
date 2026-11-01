"""What runs now, for every device: a run asked by hand goes on in the background, the worker's runs show too."""

from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from core.clock import naive_utc_now
from enums.listing_source import ListingSource
from enums.source_run_status import SourceRunStatus
from models.source_run import SourceRun
from services.collection_runner import INTERRUPTED_RUN_MESSAGE, collection_runner
from services.source_run_launcher import source_run_launcher

ACTIVITY_URL = "/api/v1/sources/activity"


def test_a_run_asked_by_hand_answers_at_once_then_runs_in_the_background(
    client: TestClient, auth_headers: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    seen_while_running: list[list[ListingSource]] = []

    def run_without_network(run_db: Session, source: ListingSource) -> None:
        """Open and close a run line as the runner does, noting what every device sees in between."""
        source_run = SourceRun(source=source, started_at=naive_utc_now())
        run_db.add(source_run)
        run_db.commit()
        seen_while_running.append(source_run_launcher.running_sources(run_db, naive_utc_now()))
        source_run.status = SourceRunStatus.OK
        source_run.finished_at = naive_utc_now()
        run_db.commit()

    monkeypatch.setattr(collection_runner, "run_source", run_without_network)

    response = client.post("/api/v1/sources/chiens_de_france/run", headers=auth_headers)
    activity_after = client.get(ACTIVITY_URL, headers=auth_headers).json()
    statuses = {status["source"]: status for status in client.get("/api/v1/sources", headers=auth_headers).json()}

    assert response.status_code == 202
    assert response.json() == {"running_sources": ["chiens_de_france"], "relay": None}
    assert seen_while_running == [[ListingSource.CHIENS_DE_FRANCE]]
    assert activity_after == {"running_sources": [], "relay": None}
    assert statuses["chiens_de_france"]["last_status"] == "ok"


def test_a_source_the_worker_is_reading_is_not_run_twice(
    client: TestClient, db: Session, auth_headers: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    runs: list[ListingSource] = []
    monkeypatch.setattr(collection_runner, "run_source", lambda _db, source: runs.append(source))
    db.add(SourceRun(source=ListingSource.WHOOF, started_at=naive_utc_now() - timedelta(minutes=2)))
    db.commit()

    response = client.post("/api/v1/sources/whoof/run", headers=auth_headers)

    assert response.status_code == 202
    assert response.json()["running_sources"] == ["whoof"]
    assert runs == []


def test_a_run_left_running_for_hours_no_longer_shows_in_progress(
    client: TestClient, db: Session, auth_headers: dict[str, str]
) -> None:
    db.add(SourceRun(source=ListingSource.WHOOF, started_at=naive_utc_now() - timedelta(hours=3)))
    db.commit()

    assert client.get(ACTIVITY_URL, headers=auth_headers).json() == {"running_sources": [], "relay": None}


def test_the_worker_closes_at_start_the_runs_a_stopped_process_left_running(db: Session) -> None:
    started_at = datetime(2026, 11, 1, 9, 0)
    db.add_all(
        [
            SourceRun(source=ListingSource.WHOOF, started_at=started_at - timedelta(minutes=5)),
            SourceRun(
                source=ListingSource.COEUR_DE_COCKER,
                started_at=started_at - timedelta(hours=1),
                finished_at=started_at - timedelta(minutes=59),
                status=SourceRunStatus.OK,
            ),
        ]
    )
    db.commit()

    closed_count = collection_runner.close_interrupted_runs(db, started_at)

    interrupted = db.query(SourceRun).filter(SourceRun.source == ListingSource.WHOOF).one()
    finished = db.query(SourceRun).filter(SourceRun.source == ListingSource.COEUR_DE_COCKER).one()
    assert closed_count == 1
    assert (interrupted.status, interrupted.finished_at, interrupted.error_message) == (
        SourceRunStatus.ERROR,
        started_at,
        INTERRUPTED_RUN_MESSAGE,
    )
    assert finished.status == SourceRunStatus.OK
