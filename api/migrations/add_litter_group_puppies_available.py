"""Migration: add ``litter_groups.puppies_available`` (puppies still offered, to tell a followed litter's drop).

Idempotent — the column is added only when missing.
"""

from sqlalchemy import Engine, inspect, text


def run_migration(database_engine: Engine) -> None:
    """
    Add the column to an existing table; a fresh database already has it.

    Args:
        database_engine: Engine of the database to migrate.
    """
    columns = {column["name"] for column in inspect(database_engine).get_columns("litter_groups")}
    if "puppies_available" in columns:
        return
    with database_engine.begin() as connection:
        connection.execute(text("ALTER TABLE litter_groups ADD COLUMN puppies_available INTEGER"))
