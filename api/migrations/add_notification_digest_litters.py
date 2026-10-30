"""Migration: add ``notifications.digest_litters`` (the litters an evening digest is about, with their event).

Idempotent — the column is added only when missing; the digests already sent keep an empty list.
"""

from sqlalchemy import Engine, inspect, text


def run_migration(database_engine: Engine) -> None:
    """
    Add the column to an existing table; a fresh database already has it.

    Args:
        database_engine: Engine of the database to migrate.
    """
    columns = {column["name"] for column in inspect(database_engine).get_columns("notifications")}
    if "digest_litters" in columns:
        return
    with database_engine.begin() as connection:
        connection.execute(text("ALTER TABLE notifications ADD COLUMN digest_litters JSON NOT NULL DEFAULT '[]'"))
