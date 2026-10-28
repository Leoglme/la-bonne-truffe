"""Migration: add ``breeders.latitude`` / ``longitude`` and ``listings.published_at``.

The Centrale Canine gives the location of each breeding and the day a litter went online
(docs/02-sources.md). Idempotent — each column is added only when missing.
"""

from sqlalchemy import Engine, inspect, text

NEW_COLUMNS: tuple[tuple[str, str, str], ...] = (
    ("breeders", "latitude", "FLOAT"),
    ("breeders", "longitude", "FLOAT"),
    ("listings", "published_at", "DATETIME"),
)


def run_migration(database_engine: Engine) -> None:
    """
    Add the columns to existing tables; a fresh database already has them.

    Args:
        database_engine: Engine of the database to migrate.
    """
    for table_name, column_name, column_type in NEW_COLUMNS:
        columns = {column["name"] for column in inspect(database_engine).get_columns(table_name)}
        if column_name in columns:
            continue
        with database_engine.begin() as connection:
            connection.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"))
