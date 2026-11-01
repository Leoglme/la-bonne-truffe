"""Migration: add to ``breeders`` the social accounts the Centrale Canine site of a breeding declares (docs/03).

Idempotent — each column is added only when missing.
"""

from sqlalchemy import Engine, inspect, text

BREEDER_COLUMNS: tuple[tuple[str, str], ...] = (
    ("facebook_url", "VARCHAR(500)"),
    ("instagram_url", "VARCHAR(500)"),
    ("youtube_url", "VARCHAR(500)"),
)


def run_migration(database_engine: Engine) -> None:
    """
    Add the missing columns to an existing table; a fresh database already has them.

    Args:
        database_engine: Engine of the database to migrate.
    """
    existing = {column["name"] for column in inspect(database_engine).get_columns("breeders")}
    with database_engine.begin() as connection:
        for name, definition in BREEDER_COLUMNS:
            if name in existing:
                continue
            connection.execute(text(f"ALTER TABLE breeders ADD COLUMN {name} {definition}"))
