"""Migration: add ``follow_ups.reminder_sent_at`` (when the follow-up reminder was pushed).

Idempotent — the column is added only when missing.
"""

from sqlalchemy import Engine, inspect, text


def run_migration(database_engine: Engine) -> None:
    """
    Add the column to an existing table; a fresh database already has it.

    Args:
        database_engine: Engine of the database to migrate.
    """
    columns = {column["name"] for column in inspect(database_engine).get_columns("follow_ups")}
    if "reminder_sent_at" in columns:
        return
    with database_engine.begin() as connection:
        connection.execute(text("ALTER TABLE follow_ups ADD COLUMN reminder_sent_at DATETIME"))
