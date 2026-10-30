"""A Centrale Canine run end to end on the recorded pages: plan, identifiers, store, changes, disappearance."""

from datetime import date, datetime

import pytest
from sqlalchemy.orm import Session

from enums.notification_kind import NotificationKind
from models.breeder import Breeder
from models.department import Department
from models.listing import Listing
from models.listing_change import ListingChange
from models.litter_group import LitterGroup
from models.notification import Notification
from models.search_profile import SearchProfile
from models.source_run import SourceRun
from seeders.run_seeders import SeederRunner
from services.collection_planner import CollectionPlanner
from services.collection_runner import collection_runner
from services.push_service import PushResult, PushService
from tests.centrale_canine_pages import (
    collector_serving,
    declare_birth_under_new_id,
    litter_in,
    load_recorded_pages,
    mark_breed_club_member,
    refusing_collector,
    remove_litter,
    turn_gold,
)

BIRTH_ON_27_OCTOBER_2026 = 1793102400


def test_plan_reads_every_department_of_the_profile_in_its_order(db: Session) -> None:
    SeederRunner.run(db)

    plan = CollectionPlanner.build_centrale_canine_plan(db)

    assert [department.code for department in plan.departments] == [
        "35",
        "56",
        "22",
        "29",
        "44",
        "53",
        "49",
        "72",
        "85",
    ]
    assert plan.departments_without_term_id == ()
    assert [breed.scc_slug for breed in plan.breeds] == ["cocker-spaniel-anglais"]
    assert set(plan.breeds[0].varieties_by_source_id) == {"158", "159", "317"}


def test_first_run_stores_every_litter_and_its_breeder(db: Session) -> None:
    SeederRunner.run(db)

    report = collection_runner.run_centrale_canine(db, collector_serving(load_recorded_pages()))

    assert report.source_run.status == "ok"
    assert (report.source_run.listings_seen, report.source_run.listings_new) == (19, 19)
    born_gold = db.query(Listing).filter(Listing.external_id == "4236807").one()
    assert born_gold.colors == [{"color": "gold", "confidence": "certain"}]
    assert born_gold.department_code == "35"
    assert born_gold.published_at == datetime(2026, 6, 22, 8, 19, 52)
    assert born_gold.raw_json is not None and born_gold.raw_json["n_litter_number"] == "LOF-2026016223-2026-11"
    assert db.query(Breeder).count() == 5
    breeder = db.query(Breeder).filter(Breeder.scc_breeder_id == "379540").one()
    assert (breeder.affix, breeder.city, breeder.phone_e164) == (
        "Du Clos de l'Élevage B",
        "Saint-Aubin-du-Cormier",
        "+33600000002",
    )
    assert (breeder.latitude, breeder.longitude, breeder.scc_selection_group) == (48.26, -1.40, 2)
    assert breeder.is_breed_club_member is False
    assert db.query(Breeder).filter(Breeder.scc_breeder_id == "266172").one().siren == "000000001"


def test_a_breeder_who_leaves_the_breed_club_is_no_longer_a_member(db: Session) -> None:
    SeederRunner.run(db)
    pages_of_a_member = load_recorded_pages()
    mark_breed_club_member(pages_of_a_member, "4236807")
    collection_runner.run_centrale_canine(db, collector_serving(pages_of_a_member))
    breeder = db.query(Breeder).filter(Breeder.scc_breeder_id == "379540").one()
    assert breeder.is_breed_club_member is True

    collection_runner.run_centrale_canine(db, collector_serving(load_recorded_pages()))

    db.refresh(breeder)
    assert breeder.is_breed_club_member is False


def test_department_identifiers_are_read_when_a_profile_department_has_none(db: Session) -> None:
    SeederRunner.run(db)
    db.query(Department).filter(Department.code == "29").update({Department.scc_term_id: None})
    profile = db.query(SearchProfile).one()
    profile.department_codes = [*profile.department_codes, "05"]
    db.commit()

    report = collection_runner.run_centrale_canine(db, collector_serving(load_recorded_pages()))

    finistere = db.get(Department, "29")
    assert report.source_run.status == "ok"
    assert finistere is not None and finistere.scc_term_id == "t_35"
    assert "29" in [department.code for department in report.plan.departments]
    assert report.plan.departments_without_term_id == ("05",)


def test_birth_of_an_expected_litter_is_recorded_as_changes(db: Session) -> None:
    SeederRunner.run(db)
    collection_runner.run_centrale_canine(db, collector_serving(load_recorded_pages()))
    pages = load_recorded_pages()
    litter_in(pages, "4337070").update(
        {
            "n_is_borned": True,
            "n_birth_date": [BIRTH_ON_27_OCTOBER_2026],
            "n_male_number": [1],
            "n_female_number": [4],
            "n_litter_status": [2],
        }
    )

    report = collection_runner.run_centrale_canine(db, collector_serving(pages))

    listing = db.query(Listing).filter(Listing.external_id == "4337070").one()
    changed_fields = {change.field for change in db.query(ListingChange).filter(ListingChange.listing_id == listing.id)}
    assert report.source_run.listings_changed == 1
    assert listing.kind == "litter_born"
    assert listing.birth_date == date(2026, 10, 27)
    assert (listing.male_count, listing.female_count) == (1, 4)
    assert {"kind", "birth_date", "male_count", "female_count"} <= changed_fields
    assert listing.last_changed_at is not None


def test_birth_declared_under_a_new_identifier_joins_its_mating(db: Session, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(PushService, "send", lambda *_args, **_kwargs: PushResult(delivered=1))
    SeederRunner.run(db)
    pages = load_recorded_pages()
    turn_gold(pages, "4337070")
    collection_runner.run_centrale_canine(db, collector_serving(pages))
    declare_birth_under_new_id(pages, "4337070", "9990001", BIRTH_ON_27_OCTOBER_2026, male_count=1, female_count=4)

    report = collection_runner.run_centrale_canine(db, collector_serving(pages))

    mating = db.query(Listing).filter(Listing.external_id == "4337070").one()
    birth = db.query(Listing).filter(Listing.external_id == "9990001").one()
    group = db.get(LitterGroup, mating.litter_group_id) if mating.litter_group_id is not None else None
    assert (mating.mating_number, birth.mating_number) == ("2026032501", "2026032501")
    assert birth.litter_group_id == mating.litter_group_id
    assert report.grouping.born_group_ids == [mating.litter_group_id]
    assert group is not None and group.birth_date == date(2026, 10, 27)
    assert db.query(Notification).filter(Notification.kind == NotificationKind.BORN).count() == 1


def test_unchanged_run_records_nothing(db: Session) -> None:
    SeederRunner.run(db)
    collection_runner.run_centrale_canine(db, collector_serving(load_recorded_pages()))

    report = collection_runner.run_centrale_canine(db, collector_serving(load_recorded_pages()))

    assert (report.source_run.listings_new, report.source_run.listings_changed) == (0, 0)
    assert db.query(ListingChange).count() == 0


def test_litter_missing_from_two_runs_becomes_inactive(db: Session) -> None:
    SeederRunner.run(db)
    collection_runner.run_centrale_canine(db, collector_serving(load_recorded_pages()))
    pages_without_a_litter = load_recorded_pages()
    remove_litter(pages_without_a_litter, "4207567")

    collection_runner.run_centrale_canine(db, collector_serving(pages_without_a_litter))
    listing = db.query(Listing).filter(Listing.external_id == "4207567").one()
    assert (listing.is_active, listing.missed_run_count) == (True, 1)

    report = collection_runner.run_centrale_canine(db, collector_serving(pages_without_a_litter))
    db.refresh(listing)
    assert listing.is_active is False
    assert report.summary.deactivated_listing_ids == [listing.id]


def test_refused_run_is_recorded_as_an_error(db: Session) -> None:
    SeederRunner.run(db)

    report = collection_runner.run_centrale_canine(db, refusing_collector())

    run = db.query(SourceRun).one()
    assert report.source_run.status == "error"
    assert run.finished_at is not None
    assert "Cloudflare" in (run.error_message or "")
    assert db.query(Listing).count() == 0
