"""The Centrale Canine sites of the breedings: read for their photos, planned once a month, shown on the cards."""

from datetime import datetime, timedelta

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from enums.source_run_status import SourceRunStatus
from models.breeder import Breeder
from models.breeder_follow import BreederFollow
from models.user import User
from seeders.run_seeders import SeederRunner
from services.auth_service import AuthService
from services.collection_planner import CollectionPlanner
from services.collection_runner import collection_runner
from services.collectors.scc_sites import SccSiteCollectionPlan, SccSiteCollector, SccSiteTarget
from services.push_service import PushResult, PushService
from tests.centrale_canine_pages import EMPTY_PAGE, collector_serving, load_recorded_pages
from tests.scc_breeder_pages import BREEDER_A_ID, BREEDER_F_ID, BREEDER_G_ID, directory_collector_serving
from tests.scc_site_pages import (
    SITE_A_COVER_PATH,
    SITE_A_GALLERY_PATHS,
    SITE_A_SLUG,
    SITE_F_SLUG,
    SITE_G_SLUG,
    dogs_page,
    homepage_page,
    site_collector_serving,
)

SCC_HOST = "https://www.centrale-canine.fr"
PLANNING_NOW = datetime(2026, 11, 5, 9, 0)


@pytest.fixture
def directory_collected(db: Session, monkeypatch: pytest.MonkeyPatch) -> dict[str, str]:
    """Seed, collect the litters then the directory (pushes stubbed), and return the bearer header of the user."""
    monkeypatch.setattr(PushService, "send", lambda *_args, **_kwargs: PushResult(delivered=1))
    SeederRunner.run(db)
    collection_runner.run_centrale_canine(db, collector_serving(load_recorded_pages()))
    collection_runner.run_scc_breeders(db, directory_collector_serving())
    user = db.query(User).one()
    return {"Authorization": f"Bearer {AuthService.create_access_token(user.email)}"}


def breeder_of(db: Session, scc_breeder_id: str) -> Breeder:
    """A breeder of the directory, by its Centrale Canine identifier."""
    return db.query(Breeder).filter(Breeder.scc_breeder_id == scc_breeder_id).one()


def test_the_home_page_gives_the_cover_and_the_dogs_document_the_gallery() -> None:
    cover = SccSiteCollector.parse_cover(homepage_page("Élevage de test", SITE_A_COVER_PATH))
    no_cover = SccSiteCollector.parse_cover(homepage_page("Élevage de test", None))
    gallery = SccSiteCollector.parse_gallery(dogs_page((*SITE_A_GALLERY_PATHS, SITE_A_GALLERY_PATHS[0])))

    assert cover == f"{SCC_HOST}{SITE_A_COVER_PATH}"
    assert no_cover is None
    assert gallery == tuple(f"{SCC_HOST}{path}" for path in SITE_A_GALLERY_PATHS)


def test_a_page_not_relayed_yet_gives_nothing() -> None:
    assert SccSiteCollector.parse_cover(EMPTY_PAGE) is None
    assert SccSiteCollector.parse_gallery(EMPTY_PAGE) == ()


def test_the_collector_reads_the_home_page_then_the_dogs_document_and_reports_a_site_gone() -> None:
    requests: list[httpx.Request] = []
    plan = SccSiteCollectionPlan(
        sites=(SccSiteTarget(breeder_id=1, site_slug=SITE_A_SLUG), SccSiteTarget(breeder_id=2, site_slug=SITE_F_SLUG))
    )

    collection = site_collector_serving(requests).collect(plan)

    assert [request.url.path for request in requests] == [
        f"/{SITE_A_SLUG}/api/homepage",
        f"/{SITE_A_SLUG}/api/dogs",
        f"/{SITE_F_SLUG}/api/homepage",
    ]
    assert [(site.breeder_id, site.is_missing) for site in collection.sites] == [(1, False), (2, True)]
    assert collection.sites[0].cover_photo_url == f"{SCC_HOST}{SITE_A_COVER_PATH}"
    assert len(collection.sites[0].photo_urls) == 2
    assert collection.pages_read == 3


def test_the_planner_takes_the_sites_of_the_directory_breeders_the_followed_ones_first(
    db: Session, directory_collected: dict[str, str]
) -> None:
    breeder_g = breeder_of(db, BREEDER_G_ID)
    user = db.query(User).one()
    db.add(BreederFollow(user_id=user.id, breeder_id=breeder_g.id))
    db.commit()

    plan = CollectionPlanner.build_scc_sites_plan(db, PLANNING_NOW)

    assert plan.sites[0] == SccSiteTarget(breeder_id=breeder_g.id, site_slug=SITE_G_SLUG)
    assert {site.site_slug for site in plan.sites} == {SITE_A_SLUG, SITE_F_SLUG, SITE_G_SLUG}


def test_the_run_stores_the_photos_and_rests_the_sites_for_a_month(
    client: TestClient, db: Session, directory_collected: dict[str, str]
) -> None:
    breeder_a_id = breeder_of(db, BREEDER_A_ID).id

    report = collection_runner.run_scc_sites(db, site_collector_serving())
    db.expire_all()
    second_plan = CollectionPlanner.build_scc_sites_plan(db, datetime.now() + timedelta(hours=1))
    later_plan = CollectionPlanner.build_scc_sites_plan(db, datetime.now() + timedelta(days=31))
    detail = client.get(f"/api/v1/breeders/{breeder_a_id}", headers=directory_collected).json()
    cards = client.get("/api/v1/breeders", headers=directory_collected).json()

    breeder_a = db.get(Breeder, breeder_a_id)
    breeder_f = breeder_of(db, BREEDER_F_ID)
    assert report.source_run.status == SourceRunStatus.OK
    assert breeder_a is not None
    assert breeder_a.scc_site_cover_url == f"{SCC_HOST}{SITE_A_COVER_PATH}"
    assert breeder_a.scc_site_photos == [f"{SCC_HOST}{path}" for path in SITE_A_GALLERY_PATHS]
    assert breeder_a.scc_site_seen_at is not None
    assert (breeder_f.scc_site_cover_url, breeder_f.scc_site_seen_at is not None) == (None, True)
    assert second_plan.sites == ()
    assert {site.breeder_id for site in later_plan.sites} >= {breeder_a_id}
    assert detail["photo_url"] == f"{SCC_HOST}{SITE_A_COVER_PATH}"
    assert detail["photos"] == [f"{SCC_HOST}{path}" for path in SITE_A_GALLERY_PATHS]
    card_a = next(card for card in cards if card["id"] == breeder_a_id)
    assert card_a["photo_url"] == f"{SCC_HOST}{SITE_A_COVER_PATH}"


def test_a_litter_without_a_photo_shows_the_cover_of_its_breeding(
    client: TestClient, db: Session, directory_collected: dict[str, str]
) -> None:
    collection_runner.run_scc_sites(db, site_collector_serving())
    breeder_a_id = breeder_of(db, BREEDER_A_ID).id

    detail = client.get(f"/api/v1/breeders/{breeder_a_id}", headers=directory_collected).json()

    assert detail["litters"]
    assert all(litter["photo_url"] == f"{SCC_HOST}{SITE_A_COVER_PATH}" for litter in detail["litters"])
