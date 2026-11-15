"""Migration: add ``listings.suggested_color``, the colour the AI reads on the photo of a puppy (docs/03).

Since 15/11/2026 the photo of a puppy whose ad gives no colour is read by an AI (Mistral, free plan), a few each
hour; the litter is then matched on the colours read of the puppies still offered, shown « suggéré par IA ».
``color_suggested_at`` and ``color_suggestion_photo_url`` tell which photo was read and when, so that a photo is read
once and a new one again.

Idempotent — each column is added only when missing.
"""

from sqlalchemy import Engine, inspect, text

COLUMNS: dict[str, str] = {
    "suggested_color": "VARCHAR(40)",
    "color_suggested_at": "DATETIME",
    "color_suggestion_photo_url": "VARCHAR(500)",
}


def run_migration(database_engine: Engine) -> None:
    """
    Add the columns to an existing table; a fresh database already has them.

    Args:
        database_engine: Engine of the database to migrate.
    """
    existing = {column["name"] for column in inspect(database_engine).get_columns("listings")}
    with database_engine.begin() as connection:
        for name, column_type in COLUMNS.items():
            if name not in existing:
                connection.execute(text(f"ALTER TABLE listings ADD COLUMN {name} {column_type}"))
