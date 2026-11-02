"""Migration: give one more breeder the page found by hand on 02/11/2026 (docs/05, « Sites des élevages »).

The second search, on the breeders the first one could not reach, found no site showing English cockers: only
kennels of other breeds, dead sites, and the ads of a breeding without a site, whose photos show its cockers. Runs
once (recorded in ``schema_migrations``).
"""

from sqlalchemy import Engine

from migrations.add_breeder_links_found_by_hand import fill_empty_places

MORE_LINKS_FOUND_BY_HAND: tuple[dict[str, str], ...] = (
    {
        "scc_breeder_id": "509530",
        "website": "https://www.uncompagnon.fr/annonce/detail/173222/cocker-anglais-noir-et-feu.html",
        "website_photo_url": "https://www.uncompagnon.fr/assets/uploads/announces/173222/1777909922886.jpg",
    },
)


def run_migration(database_engine: Engine) -> None:
    """
    Fill the empty places of each breeder found.

    Args:
        database_engine: Engine of the database to migrate.
    """
    fill_empty_places(database_engine, MORE_LINKS_FOUND_BY_HAND)
