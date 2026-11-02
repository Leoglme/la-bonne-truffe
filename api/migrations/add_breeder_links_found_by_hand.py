"""Migration: give some breeders the sites and the accounts found by hand on 01/11/2026 (docs/05, « Sites des
élevages »): a Chiens de France site the regional lists do not tie to them, an own website, a Facebook or Instagram
account.

Only the sites that show English cockers are given, since their photos go on the card of the breeder and on its
litters. A breeder is found by its Centrale Canine identifier, and what it already has is kept. Runs once (recorded
in ``schema_migrations``).
"""

import json

from sqlalchemy import Engine, text

from core.clock import naive_utc_now
from enums.social_link_origin import SocialLinkOrigin

LINKS_FOUND_BY_HAND: tuple[dict[str, str], ...] = (
    {"scc_breeder_id": "500655", "chiens_de_france_site_url": "https://dulavoir.chiens-de-france.com"},
    {
        "scc_breeder_id": "187925",
        "website": "https://elevage-canin-lagarnache.fr/",
        "website_photo_url": "https://elevage-canin-lagarnache.fr/wp-content/uploads/2022/09/Cocker-chiot-1024x768.jpg",
        "facebook_url": "https://www.facebook.com/La-Colline-des-Terres-Noires-857994887891219/",
    },
    {"scc_breeder_id": "467047", "website": "https://cockerdelademeureduberger.weebly.com"},
    {
        "scc_breeder_id": "382284",
        "chiens_de_france_site_url": "https://delavignelais.chiens-de-france.com",
        "facebook_url": "https://www.facebook.com/DomainedelaVignelais",
        "instagram_url": "https://www.instagram.com/domaine_de_la_vignelais_/",
    },
    {"scc_breeder_id": "475036", "chiens_de_france_site_url": "https://goncalves-gil.chiens-de-france.com"},
    {"scc_breeder_id": "456150", "facebook_url": "https://www.facebook.com/elevage.jardindeboheme/"},
    {"scc_breeder_id": "400228", "facebook_url": "https://www.facebook.com/ElevageOreeduchenay/"},
    {"scc_breeder_id": "336368", "facebook_url": "https://www.facebook.com/profile.php?id=1699034256993541"},
)
FILLED_COLUMNS: tuple[str, ...] = (
    "website",
    "chiens_de_france_site_url",
    "facebook_url",
    "instagram_url",
    "website_photo_url",
)
SOCIAL_ACCOUNTS_BY_COLUMN: dict[str, str] = {"facebook_url": "facebook", "instagram_url": "instagram"}
SELECT_BREEDER_SQL = (
    "SELECT id, social_link_origins, "
    + ", ".join(FILLED_COLUMNS)
    + " FROM breeders WHERE scc_breeder_id = :scc_breeder_id"
)


def run_migration(database_engine: Engine) -> None:
    """
    Fill the empty places of each breeder found.

    Args:
        database_engine: Engine of the database to migrate.
    """
    fill_empty_places(database_engine, LINKS_FOUND_BY_HAND)


def fill_empty_places(database_engine: Engine, links_found_by_hand: tuple[dict[str, str], ...]) -> None:
    """
    Fill the empty places of the breeders found by their Centrale Canine identifier. A Chiens de France site also
    becomes the website of a breeding that has none, as a link pasted by hand does; a photo chosen by hand counts as
    the reading of the website; the search text is built again at the next search.

    Args:
        database_engine: Engine of the database to migrate.
        links_found_by_hand: Per breeder, its ``scc_breeder_id`` and the values of ``FILLED_COLUMNS`` found.
    """
    with database_engine.begin() as connection:
        for links in links_found_by_hand:
            breeder = (
                connection.execute(text(SELECT_BREEDER_SQL), {"scc_breeder_id": links["scc_breeder_id"]})
                .mappings()
                .first()
            )
            if breeder is None:
                continue
            values: dict[str, object] = {
                column: links[column] for column in FILLED_COLUMNS if column in links and breeder[column] is None
            }
            if "chiens_de_france_site_url" in values and breeder["website"] is None:
                values.setdefault("website", values["chiens_de_france_site_url"])
            if not values:
                continue
            if "website_photo_url" in values:
                values["website_read_at"] = naive_utc_now().isoformat(sep=" ")
            origins = json.loads(breeder["social_link_origins"] or "{}")
            for column, account in SOCIAL_ACCOUNTS_BY_COLUMN.items():
                if column in values:
                    origins[account] = SocialLinkOrigin.ADDED_BY_HAND.value
            values["social_link_origins"] = json.dumps(origins)
            assignments = ", ".join(f"{column} = :{column}" for column in values)
            connection.execute(
                text(f"UPDATE breeders SET {assignments}, search_text = NULL WHERE id = :breeder_id"),
                {**values, "breeder_id": breeder["id"]},
            )
