"""Migration: add ``breeders.is_breed_club_member`` (the Centrale Canine tells the members of the breed club).

Idempotent — the column is added only when missing; the next Centrale Canine run fills it.
"""

from sqlalchemy import Engine, inspect, text


def run_migration(database_engine: Engine) -> None:
    """
    Add the column to an existing table; a fresh database already has it.

    Args:
        database_engine: Engine of the database to migrate.
    """
    columns = {column["name"] for column in inspect(database_engine).get_columns("breeders")}
    if "is_breed_club_member" in columns:
        return
    with database_engine.begin() as connection:
        connection.execute(text("ALTER TABLE breeders ADD COLUMN is_breed_club_member BOOLEAN"))
