"""A Centrale Canine run end to end: plan, collect, store, change history, disappearance."""

import copy
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import httpx
from sqlalchemy.orm import Session

from models.breeder import Breeder
from models.listing import Listing
from models.listing_change import ListingChange
from models.source_run import SourceRun
from seeders.run_seeders import SeederRunner
from services.collection_planner import CollectionPlanner
from services.collection_runner import collection_runner
from services.collectors.centrale_canine import CentraleCanineCollector

FIXTURE = Path(__file__).parent / "fixtures" / "centrale_canine" / "litters_35_page_0.json"


def load_page() -> dict[str, Any]:
    """The synthetic page of the fixtures."""
    page: dict[str, Any] = json.loads(FIXTURE.read_text(encoding="utf-8"))
    return page


def collector_serving(page_for_request: Callable[[], dict[str, Any]]) -> CentraleCanineCollector:
    """A collector whose every request gets the given page, without waiting."""
    return CentraleCanineCollector(
        http_client=httpx.Client(
            transport=httpx.MockTransport(lambda _request: httpx.Response(200, json=page_for_request()))
        ),
        sleep=lambda _seconds: None,
    )


def test_plan_reads_only_departments_with_a_known_identifier(db: Session) -> None:
    SeederRunner.run(db)

    plan = CollectionPlanner.build_centrale_canine_plan(db)

    assert [department.code for department in plan.departments] == ["35"]
    assert plan.departments_without_term_id == ("56", "22", "29", "44", "53", "49", "72", "85")
    assert [breed.scc_slug for breed in plan.breeds] == ["cocker-spaniel-anglais"]
    assert set(plan.breeds[0].varieties_by_source_id) == {"317", "159"}


def test_first_run_stores_every_litter_and_its_breeder(db: Session) -> None:
    SeederRunner.run(db)

    report = collection_runner.run_centrale_canine(db, collector_serving(load_page))

    assert report.source_run.status == "ok"
    assert (report.source_run.listings_seen, report.source_run.listings_new) == (4, 4)
    born_gold = db.query(Listing).filter(Listing.external_id == "9000001").one()
    assert born_gold.colors == [{"color": "gold", "confidence": "certain"}]
    assert born_gold.department_code == "35"
    assert born_gold.raw_json is not None and born_gold.raw_json["n_litter_number"] == "LOF-TEST-0001"
    assert db.query(Breeder).count() == 3
    assert db.query(Breeder).filter(Breeder.scc_breeder_id == "7000001").one().scc_selection_group == 1


def test_birth_of_an_expected_litter_is_recorded_as_changes(db: Session) -> None:
    SeederRunner.run(db)
    collection_runner.run_centrale_canine(db, collector_serving(load_page))
    born_page = load_page()
    expected_litter = born_page["litters"]["node"]["2"]["n9000002"]
    expected_litter.update({"n_is_borned": True, "n_birth_date": 1795046400, "n_male_number": 1, "n_female_number": 4})

    report = collection_runner.run_centrale_canine(db, collector_serving(lambda: born_page))

    listing = db.query(Listing).filter(Listing.external_id == "9000002").one()
    changed_fields = {change.field for change in db.query(ListingChange).filter(ListingChange.listing_id == listing.id)}
    assert report.source_run.listings_changed == 1
    assert listing.kind == "litter_born"
    assert (listing.male_count, listing.female_count) == (1, 4)
    assert {"kind", "birth_date", "male_count", "female_count"} <= changed_fields
    assert listing.last_changed_at is not None


def test_unchanged_run_records_nothing(db: Session) -> None:
    SeederRunner.run(db)
    collection_runner.run_centrale_canine(db, collector_serving(load_page))

    report = collection_runner.run_centrale_canine(db, collector_serving(load_page))

    assert (report.source_run.listings_new, report.source_run.listings_changed) == (0, 0)
    assert db.query(ListingChange).count() == 0


def test_litter_missing_from_two_runs_becomes_inactive(db: Session) -> None:
    SeederRunner.run(db)
    collection_runner.run_centrale_canine(db, collector_serving(load_page))
    page_without_last_litter = copy.deepcopy(load_page())
    del page_without_last_litter["litters"]["node"]["3"]

    collection_runner.run_centrale_canine(db, collector_serving(lambda: page_without_last_litter))
    listing = db.query(Listing).filter(Listing.external_id == "9000004").one()
    assert (listing.is_active, listing.missed_run_count) == (True, 1)

    report = collection_runner.run_centrale_canine(db, collector_serving(lambda: page_without_last_litter))
    db.refresh(listing)
    assert listing.is_active is False
    assert report.summary.deactivated_listing_ids == [listing.id]


def test_refused_run_is_recorded_as_an_error(db: Session) -> None:
    SeederRunner.run(db)
    collector = CentraleCanineCollector(
        http_client=httpx.Client(
            transport=httpx.MockTransport(lambda _request: httpx.Response(403, headers={"cf-mitigated": "challenge"}))
        )
    )

    report = collection_runner.run_centrale_canine(db, collector)

    run = db.query(SourceRun).one()
    assert report.source_run.status == "error"
    assert run.finished_at is not None
    assert "Cloudflare" in (run.error_message or "")
    assert db.query(Listing).count() == 0
