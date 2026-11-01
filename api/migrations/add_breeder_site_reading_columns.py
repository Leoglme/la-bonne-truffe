"""Migration: add to ``breeders`` what the reading of a breeder's site keeps (docs/03), and where its accounts came from.

The social accounts known before came from the Centrale Canine sites of the breedings: they are marked so.

Runs once (recorded in ``schema_migrations``); each column is added only when missing.
"""

import json

from sqlalchemy import Engine, inspect, text

from enums.social_link_origin import SocialLinkOrigin

BREEDER_COLUMNS: tuple[tuple[str, str], ...] = (
    ("chiens_de_france_site_seen_at", "DATETIME"),
    ("chiens_de_france_litters", "JSON NOT NULL DEFAULT '[]'"),
    ("social_link_origins", "JSON NOT NULL DEFAULT '{}'"),
)
SOCIAL_ACCOUNT_COLUMNS: dict[str, str] = {
    "facebook": "facebook_url",
    "instagram": "instagram_url",
    "youtube": "youtube_url",
}


def run_migration(database_engine: Engine) -> None:
    """
    Add the missing columns, then mark the accounts already known as found on the Centrale Canine sites.

    Args:
        database_engine: Engine of the database to migrate.
    """
    existing = {column["name"] for column in inspect(database_engine).get_columns("breeders")}
    with database_engine.begin() as connection:
        for name, definition in BREEDER_COLUMNS:
            if name not in existing:
                connection.execute(text(f"ALTER TABLE breeders ADD COLUMN {name} {definition}"))
        breeders = connection.execute(text("SELECT id, facebook_url, instagram_url, youtube_url FROM breeders")).all()
        for breeder_id, *addresses in breeders:
            origins = {
                account: SocialLinkOrigin.CENTRALE_CANINE.value
                for account, address in zip(SOCIAL_ACCOUNT_COLUMNS, addresses, strict=True)
                if address
            }
            if origins:
                connection.execute(
                    text("UPDATE breeders SET social_link_origins = :origins WHERE id = :breeder_id"),
                    {"origins": json.dumps(origins), "breeder_id": breeder_id},
                )
