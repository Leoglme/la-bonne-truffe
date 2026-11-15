"""Migration: add ``breeder_follow_events.subject_key``, what an event without litter is about (docs/03).

Since 15/11/2026 a followed breeder whose mother is likely to have a litter within a month is told so once per
mother and last litter: the key (« selune du clos de l ecotay:2025-11-19 ») keeps it from coming back.

Idempotent — the column is added only when missing.
"""

from sqlalchemy import Engine, inspect, text


def run_migration(database_engine: Engine) -> None:
    """
    Add the column to an existing table; a fresh database already has it.

    Args:
        database_engine: Engine of the database to migrate.
    """
    columns = {column["name"] for column in inspect(database_engine).get_columns("breeder_follow_events")}
    if "subject_key" in columns:
        return
    with database_engine.begin() as connection:
        connection.execute(text("ALTER TABLE breeder_follow_events ADD COLUMN subject_key VARCHAR(160)"))
