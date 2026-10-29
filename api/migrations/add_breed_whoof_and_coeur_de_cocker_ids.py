"""Migration: add ``breeds.whoof_id`` and ``breeds.coeur_de_cocker_id`` (how those two sources name a breed).

Idempotent — each column is added only when missing; the breed seeder fills them.
"""

from sqlalchemy import Engine, inspect, text

NEW_COLUMNS: tuple[str, ...] = ("whoof_id", "coeur_de_cocker_id")


def run_migration(database_engine: Engine) -> None:
    """
    Add the columns to an existing table; a fresh database already has them.

    Args:
        database_engine: Engine of the database to migrate.
    """
    columns = {column["name"] for column in inspect(database_engine).get_columns("breeds")}
    with database_engine.begin() as connection:
        for column in NEW_COLUMNS:
            if column not in columns:
                connection.execute(text(f"ALTER TABLE breeds ADD COLUMN {column} VARCHAR(120)"))
