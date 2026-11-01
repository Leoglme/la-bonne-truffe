"""Migration: keep on ``dogs`` the colours of each dog's own parents, and read the colour genes again (docs/03).

The colour of a black dog with tan and white is now « tricolore », and the mask test « LocEm-Em/e » counts as the
E locus: both are computed again from what each dog's page gave. The parents read at the Centrale Canine are read
again by the next relays, for the colours of their own parents (a dog with a parent of the gold family carries the
gold, docs/04).

Runs once (recorded in ``schema_migrations``); the columns are added only when missing.
"""

import json

from sqlalchemy import Engine, inspect, text

from enums.dog_role import DogRole
from enums.listing_source import ListingSource
from services.dog_color_inference import DogColorInference

DOG_COLUMNS: tuple[tuple[str, str], ...] = (
    ("sire_color_code", "VARCHAR(80)"),
    ("dam_color_code", "VARCHAR(80)"),
)


def run_migration(database_engine: Engine) -> None:
    """
    Add the missing columns, compute the colour and the E locus of every dog again, and plan its parents' pages.

    Args:
        database_engine: Engine of the database to migrate.
    """
    existing = {column["name"] for column in inspect(database_engine).get_columns("dogs")}
    with database_engine.begin() as connection:
        for name, definition in DOG_COLUMNS:
            if name not in existing:
                connection.execute(text(f"ALTER TABLE dogs ADD COLUMN {name} {definition}"))
        dogs = connection.execute(text("SELECT id, color_code, health_codes, e_locus FROM dogs")).all()
        for dog_id, color_code, health_codes_json, e_locus in dogs:
            health_codes = json.loads(health_codes_json) if health_codes_json else []
            connection.execute(
                text("UPDATE dogs SET color = :color, e_locus = :e_locus WHERE id = :dog_id"),
                {
                    "color": DogColorInference.canonical_color(color_code).value,
                    "e_locus": DogColorInference.e_locus_of(health_codes) or e_locus,
                    "dog_id": dog_id,
                },
            )
        connection.execute(
            text("UPDATE dogs SET fetched_at = NULL WHERE source = :source AND role = :role"),
            {"source": ListingSource.CENTRALE_CANINE.value, "role": DogRole.PARENT.value},
        )
