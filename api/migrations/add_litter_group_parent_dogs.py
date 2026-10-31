"""Migration: add to ``litter_groups`` the parents read at the Centrale Canine and the colours they imply (docs/03).

Idempotent — each column is added only when missing.
"""

from sqlalchemy import Engine, inspect, text

LITTER_GROUP_COLUMNS: tuple[tuple[str, str], ...] = (
    ("sire_dog_id", "INTEGER"),
    ("dam_dog_id", "INTEGER"),
    ("expected_colors", "JSON NOT NULL DEFAULT '[]'"),
    ("puppies_detail_fetched_at", "DATETIME"),
    ("puppies_detail_next_try_at", "DATETIME"),
)


def run_migration(database_engine: Engine) -> None:
    """
    Add the missing columns to an existing table; a fresh database already has them.

    Args:
        database_engine: Engine of the database to migrate.
    """
    existing = {column["name"] for column in inspect(database_engine).get_columns("litter_groups")}
    with database_engine.begin() as connection:
        for name, definition in LITTER_GROUP_COLUMNS:
            if name in existing:
                continue
            connection.execute(text(f"ALTER TABLE litter_groups ADD COLUMN {name} {definition}"))
