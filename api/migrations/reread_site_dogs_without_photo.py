"""Migration: read again the pages of the reproducers of the breeders' Chiens de France sites that have no photo.

The newer dog pages of these sites show a gallery instead of the main image the reading looked for: their dogs were
stored without a photo (seen on 12/11/2026), so a breeding showed its reproducers, and a litter its mother, without
one. A dog page is read again only after thirty days: forgetting when these were read makes the next reading of
each site read them now, with the photos.

Runs once (recorded in ``schema_migrations``).
"""

from sqlalchemy import Engine, text

from enums.listing_source import ListingSource


def run_migration(database_engine: Engine) -> None:
    """
    Forget when the page of each Chiens de France dog without a photo was read.

    Args:
        database_engine: Engine of the database to migrate.
    """
    with database_engine.begin() as connection:
        connection.execute(
            text("UPDATE dogs SET fetched_at = NULL WHERE source = :source AND photos = '[]'"),
            {"source": ListingSource.CHIENS_DE_FRANCE.value},
        )
