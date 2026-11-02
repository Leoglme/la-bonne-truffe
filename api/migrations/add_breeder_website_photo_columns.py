"""Migration: add to ``breeders`` the main photo of the breeding's own website, and when it was read (docs/05).

Runs once (recorded in ``schema_migrations``); each column is added only when missing.
"""

from sqlalchemy import Engine, inspect, text

BREEDER_COLUMNS: tuple[tuple[str, str], ...] = (
    ("website_photo_url", "VARCHAR(500)"),
    ("website_read_at", "DATETIME"),
)


def run_migration(database_engine: Engine) -> None:
    """
    Add the missing columns.

    Args:
        database_engine: Engine of the database to migrate.
    """
    existing = {column["name"] for column in inspect(database_engine).get_columns("breeders")}
    with database_engine.begin() as connection:
        for name, definition in BREEDER_COLUMNS:
            if name not in existing:
                connection.execute(text(f"ALTER TABLE breeders ADD COLUMN {name} {definition}"))
