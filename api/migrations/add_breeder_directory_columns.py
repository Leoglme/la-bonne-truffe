"""Migration: add to ``breeders`` what the Centrale Canine directory, the breeder sites and Léo's hand give (docs/03).

Idempotent — each column is added only when missing. SQLite cannot add a UNIQUE column, so the uniqueness of
``scc_user_id`` on an existing database comes from a unique index.
"""

from sqlalchemy import Engine, inspect, text

BREEDER_COLUMNS: tuple[tuple[str, str], ...] = (
    ("scc_user_id", "VARCHAR(40)"),
    ("scc_breeder_number", "VARCHAR(40)"),
    ("scc_site_slug", "VARCHAR(120)"),
    ("logo_url", "VARCHAR(500)"),
    ("scc_variety_ids", "JSON NOT NULL DEFAULT '[]'"),
    ("scc_last_litter_at", "DATETIME"),
    ("is_scc_selected", "BOOLEAN"),
    ("scc_directory_seen_at", "DATETIME"),
    ("chiens_de_france_site_url", "VARCHAR(500)"),
    ("chiens_de_france_registered_on", "DATE"),
    ("breeding_females_count", "INTEGER"),
    ("litters_last_year_count", "INTEGER"),
    ("cover_photo_url", "VARCHAR(500)"),
    ("links", "JSON NOT NULL DEFAULT '[]'"),
    ("is_manual", "BOOLEAN NOT NULL DEFAULT 0"),
    ("created_by_user_id", "INTEGER REFERENCES users(id) ON DELETE SET NULL"),
    ("search_text", "TEXT"),
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
        connection.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ux_breeders_scc_user_id ON breeders (scc_user_id)"))
