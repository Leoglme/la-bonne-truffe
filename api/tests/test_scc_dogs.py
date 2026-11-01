"""The litter and dog pages of the Centrale Canine: read, stored, and used by the matching and the detail."""

from datetime import datetime

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from enums.coat_color import CoatColor
from enums.dog_role import DogRole
from enums.dog_sex import DogSex
from enums.source_run_status import SourceRunStatus
from models.dog import Dog
from models.follow_up import FollowUp
from models.listing import Listing
from models.litter_group import LitterGroup
from models.user import User
from seeders.run_seeders import SeederRunner
from services.auth_service import AuthService
from services.collection_runner import collection_runner
from services.collectors.scc_dogs import SccDogCollectionPlan, SccDogCollector, SccLitterTarget
from services.dog_collection_planner import DogCollectionPlanner
from services.push_service import PushResult, PushService
from tests.centrale_canine_pages import collector_serving, load_recorded_pages
from tests.scc_dog_pages import (
    BUNDLE_FATHER_DOG_ID,
    BUNDLE_LITTER_SCC_ID,
    GOLD_FATHER_DOG_ID,
    GOLD_LITTER_SCC_ID,
    GOLD_MOTHER_DOG_ID,
    GOLD_PUPPY_IDS,
    dog_collector_serving,
    dog_page,
    recorded_litter_pages,
)

GOLD_LITTER_ID = "4333817"
BUNDLE_LITTER_ID = "4320577"
EXPECTED_LITTER_ID = "4337070"
PLANNING_NOW = datetime(2026, 11, 5, 9, 0)


@pytest.fixture
def collected(db: Session, monkeypatch: pytest.MonkeyPatch) -> dict[str, str]:
    """Seed, collect the recorded litters once (pushes stubbed), and return the bearer header of the user."""
    monkeypatch.setattr(PushService, "send", lambda *_args, **_kwargs: PushResult(delivered=1))
    SeederRunner.run(db)
    collection_runner.run_centrale_canine(db, collector_serving(load_recorded_pages()))
    user = db.query(User).one()
    return {"Authorization": f"Bearer {AuthService.create_access_token(user.email)}"}


def group_of(db: Session, external_id: str) -> LitterGroup:
    """The litter group of a recorded listing."""
    listing = db.query(Listing).filter(Listing.external_id == external_id).one()
    group = db.get(LitterGroup, listing.litter_group_id)
    assert group is not None
    return group


def test_a_litter_page_names_the_parents_by_their_dog_identifier_and_lists_the_puppies() -> None:
    target = SccLitterTarget(group_id=1, scc_litter_id=GOLD_LITTER_SCC_ID, read_parents=True, read_puppies=True)

    detail = SccDogCollector.parse_litter_detail(recorded_litter_pages()[GOLD_LITTER_SCC_ID], target)

    assert detail is not None
    assert (detail.sire_dog_id, detail.dam_dog_id) == (GOLD_FATHER_DOG_ID, GOLD_MOTHER_DOG_ID)
    assert [(puppy.dog_id, puppy.name, puppy.sex) for puppy in detail.puppies] == [
        (GOLD_PUPPY_IDS[0], "Balti", DogSex.MALE),
        (GOLD_PUPPY_IDS[1], "Bella", DogSex.FEMALE),
        (GOLD_PUPPY_IDS[2], "Bonnie", DogSex.FEMALE),
    ]


def test_a_page_not_relayed_yet_holds_no_litter_nor_dog() -> None:
    target = SccLitterTarget(group_id=1, scc_litter_id=GOLD_LITTER_SCC_ID, read_parents=True, read_puppies=True)
    placeholder = {"litters": {"count": 0, "node": []}}

    assert SccDogCollector.parse_litter_detail(placeholder, target) is None
    assert SccDogCollector.parse_dog(placeholder, DogRole.PARENT, 1) is None


def test_a_dog_page_gives_the_colour_the_locus_and_the_tests_but_never_the_owner() -> None:
    page = dog_page("7000009", "PÈRE GOLD", True, "F.Or.", ["FN-1.1", "LocE-e/e"], "4", sire_id="1", dam_id="2")

    dog = SccDogCollector.parse_dog(page, DogRole.PARENT, 1)

    assert dog is not None
    assert (dog.external_id, dog.name, dog.affix, dog.full_name) == (
        "7000009",
        "Père Gold",
        "Du Clos de Test",
        "Père Gold du Clos de Test",
    )
    assert (dog.sex, dog.birth_date.isoformat() if dog.birth_date else None) == (DogSex.MALE, "2026-07-05")
    assert (dog.color_code, dog.color, dog.e_locus, dog.rating) == ("F.Or.", CoatColor.GOLD, "e/e", 4)
    assert dog.health_codes == ("FN-1.1", "LocE-e/e")
    assert (dog.sire_external_id, dog.dam_external_id, dog.has_dna_profile) == ("1", "2", True)
    assert (dog.sire_color_code, dog.dam_color_code) == ("F.Or.", "F.Cl.")
    assert dog.litter_group_id is None


def test_the_collector_reads_the_litter_then_its_dogs_within_the_budget() -> None:
    requests: list[httpx.Request] = []
    target = SccLitterTarget(group_id=1, scc_litter_id=GOLD_LITTER_SCC_ID, read_parents=True, read_puppies=True)

    full = dog_collector_serving(requests).collect(SccDogCollectionPlan(litters=(target,), page_budget=60))
    requests.clear()
    short = dog_collector_serving(requests).collect(SccDogCollectionPlan(litters=(target,), page_budget=3))

    assert full.pages_read == 6
    assert [dog.role for dog in full.dogs] == [
        DogRole.PARENT,
        DogRole.PARENT,
        DogRole.PUPPY,
        DogRole.PUPPY,
        DogRole.PUPPY,
    ]
    assert short.pages_read == 3
    assert [dog.external_id for dog in short.dogs] == [GOLD_FATHER_DOG_ID, GOLD_MOTHER_DOG_ID]
    assert [request.url.path for request in requests] == [
        f"/api/litter/{GOLD_LITTER_SCC_ID}",
        f"/api/dog/{GOLD_FATHER_DOG_ID}",
        f"/api/dog/{GOLD_MOTHER_DOG_ID}",
    ]


def test_a_fresh_parent_is_not_read_again() -> None:
    requests: list[httpx.Request] = []
    target = SccLitterTarget(
        group_id=1,
        scc_litter_id=GOLD_LITTER_SCC_ID,
        read_parents=True,
        read_puppies=False,
        fresh_dog_ids=frozenset({GOLD_FATHER_DOG_ID}),
    )

    dog_collector_serving(requests).collect(SccDogCollectionPlan(litters=(target,), page_budget=60))

    assert [request.url.path for request in requests] == [
        f"/api/litter/{GOLD_LITTER_SCC_ID}",
        f"/api/dog/{GOLD_MOTHER_DOG_ID}",
    ]


def test_the_planner_puts_the_followed_litters_first_and_skips_the_up_to_date_ones(
    db: Session, collected: dict[str, str]
) -> None:
    bundle_group = group_of(db, BUNDLE_LITTER_ID)
    user = db.query(User).one()
    db.add(FollowUp(user_id=user.id, litter_group_id=bundle_group.id))
    db.commit()

    plan = DogCollectionPlanner.build(db, PLANNING_NOW)

    assert plan.litters[0].scc_litter_id == BUNDLE_LITTER_SCC_ID
    assert plan.litters[0].read_parents is True
    assert plan.litters[0].read_puppies is True
    assert {target.scc_litter_id for target in plan.litters} >= {GOLD_LITTER_SCC_ID, BUNDLE_LITTER_SCC_ID}


def test_the_run_ties_the_parents_and_the_puppies_and_settles_the_colours(
    client: TestClient, db: Session, collected: dict[str, str]
) -> None:
    gold_group = group_of(db, GOLD_LITTER_ID)
    bundle_group = group_of(db, BUNDLE_LITTER_ID)

    report = collection_runner.run_scc_dogs(db, dog_collector_serving())
    db.expire_all()
    gold_detail = client.get(f"/api/v1/litters/{gold_group.id}", headers=collected).json()
    bundle_detail = client.get(f"/api/v1/litters/{bundle_group.id}", headers=collected).json()

    assert report.source_run.status == SourceRunStatus.OK
    sire = db.get(Dog, group_of(db, GOLD_LITTER_ID).sire_dog_id)
    assert sire is not None and (sire.external_id, sire.color, sire.e_locus) == (
        GOLD_FATHER_DOG_ID,
        CoatColor.GOLD,
        "e/e",
    )
    assert group_of(db, GOLD_LITTER_ID).expected_colors == [
        {"color": "gold", "confidence": "inferred", "reason": "Gold : les deux parents sont gold", "puppy_odds": 1.0}
    ]
    assert gold_detail["sire"]["color"] == "gold"
    assert gold_detail["sire"]["e_locus"] == "e/e"
    assert gold_detail["expected_colors"][0]["reason"] == "Gold : les deux parents sont gold"
    assert sorted(puppy["name"] for puppy in gold_detail["puppies"]) == ["Balti", "Bella", "Bonnie"]
    assert gold_detail["colors"] == [{"color": "gold", "confidence": "certain"}]
    # The ad keeps the say on the sexes: the registered puppies only fill a blank.
    assert (gold_detail["male_count"], gold_detail["female_count"]) == (4, 1)
    bundle_sire = db.get(Dog, group_of(db, BUNDLE_LITTER_ID).sire_dog_id)
    assert bundle_sire is not None and bundle_sire.external_id == BUNDLE_FATHER_DOG_ID
    assert [color["color"] for color in bundle_detail["expected_colors"]] == ["gold", "noir_et_feu"]
    assert {color["color"] for color in bundle_detail["colors"]} == {"gold", "noir_et_feu"}
    assert bundle_detail["tier"] == "acceptable"
    assert group_of(db, BUNDLE_LITTER_ID).puppies_detail_next_try_at is not None


def test_the_registered_puppies_give_the_sexes_when_the_ad_holds_none(
    client: TestClient, db: Session, collected: dict[str, str]
) -> None:
    gold_group = group_of(db, GOLD_LITTER_ID)
    for listing in db.query(Listing).filter(Listing.litter_group_id == gold_group.id):
        listing.male_count = None
        listing.female_count = None
    db.commit()

    collection_runner.run_scc_dogs(db, dog_collector_serving())
    detail = client.get(f"/api/v1/litters/{gold_group.id}", headers=collected).json()

    assert (detail["male_count"], detail["female_count"]) == (1, 2)


def test_two_gold_parents_make_an_expected_litter_preferred(
    client: TestClient, db: Session, collected: dict[str, str]
) -> None:
    expected_group = group_of(db, EXPECTED_LITTER_ID)
    expected_group.confirmed_colors = []
    for listing in db.query(Listing).filter(Listing.litter_group_id == expected_group.id):
        listing.colors = [
            {"color": "noir", "confidence": "ambiguous"},
            {"color": "noir_et_feu", "confidence": "ambiguous"},
        ]
    db.commit()

    collection_runner.run_scc_dogs(db, dog_collector_serving())
    detail = client.get(f"/api/v1/litters/{expected_group.id}", headers=collected).json()

    assert group_of(db, EXPECTED_LITTER_ID).sire_dog_id is not None
    assert detail["puppies"] == []
    assert detail["colors"] == [{"color": "gold", "confidence": "inferred"}]
    assert detail["tier"] == "preferred"
    assert detail["reasons"][0]["text"] == "Gold, ta couleur préférée : les deux parents sont gold"
