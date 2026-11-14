"""Migration: the next reading of each breeder site on Chiens de France counts as its first (docs/04, « Suivre un
élevage »).

Since 14/11/2026 the reading of a site also opens the pages of the litters born at the breeding in the last six months
that the site no longer offers. What these pages show is weeks old: like the first reading of a site, the next one
records the alerts of the followed breeders without sending them.

Runs once (recorded in ``schema_migrations``).
"""

from sqlalchemy import Engine, text

_FORGET_LAST_READINGS_SQL = """
UPDATE breeders SET chiens_de_france_site_seen_at = NULL WHERE chiens_de_france_site_url IS NOT NULL
"""


def run_migration(database_engine: Engine) -> None:
    """
    Forget when each breeder site was last read.

    Args:
        database_engine: Engine of the database to migrate.
    """
    with database_engine.begin() as connection:
        connection.execute(text(_FORGET_LAST_READINGS_SQL))
