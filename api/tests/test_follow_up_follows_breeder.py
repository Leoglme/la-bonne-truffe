"""A litter entering the follow-up follows its breeder; the migration catches up the litters followed before."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine
from sqlalchemy.orm import Session

from enums.breeder_follow_status import BreederFollowStatus
from enums.follow_up_status import FollowUpStatus
from migrations.run_migrations import MigrationRunner
from models.breeder_follow import BreederFollow
from models.follow_up import FollowUp
from models.listing import Listing
from models.litter_group import LitterGroup
from models.user import User
from seeders.run_seeders import SeederRunner
from services.auth_service import AuthService
from services.collection_runner import collection_runner
from services.push_service import PushResult, PushService
from tests.centrale_canine_pages import collector_serving, load_recorded_pages

GOLD_LITTER_ID = "4333817"
EXPECTED_LITTER_ID = "4337070"
BREEDERS_URL = "/api/v1/breeders"
DEFAULT_BREEDER_FOLLOW = {
    "status": "to_contact",
    "notify_new_mating": True,
    "notify_birth": True,
    "notify_new_photos": True,
    "notify_ignored_colors": False,
    "next_reminder_at": None,
    "last_contact_at": None,
    "notes": [],
}


@pytest.fixture
def collected(db: Session, monkeypatch: pytest.MonkeyPatch) -> dict[str, str]:
    """Seed, collect the recorded pages once (pushes stubbed), and return the bearer header of the user."""
    monkeypatch.setattr(PushService, "send", lambda *_args, **_kwargs: PushResult(delivered=1))
    SeederRunner.run(db)
    collection_runner.run_centrale_canine(db, collector_serving(load_recorded_pages()))
    user = db.query(User).one()
    return {"Authorization": f"Bearer {AuthService.create_access_token(user.email)}"}


def group_of(db: Session, external_id: str) -> LitterGroup:
    """The litter group of a recorded listing, whose breeder is known."""
    group_id = db.query(Listing).filter(Listing.external_id == external_id).one().litter_group_id
    group = db.get(LitterGroup, group_id)
    assert group is not None
    assert group.breeder_id is not None
    return group


def follow_up_url(group: LitterGroup) -> str:
    """The follow-up route of a litter."""
    return f"/api/v1/litters/{group.id}/follow-up"


def breeder_follows(db: Session) -> list[BreederFollow]:
    """Every breeder follow, read again from the database."""
    db.expire_all()
    return db.query(BreederFollow).order_by(BreederFollow.breeder_id).all()


def test_following_a_litter_follows_its_breeder_with_the_alerts_of_the_drawer(
    client: TestClient, db: Session, collected: dict[str, str]
) -> None:
    group = group_of(db, GOLD_LITTER_ID)

    litter = client.put(follow_up_url(group), json={"status": "to_contact"}, headers=collected).json()
    breeder = client.get(f"{BREEDERS_URL}/{group.breeder_id}", headers=collected).json()
    followed_cards = client.get(BREEDERS_URL, params={"filter": "followed"}, headers=collected).json()

    assert litter["follow_up"]["status"] == "to_contact"
    assert litter["breeder"]["id"] == group.breeder_id
    assert (breeder["is_followed"], breeder["follow"]) == (True, DEFAULT_BREEDER_FOLLOW)
    assert [card["id"] for card in followed_cards] == [group.breeder_id]


def test_a_note_on_a_litter_not_followed_yet_follows_its_breeder_too(
    client: TestClient, db: Session, collected: dict[str, str]
) -> None:
    group = group_of(db, GOLD_LITTER_ID)

    client.post(f"/api/v1/litters/{group.id}/notes", json={"text": "Appelée, rappeler jeudi."}, headers=collected)

    assert [follow.breeder_id for follow in breeder_follows(db)] == [group.breeder_id]


def test_a_breeder_already_followed_keeps_its_alerts_its_status_and_its_notes(
    client: TestClient, db: Session, collected: dict[str, str]
) -> None:
    group = group_of(db, GOLD_LITTER_ID)
    client.put(
        f"{BREEDERS_URL}/{group.breeder_id}/follow",
        json={"status": "waiting", "notify_birth": False},
        headers=collected,
    )
    client.post(f"{BREEDERS_URL}/{group.breeder_id}/notes", json={"text": "Liste d'attente gold"}, headers=collected)

    client.put(follow_up_url(group), json={"status": "to_contact"}, headers=collected)
    follow = client.get(f"{BREEDERS_URL}/{group.breeder_id}", headers=collected).json()["follow"]

    assert (follow["status"], follow["notify_birth"]) == ("waiting", False)
    assert [note["text"] for note in follow["notes"]] == ["Liste d'attente gold"]
    assert len(breeder_follows(db)) == 1


def test_a_litter_whose_breeder_is_unknown_follows_no_breeder(
    client: TestClient, db: Session, collected: dict[str, str]
) -> None:
    group = group_of(db, GOLD_LITTER_ID)
    group.breeder_id = None
    db.commit()

    followed = client.put(follow_up_url(group), json={"status": "to_contact"}, headers=collected)

    assert followed.json()["follow_up"]["status"] == "to_contact"
    assert breeder_follows(db) == []


def test_a_breeder_unfollowed_on_purpose_does_not_come_back_when_the_litter_changes(
    client: TestClient, db: Session, collected: dict[str, str]
) -> None:
    group = group_of(db, GOLD_LITTER_ID)
    client.put(follow_up_url(group), json={"status": "to_contact"}, headers=collected)
    client.delete(f"{BREEDERS_URL}/{group.breeder_id}/follow", headers=collected)

    client.put(
        follow_up_url(group),
        json={"status": "contacted", "next_reminder_at": "2026-11-05T09:00:00Z"},
        headers=collected,
    )
    client.post(f"/api/v1/litters/{group.id}/notes", json={"text": "Rappeler jeudi."}, headers=collected)

    assert breeder_follows(db) == []


def test_stopping_to_follow_a_litter_keeps_its_breeder_followed(
    client: TestClient, db: Session, collected: dict[str, str]
) -> None:
    group = group_of(db, GOLD_LITTER_ID)
    client.put(follow_up_url(group), json={"status": "to_contact"}, headers=collected)

    client.delete(follow_up_url(group), headers=collected)

    assert [follow.breeder_id for follow in breeder_follows(db)] == [group.breeder_id]


def follow_litters_as_before_the_migration(db: Session) -> tuple[int, int]:
    """Follow two litters of one breeder and the expected litter, whose breeder alone is followed by hand."""
    user = db.query(User).one()
    gold_group = group_of(db, GOLD_LITTER_ID)
    sibling_group = (
        db.query(LitterGroup)
        .filter(LitterGroup.breeder_id == gold_group.breeder_id, LitterGroup.id != gold_group.id)
        .first()
    )
    expected_group = group_of(db, EXPECTED_LITTER_ID)
    assert sibling_group is not None
    assert gold_group.breeder_id is not None
    assert expected_group.breeder_id is not None
    assert expected_group.breeder_id != gold_group.breeder_id
    db.add_all(
        FollowUp(user_id=user.id, litter_group_id=group.id, status=FollowUpStatus.TO_CONTACT)
        for group in (gold_group, sibling_group, expected_group)
    )
    db.add(
        BreederFollow(
            user_id=user.id,
            breeder_id=expected_group.breeder_id,
            status=BreederFollowStatus.WAITING,
            notify_birth=False,
        )
    )
    db.commit()
    return gold_group.breeder_id, expected_group.breeder_id


def test_the_migration_follows_the_breeders_of_the_litters_followed_before(
    db: Session, engine: Engine, collected: dict[str, str]
) -> None:
    gold_breeder_id, breeder_followed_by_hand_id = follow_litters_as_before_the_migration(db)

    applied = MigrationRunner(engine).run()
    follows_by_breeder = {follow.breeder_id: follow for follow in breeder_follows(db)}

    assert "follow_breeders_of_followed_litters" in applied
    assert set(follows_by_breeder) == {gold_breeder_id, breeder_followed_by_hand_id}
    gold_follow = follows_by_breeder[gold_breeder_id]
    assert gold_follow.status == BreederFollowStatus.TO_CONTACT
    assert gold_follow.notify_new_mating and gold_follow.notify_birth and gold_follow.notify_new_photos
    assert gold_follow.notify_ignored_colors is False
    assert gold_follow.created_at is not None
    follow_by_hand = follows_by_breeder[breeder_followed_by_hand_id]
    assert (follow_by_hand.status, follow_by_hand.notify_birth) == (BreederFollowStatus.WAITING, False)


def test_the_migration_runs_once_so_a_breeder_unfollowed_afterwards_stays_unfollowed(
    client: TestClient, db: Session, engine: Engine, collected: dict[str, str]
) -> None:
    gold_breeder_id, breeder_followed_by_hand_id = follow_litters_as_before_the_migration(db)
    runner = MigrationRunner(engine)
    runner.run()

    client.delete(f"{BREEDERS_URL}/{gold_breeder_id}/follow", headers=collected)
    applied_again = runner.run()

    assert applied_again == []
    assert [follow.breeder_id for follow in breeder_follows(db)] == [breeder_followed_by_hand_id]
