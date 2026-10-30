"""Seeders and migrations: reference data, single user, starting profile, idempotence."""

from pathlib import Path

from sqlalchemy import Engine, create_engine, inspect
from sqlalchemy.orm import Session

from core.config import settings
from enums.lof_preference import LofPreference
from migrations import require_lof_on_profiles_left_on_preferred
from migrations.run_migrations import MigrationRunner
from models.breed_variety import BreedVariety
from models.department import Department
from models.search_profile import SearchProfile
from models.user import User
from seeders.run_seeders import SeederRunner


def test_seeders_fill_the_reference_tables_once(db: Session) -> None:
    first_run = SeederRunner.run(db)
    second_run = SeederRunner.run(db)

    assert first_run == {"departments": 101, "breeds": 4, "user": 1, "search_profile": 1}
    assert set(second_run.values()) == {0}


def test_scc_identifiers_read_on_the_litters_page_are_seeded(db: Session) -> None:
    SeederRunner.run(db)

    known = {department.code: department.scc_term_id for department in db.query(Department) if department.scc_term_id}
    assert len(known) == 74
    assert (known["35"], known["29"], known["974"]) == ("t_41", "t_35", "t_106")
    assert "05" not in known


def test_cocker_varieties_map_to_canonical_colors(db: Session) -> None:
    SeederRunner.run(db)

    varieties = {variety.source_variety_id: variety for variety in db.query(BreedVariety)}
    assert set(varieties) == {"158", "159", "317"}
    assert varieties["158"].covered_colors == ["gold"]
    assert varieties["158"].is_ambiguous is False
    assert varieties["159"].is_ambiguous is True
    assert varieties["317"].label == "autres couleurs"
    assert varieties["317"].is_ambiguous is True


def test_seeders_correct_the_variety_identifiers_of_an_older_database(db: Session) -> None:
    SeederRunner.run(db)
    db.query(BreedVariety).filter(BreedVariety.label == "rouge et doré").update({BreedVariety.source_variety_id: "317"})
    db.query(BreedVariety).filter(BreedVariety.label == "autres couleurs").update(
        {BreedVariety.source_variety_id: None}
    )
    db.commit()

    SeederRunner.run(db)

    identifiers_by_label = {variety.label: variety.source_variety_id for variety in db.query(BreedVariety)}
    assert identifiers_by_label == {
        "rouge et doré": "158",
        "noir, noir et feu, marron, marron et feu": "159",
        "autres couleurs": "317",
    }


def test_starting_profile_matches_leo_answers(db: Session) -> None:
    SeederRunner.run(db)

    user = db.query(User).one()
    profile = db.query(SearchProfile).one()
    assert user.email == settings.admin_email
    assert profile.user_id == user.id
    assert profile.department_codes == ["35", "56", "22", "29", "44", "53", "49", "72", "85"]
    assert profile.sex_preference == "any"
    assert profile.lof_preference == "required"
    assert profile.price_max_cents is None
    assert profile.color_preferences == {"gold": "preferred", "noir_et_feu": "acceptable"}


def test_migrations_create_every_table_and_record_themselves(tmp_path: Path) -> None:
    database_engine = create_engine(f"sqlite:///{tmp_path / 'migrations.db'}")
    runner = MigrationRunner(database_engine)

    assert runner.run() == [
        "create_initial_tables",
        "add_litter_group_confirmed_colors",
        "add_digest_entries_table",
        "add_breeder_coordinates_and_listing_publication",
        "add_litter_group_puppies_available",
        "require_lof_on_profiles_left_on_preferred",
        "add_signup_requests_table",
        "add_follow_up_reminder_sent_at",
        "add_user_litters_visited_at",
        "add_breed_whoof_and_coeur_de_cocker_ids",
        "add_breeder_breed_club_member",
        "drop_listing_content_hash",
        "add_listing_mating_number",
        "add_notification_digest_litters",
    ]
    assert runner.run() == []
    tables = set(inspect(database_engine).get_table_names())
    assert {
        "listings",
        "litter_groups",
        "push_subscriptions",
        "schema_migrations",
        "signup_requests",
        "source_runs",
    } <= tables


def test_profiles_left_on_lof_preferred_now_ask_for_the_lof(db: Session, engine: Engine) -> None:
    SeederRunner.run(db)
    starting_profile = db.query(SearchProfile).one()
    starting_profile.lof_preference = LofPreference.PREFERRED
    open_profile = SearchProfile(
        user_id=starting_profile.user_id, name="Tous les cockers", lof_preference=LofPreference.ANY
    )
    db.add(open_profile)
    db.commit()

    require_lof_on_profiles_left_on_preferred.run_migration(engine)

    db.expire_all()
    assert starting_profile.lof_preference == LofPreference.REQUIRED
    assert open_profile.lof_preference == LofPreference.ANY
