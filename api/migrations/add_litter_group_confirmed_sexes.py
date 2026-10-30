"""Migration: add ``litter_groups.confirmed_male_count`` and ``confirmed_female_count`` (sexes confirmed by hand).

Idempotent — the columns are added only when missing.
"""

from sqlalchemy import Engine, inspect, text


def run_migration(database_engine: Engine) -> None:
    """
    Add the columns to an existing table; a fresh database already has them.

    Args:
        database_engine: Engine of the database to migrate.
    """
    columns = {column["name"] for column in inspect(database_engine).get_columns("litter_groups")}
    with database_engine.begin() as connection:
        for column in ("confirmed_male_count", "confirmed_female_count"):
            if column not in columns:
                connection.execute(text(f"ALTER TABLE litter_groups ADD COLUMN {column} INTEGER"))
