"""Migration: forget when each Centrale Canine site was read, so that the next runs read them again for their links.

The sites read before ``add_breeder_social_link_columns`` gave their photos only; their « general » document
(social accounts, « mon autre site ») is read once they are planned again (docs/05, ``scc_sites``).
"""

from sqlalchemy import Engine, text


def run_migration(database_engine: Engine) -> None:
    """
    Reset the reading date of every site.

    Args:
        database_engine: Engine of the database to migrate.
    """
    with database_engine.begin() as connection:
        connection.execute(text("UPDATE breeders SET scc_site_seen_at = NULL WHERE scc_site_seen_at IS NOT NULL"))
