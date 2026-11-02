"""Migration: forget the galleries read on the « dogs » document of the Centrale Canine sites, and read every site
again for the gallery of its home page (docs/05, ``scc_sites``).

Every site answers its « dogs » document with the same page of another breeding: the sixteen photos stored on
each breeder were those of that breeding, not of its dogs. Runs once (recorded in ``schema_migrations``).
"""

from sqlalchemy import Engine, text


def run_migration(database_engine: Engine) -> None:
    """
    Empty every gallery and forget when each site was read, so that the next runs read them again.

    Args:
        database_engine: Engine of the database to migrate.
    """
    with database_engine.begin() as connection:
        connection.execute(text("UPDATE breeders SET scc_site_photos = '[]' WHERE scc_site_photos != '[]'"))
        connection.execute(text("UPDATE breeders SET scc_site_seen_at = NULL WHERE scc_site_seen_at IS NOT NULL"))
