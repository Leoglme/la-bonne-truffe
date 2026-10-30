"""Migration: add ``listings.mating_number`` (the Centrale Canine declaration number a mating and its birth share).

Idempotent — the column is added only when missing; the next Centrale Canine run fills it.
"""

from sqlalchemy import Engine, inspect, text


def run_migration(database_engine: Engine) -> None:
    """
    Add the column to an existing table; a fresh database already has it.

    Args:
        database_engine: Engine of the database to migrate.
    """
    columns = {column["name"] for column in inspect(database_engine).get_columns("listings")}
    if "mating_number" in columns:
        return
    with database_engine.begin() as connection:
        connection.execute(text("ALTER TABLE listings ADD COLUMN mating_number VARCHAR(40)"))
