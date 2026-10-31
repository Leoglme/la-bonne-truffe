"""The breeder directory of the Centrale Canine and the club list, read and stored."""

import httpx
import pytest
from sqlalchemy.orm import Session

from enums.listing_source import ListingSource
from enums.source_run_status import SourceRunStatus
from models.breeder import Breeder
from models.search_profile import SearchProfile
from seeders.run_seeders import SeederRunner
from services.collection_runner import collection_runner
from services.collectors.centrale_canine import SccDepartmentTarget
from services.collectors.scc_breeders import (
    SccBreederDirectoryCollector,
    SccBreederDirectoryPlan,
    SccDirectoryBreedTarget,
)
from services.push_service import PushResult, PushService
from tests.centrale_canine_pages import collector_serving, load_recorded_pages
from tests.scc_breeder_pages import (
    BREEDER_A_ID,
    BREEDER_F_ID,
    BREEDER_G_ID,
    breeder_a_entry,
    breeder_f_entry,
    breeder_g_entry,
    directory_collector_serving,
    directory_page,
    recorded_club_pages,
)


@pytest.fixture
def seeded_with_litters(db: Session, monkeypatch: pytest.MonkeyPatch) -> None:
    """Seed and collect the recorded litters once, so that Élevage A exists before the directory names it."""
    monkeypatch.setattr(PushService, "send", lambda *_args, **_kwargs: PushResult(delivered=1))
    SeederRunner.run(db)
    collection_runner.run_centrale_canine(db, collector_serving(load_recorded_pages()))


def test_a_directory_entry_becomes_a_profile_without_the_person_details() -> None:
    profile = SccBreederDirectoryCollector.parse_profile(breeder_a_entry(), is_from_club=False)

    assert profile is not None
    assert (profile.source_id, profile.scc_user_id) == (BREEDER_A_ID, "72101")
    assert (profile.affix, profile.display_name) == ("Du Clos de l'Élevage A", "Éleveuse de Test A")
    assert (profile.siren, profile.phone_e164, profile.zip_code) == ("000000001", "+33600000001", "35140")
    assert (profile.city, profile.department_code) == ("Saint-Aubin-du-Cormier", "35")
    assert (profile.latitude, profile.longitude) == (48.26, -1.4)
    assert profile.logo_url == "https://www.centrale-canine.fr/sites/default/files/logos/logo-a.jpg"
    assert profile.variety_ids == ("158", "159")
    assert profile.last_litter_at is not None
    assert profile.is_breed_club_member is False


def test_a_club_entry_is_a_member_whatever_the_page_says() -> None:
    profiles = SccBreederDirectoryCollector.parse_profiles(recorded_club_pages()[0], is_from_club=True)

    assert [profile.source_id for profile in profiles] == [BREEDER_G_ID, BREEDER_A_ID]
    assert all(profile.is_breed_club_member for profile in profiles)


def test_a_page_not_relayed_yet_holds_no_breeder() -> None:
    assert SccBreederDirectoryCollector.parse_profiles({"litters": {"count": 0, "node": []}}, False) == []


def test_the_run_reads_every_page_of_the_directory_then_the_club(db: Session, seeded_with_litters: None) -> None:
    requests: list[httpx.Request] = []

    report = collection_runner.run_scc_breeders(db, directory_collector_serving(requests))

    paths = [f"{request.url.path}?{request.url.query.decode()}" for request in requests]
    assert report.source_run.status == SourceRunStatus.OK
    assert report.source_run.source == ListingSource.SCC_BREEDERS
    assert sum(1 for path in paths if "/eleveurs/0?department=t_41" in path) == 1
    assert sum(1 for path in paths if "/eleveurs/1?department=t_41" in path) == 1
    assert sum(1 for path in paths if "/spaniel-club-francais/api/breeders/0?filter=1728" in path) == 1
    assert all(request.headers["User-Agent"].startswith("Mozilla/5.0") for request in requests)
    assert (report.source_run.listings_seen, report.source_run.listings_new) == (3, 2)


def test_the_directory_completes_a_known_breeder_and_creates_the_others(db: Session, seeded_with_litters: None) -> None:
    breeders_before = db.query(Breeder).count()

    collection_runner.run_scc_breeders(db, directory_collector_serving())

    breeder_a = db.query(Breeder).filter(Breeder.scc_breeder_id == BREEDER_A_ID).one()
    breeder_f = db.query(Breeder).filter(Breeder.scc_breeder_id == BREEDER_F_ID).one()
    breeder_g = db.query(Breeder).filter(Breeder.scc_breeder_id == BREEDER_G_ID).one()
    assert db.query(Breeder).count() == breeders_before + 2
    assert (breeder_a.scc_user_id, breeder_a.logo_url) == (
        "72101",
        "https://www.centrale-canine.fr/sites/default/files/logos/logo-a.jpg",
    )
    assert breeder_a.scc_variety_ids == ["158", "159"]
    assert breeder_a.is_breed_club_member is True
    assert breeder_a.scc_directory_seen_at is not None
    assert breeder_a.search_text is not None and "elevage a" in breeder_a.search_text
    assert (breeder_f.city, breeder_f.department_code, breeder_f.scc_last_litter_at) == ("Rennes", "35", None)
    assert (breeder_g.department_code, breeder_g.is_breed_club_member) == ("56", True)


def test_a_run_without_an_active_profile_fails_with_a_message(db: Session) -> None:
    SeederRunner.run(db)
    db.query(SearchProfile).update({SearchProfile.is_active: False})
    db.commit()

    report = collection_runner.run_scc_breeders(db, directory_collector_serving())

    assert report.source_run.status == SourceRunStatus.ERROR
    assert report.source_run.error_message is not None and "Rien à relever" in report.source_run.error_message


def test_the_collector_reads_as_many_pages_as_the_count_of_the_first_page_says() -> None:
    pages = [
        directory_page([breeder_a_entry()], 23),
        directory_page([breeder_f_entry()], 23),
        directory_page([breeder_g_entry()], 23),
        directory_page([breeder_g_entry()], 23),
    ]
    requests: list[httpx.Request] = []

    def answer(request: httpx.Request) -> httpx.Response:
        """Serve the page asked for."""
        requests.append(request)
        return httpx.Response(200, json=pages[int(request.url.path.rsplit("/", 1)[1])])

    collector = SccBreederDirectoryCollector(
        http_client=httpx.Client(transport=httpx.MockTransport(answer)), sleep=lambda _seconds: None
    )
    plan = SccBreederDirectoryPlan(
        breeds=(SccDirectoryBreedTarget(breed_id=1, scc_slug="cocker-spaniel-anglais"),),
        departments=(SccDepartmentTarget(code="35", scc_term_id="t_41"),),
    )

    collection = collector.collect(plan)

    assert [profile.source_id for profile in collection.profiles] == [BREEDER_A_ID, BREEDER_F_ID, BREEDER_G_ID]
    assert [request.url.path.rsplit("/", 1)[1] for request in requests] == ["0", "1", "2"]
