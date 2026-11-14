"""Migration: add ``listings.confirmed_color``, the colour of one puppy noted by hand (docs/03).

Since 14/11/2026 each puppy of a litter page can have its colour noted, from its photo or after a call, and the
litter is then matched on the noted colours of the puppies still offered: a litter whose gold puppies are all reserved
is no longer matched as gold.

Idempotent — the column is added only when missing.
"""

from sqlalchemy import Engine, inspect, text


def run_migration(database_engine: Engine) -> None:
    """
    Add the column to an existing table; a fresh database already has it.

    Args:
        database_engine: Engine of the database to migrate.
    """
    columns = {column["name"] for column in inspect(database_engine).get_columns("listings")}
    if "confirmed_color" in columns:
        return
    with database_engine.begin() as connection:
        connection.execute(text("ALTER TABLE listings ADD COLUMN confirmed_color VARCHAR(40)"))
