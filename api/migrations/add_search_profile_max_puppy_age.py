"""Migration: add ``search_profiles.max_puppy_age_days`` (older litters are hidden), two months on existing profiles.

Idempotent — the column is added only when missing, and only a profile without a value gets the two months.
"""

from sqlalchemy import Engine, inspect, text

TWO_MONTHS_IN_DAYS = 61


def run_migration(database_engine: Engine) -> None:
    """
    Add the column to an existing table and give the profiles the default; a fresh database already has it.

    Args:
        database_engine: Engine of the database to migrate.
    """
    columns = {column["name"] for column in inspect(database_engine).get_columns("search_profiles")}
    with database_engine.begin() as connection:
        if "max_puppy_age_days" not in columns:
            connection.execute(text("ALTER TABLE search_profiles ADD COLUMN max_puppy_age_days INTEGER"))
        connection.execute(
            text("UPDATE search_profiles SET max_puppy_age_days = :days WHERE max_puppy_age_days IS NULL"),
            {"days": TWO_MONTHS_IN_DAYS},
        )
