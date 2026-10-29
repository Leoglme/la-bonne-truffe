"""Migration: add ``users.litters_visited_at`` (last time the home list was looked at).

Idempotent — the column is added only when missing.
"""

from sqlalchemy import Engine, inspect, text


def run_migration(database_engine: Engine) -> None:
    """
    Add the column to an existing table; a fresh database already has it.

    Args:
        database_engine: Engine of the database to migrate.
    """
    columns = {column["name"] for column in inspect(database_engine).get_columns("users")}
    if "litters_visited_at" in columns:
        return
    with database_engine.begin() as connection:
        connection.execute(text("ALTER TABLE users ADD COLUMN litters_visited_at DATETIME"))
