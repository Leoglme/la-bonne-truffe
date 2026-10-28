"""Seeders and migrations: reference data, single user, starting profile, idempotence."""

from pathlib import Path

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session

from core.config import settings
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


def test_only_verified_scc_identifiers_are_seeded(db: Session) -> None:
    SeederRunner.run(db)

    known = {department.code: department.scc_term_id for department in db.query(Department) if department.scc_term_id}
    assert known == {"35": "t_41"}


def test_cocker_varieties_map_to_canonical_colors(db: Session) -> None:
    SeederRunner.run(db)

    varieties = {variety.source_variety_id: variety for variety in db.query(BreedVariety)}
    assert varieties["317"].covered_colors == ["gold"]
    assert varieties["317"].is_ambiguous is False
    assert varieties["159"].is_ambiguous is True
    assert varieties[None].label == "autres couleurs"


def test_starting_profile_matches_leo_answers(db: Session) -> None:
    SeederRunner.run(db)

    user = db.query(User).one()
    profile = db.query(SearchProfile).one()
    assert user.email == settings.admin_email
    assert profile.user_id == user.id
    assert profile.department_codes == ["35", "56", "22", "29", "44", "53", "49", "72", "85"]
    assert profile.sex_preference == "any"
    assert profile.price_max_cents is None
    assert profile.color_preferences == {"gold": "preferred", "noir_et_feu": "acceptable"}


def test_migrations_create_every_table_and_record_themselves(tmp_path: Path) -> None:
    database_engine = create_engine(f"sqlite:///{tmp_path / 'migrations.db'}")
    runner = MigrationRunner(database_engine)

    assert runner.run() == [
        "create_initial_tables",
        "add_litter_group_confirmed_colors",
        "add_digest_entries_table",
    ]
    assert runner.run() == []
    tables = set(inspect(database_engine).get_table_names())
    assert {"listings", "litter_groups", "push_subscriptions", "schema_migrations", "source_runs"} <= tables
