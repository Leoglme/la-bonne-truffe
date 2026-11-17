"""The breedings the Centrale Canine lists without an address, placed by the regional lists of Chiens de France
(docs/02, « Les élevages qui cachent leur adresse »)."""

import copy
from collections.abc import Sequence
from dataclasses import replace
from datetime import datetime
from typing import Any

import httpx
import pytest
from sqlalchemy.orm import Session

from enums.match_flag import MatchFlag
from enums.match_tier import MatchTier
from models.breeder import Breeder
from models.breeder_site_directory_entry import BreederSiteDirectoryEntry
from models.listing import Listing
from models.listing_match import ListingMatch
from models.litter_group import LitterGroup
from models.user import User
from seeders.run_seeders import SeederRunner
from services import collection_runner as collection_runner_module
from services.breeder_site_ingestion import breeder_site_ingestion_service
from services.collection_planner import CollectionPlanner
from services.collection_runner import collection_runner
from services.collectors.centrale_canine import (
    ALL_DEPARTMENTS_FILTER,
    CentraleCanineCollector,
    HiddenAddressBreederPlace,
)
from services.collectors.raw_dog import RawSiteDirectoryEntry
from services.collectors.raw_listing import RawListing
from services.litter_query_service import LitterQueryService, LitterSort
from services.matching.snapshot_builder import LitterSnapshotBuilder
from tests.centrale_canine_pages import EMPTY_PAGE, RECORDED_DEPARTMENT_TERM_ID, load_recorded_pages, remove_litter
from tests.test_centrale_canine_collector import COCKER

HIDDEN_LITTER_ID = "4187829"
HIDDEN_BREEDER_USER_ID = "296109"
SEVEN_IN_PARIS = datetime(2026, 11, 16, 6, 5)
EIGHT_IN_PARIS = datetime(2026, 11, 16, 7, 5)
KER_DAZONT = HiddenAddressBreederPlace(
    affix_key="ker dazont", zip_code="22230", town="Merdrignac", department_code="22"
)
QUATRE_PATTES = HiddenAddressBreederPlace(
    affix_key="royaume quatre pattes", zip_code="77520", town=None, department_code="77"
)
PROFILE_DEPARTMENTS: frozenset[str] = frozenset({"35", "56", "22", "29", "44", "53", "49", "72", "85"})


def hide_the_address_of_the_breeder(pages: Sequence[dict[str, Any]]) -> None:
    """
    Make the breeder of the hidden litter one the Centrale Canine lists without any place, as « Elevage de Ker
    Dazont » is.

    Args:
        pages: Recorded pages, changed in place.
    """
    for page in pages:
        breeder = page["litters"]["breeders"].get(HIDDEN_BREEDER_USER_ID)
        if breeder is not None:
            breeder.update(
                {
                    "u_farming_affix": "ELEVAGE DE KER DAZONT",
                    "u_farming_name": "Confidentiel",
                    "u_breeder_zip_code": "",
                    "u_breeder_department": "",
                    "u_breeder_town": "",
                    "u_location": [],
                }
            )


def collector_of_france(pages_of_france: Sequence[dict[str, Any]]) -> CentraleCanineCollector:
    """
    A collector whose department pages do not show the hidden litter, while the pages of France do.

    Args:
        pages_of_france: Pages served for every department.

    Returns:
        The collector, without pause.
    """
    department_pages = copy.deepcopy(list(pages_of_france))
    remove_litter(department_pages, HIDDEN_LITTER_ID)

    def answer(request: httpx.Request) -> httpx.Response:
        """Serve the page asked for, like the real endpoint."""
        department = request.url.params.get("department")
        page_number = int(request.url.path.rsplit("/", 1)[1])
        pages = {RECORDED_DEPARTMENT_TERM_ID: department_pages, ALL_DEPARTMENTS_FILTER: pages_of_france}.get(
            department or "", []
        )
        return httpx.Response(200, json=pages[page_number] if page_number < len(pages) else EMPTY_PAGE)

    return CentraleCanineCollector(
        http_client=httpx.Client(transport=httpx.MockTransport(answer)), sleep=lambda _seconds: None
    )


def read_hidden_address_litters(
    pages: Sequence[dict[str, Any]], places: tuple[HiddenAddressBreederPlace, ...]
) -> list[RawListing]:
    """
    Read the recorded pages as pages of France, for the departments of the starting profile.

    Args:
        pages: Recorded pages.
        places: The places the regional lists give.

    Returns:
        The listings of the breedings that hide their address.
    """
    collector = CentraleCanineCollector()
    return [
        listing
        for page in pages
        for listing in collector.parse_hidden_address_litters(page, COCKER, places, PROFILE_DEPARTMENTS)
    ]


def test_a_breeding_hiding_its_address_takes_the_place_a_regional_list_gives_it_near_and_is_left_out_far() -> None:
    pages = load_recorded_pages()
    hide_the_address_of_the_breeder(pages)

    placed = read_hidden_address_litters(pages, (KER_DAZONT,))
    unplaced = read_hidden_address_litters(pages, (QUATRE_PATTES,))
    far = read_hidden_address_litters(pages, (replace(KER_DAZONT, zip_code="77520", department_code="77"),))

    assert [listing.external_id for listing in placed] == [HIDDEN_LITTER_ID]
    assert placed[0].department_code is None
    assert placed[0].breeder is not None
    assert (placed[0].breeder.affix, placed[0].breeder.display_name) == ("Elevage de Ker Dazont", None)
    assert (placed[0].breeder.zip_code, placed[0].breeder.city) == ("22230", "Merdrignac")
    assert [listing.external_id for listing in unplaced] == [HIDDEN_LITTER_ID]
    assert unplaced[0].breeder is not None
    assert (unplaced[0].breeder.zip_code, unplaced[0].breeder.city, unplaced[0].department_code) == (None, None, None)
    assert far == []


def test_two_places_bearing_the_same_affix_place_nothing() -> None:
    pages = load_recorded_pages()
    hide_the_address_of_the_breeder(pages)
    twin = replace(KER_DAZONT, zip_code="29000", town="Quimper", department_code="29")

    listings = read_hidden_address_litters(pages, (KER_DAZONT, twin))

    assert [listing.external_id for listing in listings] == [HIDDEN_LITTER_ID]
    assert listings[0].breeder is not None and listings[0].breeder.zip_code is None


def test_the_plan_places_the_breedings_of_every_region_at_their_hours_only(db: Session) -> None:
    SeederRunner.run(db)
    breeder_site_ingestion_service.keep_directory_entries(
        db,
        [
            RawSiteDirectoryEntry(
                "https://kerdazont.chiens-de-france.com", "Elevage De Ker Dazont", "22230", "Merdrignac"
            ),
            RawSiteDirectoryEntry("https://paris.chiens-de-france.com", "Du Royaume Des Quatre Pattes", "77520", None),
        ],
        SEVEN_IN_PARIS,
    )

    at_seven = CollectionPlanner.build_centrale_canine_plan(db, SEVEN_IN_PARIS)
    at_eight = CollectionPlanner.build_centrale_canine_plan(db, EIGHT_IN_PARIS)

    assert at_seven.reads_hidden_address_litters is True
    assert at_seven.hidden_address_breeder_places == (KER_DAZONT, QUATRE_PATTES)
    assert (at_eight.reads_hidden_address_litters, at_eight.hidden_address_breeder_places) == (False, ())
    assert db.query(BreederSiteDirectoryEntry).count() == 2


def test_the_litter_of_a_hidden_breeding_is_stored_kept_between_two_passes_and_retired_once_gone(
    db: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    SeederRunner.run(db)
    breeder_site_ingestion_service.keep_directory_entries(
        db,
        [
            RawSiteDirectoryEntry(
                "https://kerdazont.chiens-de-france.com", "Elevage De Ker Dazont", "22230", "Merdrignac"
            )
        ],
        SEVEN_IN_PARIS,
    )
    pages = load_recorded_pages()
    hide_the_address_of_the_breeder(pages)
    monkeypatch.setattr(collection_runner_module, "naive_utc_now", lambda: SEVEN_IN_PARIS)

    collection_runner.run_centrale_canine(db, collector_of_france(pages))

    listing = db.query(Listing).filter(Listing.external_id == HIDDEN_LITTER_ID).one()
    breeder = db.query(Breeder).filter(Breeder.id == listing.breeder_id).one()
    group = db.query(LitterGroup).filter(LitterGroup.id == listing.litter_group_id).one()
    snapshot = LitterSnapshotBuilder.build(db, group)
    assert (listing.department_code, listing.is_active) == (None, True)
    assert (breeder.zip_code, breeder.city, breeder.department_code) == ("22230", "Merdrignac", "22")
    assert snapshot is not None and snapshot.department_code == "22"

    monkeypatch.setattr(collection_runner_module, "naive_utc_now", lambda: EIGHT_IN_PARIS)
    for _run in range(2):
        collection_runner.run_centrale_canine(db, collector_of_france(pages))
    db.refresh(listing)
    assert listing.is_active is True

    remove_litter(pages, HIDDEN_LITTER_ID)
    monkeypatch.setattr(collection_runner_module, "naive_utc_now", lambda: SEVEN_IN_PARIS)
    for _run in range(2):
        collection_runner.run_centrale_canine(db, collector_of_france(pages))
    db.refresh(listing)
    assert listing.is_active is False


def test_a_litter_nothing_places_waits_apart_in_lieu_non_publie_and_never_in_the_home_list(
    db: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    SeederRunner.run(db)
    pages = load_recorded_pages()
    hide_the_address_of_the_breeder(pages)
    monkeypatch.setattr(collection_runner_module, "naive_utc_now", lambda: SEVEN_IN_PARIS)

    collection_runner.run_centrale_canine(db, collector_of_france(pages))

    listing = db.query(Listing).filter(Listing.external_id == HIDDEN_LITTER_ID).one()
    group = db.query(LitterGroup).filter(LitterGroup.id == listing.litter_group_id).one()
    snapshot = LitterSnapshotBuilder.build(db, group)
    match = db.query(ListingMatch).filter(ListingMatch.litter_group_id == group.id).one()
    user = db.query(User).order_by(User.id).first()
    assert user is not None
    home = LitterQueryService.list_cards(db, user.id, None, None, True, LitterSort.SCORE)
    apart = LitterQueryService.list_cards(db, user.id, None, None, True, LitterSort.SCORE, is_place_hidden=True)
    assert snapshot is not None and snapshot.is_place_hidden is True
    assert match.tier == MatchTier.EXCLUDED
    assert MatchFlag.PLACE_HIDDEN.value in match.flags
    assert group.id not in [card.id for card in home]
    assert [card.id for card in apart] == [group.id]
