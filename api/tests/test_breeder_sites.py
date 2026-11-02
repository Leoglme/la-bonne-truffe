"""The breeders' sites on Chiens de France: found from the regional lists, read for their accounts and their
litters, a link pasted by hand, the dogs both sources know, and the migrations that read the colours again."""

from collections.abc import Callable
from datetime import datetime

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import Engine
from sqlalchemy.orm import Session

from enums.breeder_link_kind import BreederLinkKind
from enums.coat_color import CoatColor
from enums.dog_role import DogRole
from enums.dog_sex import DogSex
from enums.listing_kind import ListingKind
from enums.listing_source import ListingSource
from enums.puppy_ad_state import PuppyAdState
from enums.social_link_origin import SocialLinkOrigin
from enums.source_run_status import SourceRunStatus
from migrations import add_breeder_site_reading_columns, add_dog_parent_colors
from models.breeder import Breeder
from models.breeder_follow import BreederFollow
from models.department import Department
from models.dog import Dog
from models.listing import Listing
from models.litter_group import LitterGroup
from models.search_profile import SearchProfile
from models.source_run import SourceRun
from models.user import User
from seeders.run_seeders import SeederRunner
from services.auth_service import AuthService
from services.breeder_alert_service import BreederRunFacts, breeder_alert_service
from services.breeder_link_service import BreederLinkService
from services.breeder_site_ingestion import breeder_site_ingestion_service
from services.breeder_social_links import BreederSocialLinks
from services.collection_planner import CollectionPlanner
from services.collection_runner import collection_runner
from services.collectors.chiens_de_france import REGION_SLUGS
from services.collectors.polite_http_client import SourceReadError
from services.collectors.raw_dog import RawSiteDirectoryEntry
from services.dog_ingestion import DogIngestionService
from services.litter_query_service import LitterQueryService
from services.push_service import PushResult, PushService
from services.source_run_launcher import source_run_launcher
from tests.centrale_canine_pages import collector_serving, load_recorded_pages
from tests.chiens_de_france_site_pages import chiens_de_france_site_collector_serving

SITE_URL = "https://elevage-a.chiens-de-france.com"
BREEDERS_URL = "/api/v1/breeders"
SITE_FACEBOOK_URL = "https://www.facebook.com/elevage.a.test"
FOOTER_PAGE = """
<html><body><footer>
  <a href="https://www.facebook.com/sharer/sharer.php?u=ferme">Partager</a>
  <a href="https://facebook.com/ferme.des.tests">Facebook</a>
  <a href="https://instagram.com/ferme.des.tests">Instagram</a>
  <a href="https://youtube.com/@fermedestests">YouTube</a>
  <a href="https://www.ferme-des-tests.fr/contact">Contact</a>
</footer></body></html>
"""


@pytest.fixture
def seeded(db: Session, monkeypatch: pytest.MonkeyPatch) -> dict[str, str]:
    """Seed the reference data, the user and the starting profile (pushes stubbed); return the bearer header."""
    monkeypatch.setattr(PushService, "send", lambda *_args, **_kwargs: PushResult(delivered=1))
    SeederRunner.run(db)
    user = db.query(User).one()
    return {"Authorization": f"Bearer {AuthService.create_access_token(user.email)}"}


def ferme_des_tests(db: Session, **columns: object) -> Breeder:
    """A breeder of Liffré named as the regional list of the fixtures names it, without its affix."""
    breeder = Breeder(display_name="La Ferme des Tests", zip_code="35340", city="Liffré", department_code="35")
    for name, value in columns.items():
        setattr(breeder, name, value)
    db.add(breeder)
    db.commit()
    return breeder


def footer_reader(html: str) -> Callable[[str], str]:
    """A page reader that serves the same page whatever the address."""
    return lambda _address: html


def test_the_morning_run_gives_a_breeder_its_site_from_the_regional_list_then_reads_it(
    db: Session, seeded: dict[str, str]
) -> None:
    breeder = ferme_des_tests(db)
    namesake_elsewhere = Breeder(display_name="Du Clos de l'Élevage D", zip_code="56000", department_code="56")
    db.add(namesake_elsewhere)
    db.commit()

    report = collection_runner.run_breeder_sites(db, chiens_de_france_site_collector_serving())

    db.expire_all()
    assert report.linked_breeder_ids == [breeder.id]
    assert breeder.chiens_de_france_site_url == SITE_URL
    assert namesake_elsewhere.chiens_de_france_site_url is None
    assert (breeder.facebook_url, breeder.social_link_origins) == (SITE_FACEBOOK_URL, {"facebook": "breeder_site"})
    assert [litter["birth_date"] for litter in breeder.chiens_de_france_litters] == ["2026-08-28", "2026-07-19"]
    assert breeder.chiens_de_france_site_seen_at is not None
    assert len(report.collection.listings) == 6
    puppy_ad = db.query(Listing).filter(Listing.external_id == "chiot-2199888").one()
    assert puppy_ad.litter_group_id is not None
    user = db.query(User).one()
    detail = LitterQueryService.detail(db, user.id, puppy_ad.litter_group_id)
    assert detail.photos_added_at is not None
    assert {listing.puppy_state for listing in detail.listings} >= {PuppyAdState.AVAILABLE, PuppyAdState.RESERVED}


def test_a_site_read_for_the_first_time_records_its_breeders_alerts_without_sending_them(
    db: Session, seeded: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    never_read = ferme_des_tests(db, chiens_de_france_site_url=SITE_URL)
    already_read = Breeder(
        display_name="Du Clos de Test",
        chiens_de_france_site_url="https://elevage-b.chiens-de-france.com",
        chiens_de_france_site_seen_at=datetime(2026, 10, 31, 5, 40),
    )
    db.add(already_read)
    db.commit()
    raised_facts: list[BreederRunFacts] = []

    def record_facts(_db: Session, facts: BreederRunFacts, _now: datetime, should_notify: bool) -> int:
        """Keep the facts the run hands to the breeder alerts."""
        raised_facts.append(facts)
        return 0

    monkeypatch.setattr(breeder_alert_service, "raise_events", record_facts)

    collection_runner.run_breeder_sites(db, chiens_de_france_site_collector_serving())

    assert [facts.first_site_read_breeder_ids for facts in raised_facts] == [frozenset({never_read.id})]


def test_the_hourly_reading_reads_only_the_sites_of_the_followed_breeders(db: Session, seeded: dict[str, str]) -> None:
    followed = ferme_des_tests(db, chiens_de_france_site_url=SITE_URL)
    not_followed = Breeder(
        display_name="Du Clos de Test", chiens_de_france_site_url="https://elevage-b.chiens-de-france.com"
    )
    db.add(not_followed)
    db.add(BreederFollow(user_id=db.query(User).one().id, breeder_id=followed.id))
    db.commit()

    report = collection_runner.run_followed_breeder_sites(db, chiens_de_france_site_collector_serving())

    assert report is not None
    assert report.directory.raw_pages == []
    assert {site.breeder_id for site in report.plan.sites} == {followed.id}


def test_the_hourly_reading_waits_while_the_sites_are_read_and_without_a_followed_site(
    db: Session, seeded: dict[str, str]
) -> None:
    followed = ferme_des_tests(db)
    db.add(BreederFollow(user_id=db.query(User).one().id, breeder_id=followed.id))
    db.commit()
    without_followed_site = collection_runner.run_followed_breeder_sites(db, chiens_de_france_site_collector_serving())
    followed.chiens_de_france_site_url = SITE_URL
    db.add(SourceRun(source=ListingSource.CHIENS_DE_FRANCE_SITES, status=SourceRunStatus.RUNNING))
    db.commit()

    while_another_reading = collection_runner.run_followed_breeder_sites(db, chiens_de_france_site_collector_serving())

    assert (without_followed_site, while_another_reading) == (None, None)


def test_a_name_two_breeders_of_the_postal_code_bear_or_a_known_site_links_nothing(
    db: Session, seeded: dict[str, str]
) -> None:
    twins = [ferme_des_tests(db), ferme_des_tests(db, display_name=None, affix="La Ferme des Tests")]
    entry = RawSiteDirectoryEntry(SITE_URL, "Sarl La Ferme Des Tests", "35340", "Liffré")
    known_entry = RawSiteDirectoryEntry("https://elevage-b.chiens-de-france.com", "Du Clos de Test", "35340", None)
    ferme_des_tests(db, display_name="Du Clos de Test", chiens_de_france_site_url=known_entry.site_url)

    linked = breeder_site_ingestion_service.link_directory_sites(db, [entry, known_entry])

    assert linked == []
    assert [twin.chiens_de_france_site_url for twin in twins] == [None, None]


def test_an_affix_links_its_breeding_wherever_the_list_places_it_unless_two_breedings_bear_it(
    db: Session, seeded: dict[str, str]
) -> None:
    moved = ferme_des_tests(db, display_name="Martin Anne", affix="Des Landes de l'Élevage E", zip_code="22300")
    twins = [
        ferme_des_tests(db, display_name="Martin Paul", affix="Du Clos des Jumeaux", zip_code="56000"),
        ferme_des_tests(db, display_name="Martin Jean", affix="Du Clos des Jumeaux", zip_code="44000"),
    ]
    entry = RawSiteDirectoryEntry("https://elevage-e.chiens-de-france.com", "des landes de l'élevage E", "29870", None)
    twin_entry = RawSiteDirectoryEntry("https://jumeaux.chiens-de-france.com", "Du Clos Des Jumeaux", "35000", None)

    linked = breeder_site_ingestion_service.link_directory_sites(db, [entry, twin_entry])

    assert linked == [moved.id]
    assert moved.chiens_de_france_site_url == entry.site_url
    assert [twin.chiens_de_france_site_url for twin in twins] == [None, None]


def test_a_list_naming_a_person_links_the_breeder_of_that_name_in_the_postal_code(
    db: Session, seeded: dict[str, str]
) -> None:
    breeder = ferme_des_tests(db, display_name="Dupont Jean", affix="Elevage du Test", zip_code="72250")
    namesake_elsewhere = ferme_des_tests(db, display_name="Dupont Paul", zip_code="35000")
    entry = RawSiteDirectoryEntry("https://dupont-jean.chiens-de-france.com", "Mr Marc Dupont", "72250", None)
    kennel_entry = RawSiteDirectoryEntry("https://elevage-f.chiens-de-france.com", "Du Moulin du Test", "72250", None)

    linked = breeder_site_ingestion_service.link_directory_sites(db, [entry, kennel_entry])

    assert linked == [breeder.id]
    assert breeder.chiens_de_france_site_url == entry.site_url
    assert namesake_elsewhere.chiens_de_france_site_url is None


def test_the_regional_lists_of_provence_and_la_reunion_are_read_at_the_addresses_of_the_site(
    db: Session, seeded: dict[str, str]
) -> None:
    profile = db.query(SearchProfile).one()
    profile.department_codes = ["13", "974"]
    db.commit()

    plan = CollectionPlanner.build_site_directory_plan(db)

    assert plan.list_urls == (
        "https://www.chiens-de-france.com/eleveurs/cocker-spaniel-anglais/france/provence-alpes-cote-dazur",
        "https://www.chiens-de-france.com/eleveurs/cocker-spaniel-anglais/france/reunion",
    )
    assert {department.region for department in db.query(Department)} <= set(REGION_SLUGS)


def test_an_account_found_on_a_site_never_replaces_one_declared_or_added_by_hand() -> None:
    breeder = Breeder(
        facebook_url="https://www.facebook.com/declared", social_link_origins={"facebook": "centrale_canine"}
    )

    from_site = BreederSocialLinks.keep(
        breeder, "facebook", "https://www.facebook.com/site", SocialLinkOrigin.BREEDER_SITE
    )
    by_hand = BreederSocialLinks.keep(
        breeder, "facebook", "https://www.facebook.com/hand", SocialLinkOrigin.ADDED_BY_HAND
    )
    from_scc = BreederSocialLinks.keep(
        breeder, "facebook", "https://www.facebook.com/declared", SocialLinkOrigin.CENTRALE_CANINE
    )

    assert (from_site, by_hand, from_scc) == (False, True, False)
    assert (breeder.facebook_url, breeder.social_link_origins) == (
        "https://www.facebook.com/hand",
        {"facebook": "added_by_hand"},
    )


def test_a_pasted_link_is_recognised_as_a_site_an_account_or_another_site() -> None:
    service = BreederLinkService(page_reader=footer_reader(FOOTER_PAGE))

    site = service.read("elevage-a.chiens-de-france.com/cocker-spaniel-anglais/chiots")
    facebook = service.read("https://www.facebook.com/elevage.a.test")
    other_site = service.read("www.ferme-des-tests.fr")

    assert (site.kind, site.address) == (BreederLinkKind.CHIENS_DE_FRANCE_SITE, SITE_URL)
    assert (facebook.kind, facebook.address) == (BreederLinkKind.FACEBOOK, SITE_FACEBOOK_URL)
    assert (other_site.kind, other_site.address, other_site.is_page_read) == (
        BreederLinkKind.WEBSITE,
        "https://www.ferme-des-tests.fr",
        True,
    )
    assert other_site.social_accounts == {
        "facebook": "https://facebook.com/ferme.des.tests",
        "instagram": "https://instagram.com/ferme.des.tests",
        "youtube": "https://youtube.com/@fermedestests",
    }


def test_a_site_that_cannot_be_read_is_kept_without_accounts_and_a_text_without_host_is_refused() -> None:
    def refuse(_address: str) -> str:
        """A site that answers nothing."""
        raise SourceReadError("refusé")

    service = BreederLinkService(page_reader=refuse)

    reading = service.read("https://www.ferme-des-tests.fr")

    assert (reading.kind, reading.social_accounts, reading.is_page_read) == (BreederLinkKind.WEBSITE, {}, False)
    with pytest.raises(HTTPException) as refused:
        service.read("pas une adresse")
    assert refused.value.status_code == 422


def test_another_site_becomes_the_website_and_gives_the_accounts_it_links(db: Session, seeded: dict[str, str]) -> None:
    breeder = ferme_des_tests(db, facebook_url="https://www.facebook.com/declared")
    breeder.social_link_origins = {"facebook": "centrale_canine"}
    db.commit()

    BreederLinkService(page_reader=footer_reader(FOOTER_PAGE)).add(db, breeder.id, "www.ferme-des-tests.fr")

    db.expire_all()
    assert breeder.website == "https://www.ferme-des-tests.fr"
    assert breeder.facebook_url == "https://www.facebook.com/declared"
    assert breeder.instagram_url == "https://instagram.com/ferme.des.tests"
    assert breeder.social_link_origins == {
        "facebook": "centrale_canine",
        "instagram": "breeder_site",
        "youtube": "breeder_site",
    }


def test_the_routes_preview_then_add_a_pasted_site_and_read_it_at_once(
    client: TestClient, db: Session, seeded: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    breeder = ferme_des_tests(db)
    reads: list[int] = []
    monkeypatch.setattr(source_run_launcher, "launched_sources", set())
    monkeypatch.setattr(
        source_run_launcher,
        "read_breeder_site",
        lambda _session_factory, breeder_id: reads.append(breeder_id),
    )
    pasted = {"url": "elevage-a.chiens-de-france.com/cocker-spaniel-anglais"}

    preview = client.post(f"{BREEDERS_URL}/{breeder.id}/links/preview", json=pasted, headers=seeded).json()
    detail = client.post(f"{BREEDERS_URL}/{breeder.id}/links", json=pasted, headers=seeded).json()
    facebook = client.post(f"{BREEDERS_URL}/{breeder.id}/links", json={"url": SITE_FACEBOOK_URL}, headers=seeded).json()

    assert preview == {
        "kind": "chiens_de_france_site",
        "address": SITE_URL,
        "social_accounts": [],
        "is_page_read": False,
    }
    assert detail["chiens_de_france_site_url"] == SITE_URL
    assert reads == [breeder.id]
    assert (facebook["facebook_url"], facebook["social_link_origins"]) == (
        SITE_FACEBOOK_URL,
        {"facebook": "added_by_hand"},
    )


def test_the_detail_shows_a_dog_both_sources_know_once_and_the_gold_litters_only_its_site_lists(
    client: TestClient, db: Session, seeded: dict[str, str]
) -> None:
    breeder = ferme_des_tests(
        db,
        chiens_de_france_site_url=SITE_URL,
        chiens_de_france_litters=[{"birth_date": "2026-08-28", "sire_name": "Père Gold", "dam_name": "Mère Gold"}],
    )
    site_photo = f"{SITE_URL}/media_cdf/photos/chiens/photo-de-test-3.png"
    db.add_all(
        [
            Dog(
                source=ListingSource.CENTRALE_CANINE,
                external_id="7000201",
                role=DogRole.PARENT,
                breeder_id=breeder.id,
                full_name="MÈRE DE TEST",
                sex=DogSex.FEMALE,
                identifier="250000000000003",
                color_code="Noi. Mar.Fau. Pan.Bla.",
                color=CoatColor.TRICOLORE,
                rating=1,
                health_codes=["LocEm-Em/e"],
            ),
            Dog(
                source=ListingSource.CHIENS_DE_FRANCE,
                external_id="1212400",
                role=DogRole.REPRODUCER,
                breeder_id=breeder.id,
                full_name="Mère de test Du Clos de Test",
                sex=DogSex.FEMALE,
                identifier="250 000 000 000 003",
                photos=[site_photo],
            ),
            Dog(
                source=ListingSource.CHIENS_DE_FRANCE,
                external_id="1430047",
                role=DogRole.REPRODUCER,
                breeder_id=breeder.id,
                full_name="Père Gold",
                sex=DogSex.MALE,
                color_code="GOLDEN",
                color=CoatColor.GOLD,
            ),
            Dog(
                source=ListingSource.CHIENS_DE_FRANCE,
                external_id="1386355",
                role=DogRole.REPRODUCER,
                breeder_id=breeder.id,
                full_name="Mère Gold",
                sex=DogSex.FEMALE,
                color_code="GOLDEN",
                color=CoatColor.GOLD,
            ),
        ]
    )
    db.commit()

    detail = client.get(f"{BREEDERS_URL}/{breeder.id}", headers=seeded).json()

    assert [dog["full_name"] for dog in detail["reproducers"]] == [
        "Mère de test Du Clos de Test",
        "Mère Gold",
        "Père Gold",
    ]
    merged = detail["reproducers"][0]
    assert (merged["photos"], merged["rating"], merged["color"], merged["e_locus"]) == (
        [site_photo],
        1,
        "tricolore",
        "E/e",
    )
    assert detail["site_litters"] == [{"birth_date": "2026-08-28", "sire_name": "Père Gold", "dam_name": "Mère Gold"}]
    assert detail["site_litters_url"] == f"{SITE_URL}/cocker-spaniel-anglais/chiots-vendus"
    assert detail["site_dogs_url"] == f"{SITE_URL}/cocker-spaniel-anglais"
    assert detail["color_shares"] == [{"color": "gold", "litters_count": 1}]


def test_the_puppy_of_an_ad_is_told_available_reserved_or_sold() -> None:
    def puppy_ad(status_text: str, puppies_available: int | None) -> Listing:
        """A puppy ad of a breeder's site with its status line."""
        return Listing(kind=ListingKind.PUPPY_AD, raw_json={"status": status_text}, puppies_available=puppies_available)

    assert LitterQueryService._puppy_state(puppy_ad("Mâle disponible à la vente à 1400 €", 1)) == PuppyAdState.AVAILABLE
    assert LitterQueryService._puppy_state(puppy_ad("Femelle réservée", 0)) == PuppyAdState.RESERVED
    assert LitterQueryService._puppy_state(puppy_ad("Mâle vendu", 0)) == PuppyAdState.SOLD
    assert LitterQueryService._puppy_state(Listing(kind=ListingKind.LITTER_BORN, raw_json={})) is None


def test_the_dog_migration_reads_the_colours_again_and_plans_the_parents(db: Session, engine: Engine) -> None:
    read_at = datetime(2026, 10, 31, 8, 0)
    parent = Dog(
        source=ListingSource.CENTRALE_CANINE,
        external_id="7000301",
        role=DogRole.PARENT,
        color_code="Noi. Mar.Fau. Pan.Bla.Gri.",
        color=CoatColor.NOIR_ET_FEU,
        health_codes=["PRCD-1.2", "LocEm-Em/e"],
        fetched_at=read_at,
    )
    site_dog = Dog(
        source=ListingSource.CHIENS_DE_FRANCE,
        external_id="1999002",
        role=DogRole.REPRODUCER,
        color_code="GOLDEN",
        color=CoatColor.GOLD,
        fetched_at=read_at,
    )
    db.add_all([parent, site_dog])
    db.commit()

    add_dog_parent_colors.run_migration(engine)

    db.expire_all()
    assert (parent.color, parent.e_locus, parent.fetched_at) == (CoatColor.TRICOLORE, "E/e", None)
    assert (site_dog.color, site_dog.fetched_at) == (CoatColor.GOLD, read_at)


def test_the_breeder_migration_marks_the_known_accounts_as_declared_at_the_centrale_canine(
    db: Session, engine: Engine
) -> None:
    breeder = Breeder(display_name="Élevage de test", facebook_url="https://www.facebook.com/elevage.test")
    without_account = Breeder(display_name="Élevage sans compte")
    db.add_all([breeder, without_account])
    db.commit()

    add_breeder_site_reading_columns.run_migration(engine)

    db.expire_all()
    assert breeder.social_link_origins == {"facebook": "centrale_canine"}
    assert without_account.social_link_origins == {}


def test_the_litter_shows_its_father_with_his_site_photo_and_one_gold_puppy_in_two(
    client: TestClient, db: Session, seeded: dict[str, str]
) -> None:
    collection_runner.run_centrale_canine(db, collector_serving(load_recorded_pages()))
    group = db.query(LitterGroup).order_by(LitterGroup.id).first()
    assert group is not None
    site_photo = f"{SITE_URL}/media_cdf/photos/chiens/photo-de-test-9.jpg"
    sire = Dog(
        source=ListingSource.CENTRALE_CANINE,
        external_id="7000401",
        role=DogRole.PARENT,
        full_name="PÈRE GOLD DE TEST",
        color_code="F.Or.",
        color=CoatColor.GOLD,
        identifier="250000000000101",
    )
    dam = Dog(
        source=ListingSource.CENTRALE_CANINE,
        external_id="7000402",
        role=DogRole.PARENT,
        full_name="MÈRE TRICOLORE DE TEST",
        color_code="Noi. Mar.Fau. Pan.Bla.",
        color=CoatColor.TRICOLORE,
        sire_color_code="Fau. Pan.Bla.Rou.",
    )
    site_sire = Dog(
        source=ListingSource.CHIENS_DE_FRANCE,
        external_id="1999101",
        role=DogRole.REPRODUCER,
        identifier="250 000 000 000 101",
        photos=[site_photo],
    )
    db.add_all([sire, dam, site_sire])
    db.flush()
    group.sire_dog_id, group.dam_dog_id = sire.id, dam.id
    DogIngestionService.refresh_expected_colors(db, group)
    db.commit()

    detail = client.get(f"/api/v1/litters/{group.id}", headers=seeded).json()

    assert detail["sire"]["photo_url"] == site_photo
    assert detail["dam"]["photo_url"] is None
    assert (detail["dam"]["color"], detail["dam"]["carries_gold_by_parents"]) == ("tricolore", True)
    assert detail["gold_puppy_odds"] == 0.5
    assert detail["expected_colors"][0]["puppy_odds"] == 0.5
