"""Migration: add ``listings.available_from``, the day an ad says the puppies may leave.

The departure of a litter was always its birth + 56 days, the legal handover age, even when the breeder announces a
later day (« Chiots nés le 12/11/2026 disponibles à partir du 23/01/2027 », seen on 12/11/2026). The next readings of
Chiens de France fill the column; the departure of each litter follows at the regrouping that comes after.

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
    if "available_from" in columns:
        return
    with database_engine.begin() as connection:
        connection.execute(text("ALTER TABLE listings ADD COLUMN available_from DATE"))
