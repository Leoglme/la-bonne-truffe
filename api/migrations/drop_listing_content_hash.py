"""Migration: drop ``listings.content_hash``, a hash written at every run and never read.

Idempotent — the column is dropped only when present; a fresh database never had it.
"""

from sqlalchemy import Engine, inspect, text


def run_migration(database_engine: Engine) -> None:
    """
    Drop the column from an existing table.

    Args:
        database_engine: Engine of the database to migrate.
    """
    columns = {column["name"] for column in inspect(database_engine).get_columns("listings")}
    if "content_hash" not in columns:
        return
    with database_engine.begin() as connection:
        connection.execute(text("ALTER TABLE listings DROP COLUMN content_hash"))
