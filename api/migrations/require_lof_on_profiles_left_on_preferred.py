"""Migration: the profiles left on « LOF préféré » now ask for the LOF (« Obligatoire »).

Until the « Type Cocker… » ads of Chiots de France were read, no litter without papers reached the app:
« Préféré » and « Obligatoire » showed the same litters. Only LOF litters show by default since
29/10/2026; the « Pedigree LOF » criterion still opens the app to the others.

Runs once (recorded in ``schema_migrations``); a fresh database has no profile yet.
"""

from sqlalchemy import Engine, text


def run_migration(database_engine: Engine) -> None:
    """
    Move the profiles still on « Préféré » to « Obligatoire ».

    Args:
        database_engine: Engine of the database to migrate.
    """
    with database_engine.begin() as connection:
        connection.execute(
            text("UPDATE search_profiles SET lof_preference = 'required' WHERE lof_preference = 'preferred'")
        )
