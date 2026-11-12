"""Migration: add ``listings.breeder_site_page_url``, the page of a listing on the breeder's own Chiens de France site.

The main site of Chiens de France sends ``/chiot/<n>`` to its regional list, and answers ``/saillie/<id>`` with a 404,
for the ads a breeder only shows on its own site (docs/02, verified on 12/11/2026): the app linked such puppies and
matings to nothing. The column is filled from the page the last reading of each site kept (``raw_json["site_url"]``),
a puppy pointed at its number on the page of its litter; the next readings of the sites keep it up to date.

Runs once (recorded in ``schema_migrations``); the column is added only when missing.
"""

import json

from sqlalchemy import Engine, inspect, text

from enums.listing_kind import ListingKind
from enums.listing_source import ListingSource
from services.collectors.chiens_de_france_sites import puppy_place_on_litter_page

PUPPY_EXTERNAL_ID_PREFIX = "chiot-"


def run_migration(database_engine: Engine) -> None:
    """
    Add the column, then give each listing read on a breeder's site the page that site showed it on.

    Args:
        database_engine: Engine of the database to migrate.
    """
    columns = {column["name"] for column in inspect(database_engine).get_columns("listings")}
    with database_engine.begin() as connection:
        if "breeder_site_page_url" not in columns:
            connection.execute(text("ALTER TABLE listings ADD COLUMN breeder_site_page_url VARCHAR(500)"))
        listings = connection.execute(
            text(
                "SELECT id, kind, external_id, raw_json FROM listings "
                "WHERE source = :source AND breeder_site_page_url IS NULL AND raw_json IS NOT NULL"
            ),
            {"source": ListingSource.CHIENS_DE_FRANCE.value},
        ).all()
        for listing_id, kind, external_id, raw_json in listings:
            raw_page = json.loads(raw_json)
            site_page_url = raw_page.get("site_url") if isinstance(raw_page, dict) else None
            if not site_page_url:
                continue
            if kind == ListingKind.PUPPY_AD.value:
                site_page_url = puppy_place_on_litter_page(
                    site_page_url, external_id.removeprefix(PUPPY_EXTERNAL_ID_PREFIX)
                )
            connection.execute(
                text("UPDATE listings SET breeder_site_page_url = :page_url WHERE id = :listing_id"),
                {"page_url": site_page_url, "listing_id": listing_id},
            )
