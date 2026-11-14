"""Migration: write again why the parents of each litter rule the gold out (docs/04, « Ce que donnent les parents »).

Since 14/11/2026 the litter page says « Aucun gold » with the reason the parents give, and that reason tells more: two
parents with white that both carry the gold give orange puppies with white, one in four, one in two or all of them;
a gold parent with another tested E/E names both. The reasons stored before kept the old words.

Runs once (recorded in ``schema_migrations``): each later reading of a litter's parents stores its colours afresh.
"""

from sqlalchemy import Engine
from sqlalchemy.orm import Session

from models.litter_group import LitterGroup
from services.dog_ingestion import DogIngestionService


def run_migration(database_engine: Engine) -> None:
    """
    Store again the expected colours, with their reasons, of every litter whose two parents are read.

    Args:
        database_engine: Engine of the database to migrate.
    """
    with Session(database_engine) as db:
        litters_with_both_parents = (
            db.query(LitterGroup)
            .filter(LitterGroup.sire_dog_id.is_not(None), LitterGroup.dam_dog_id.is_not(None))
            .all()
        )
        for litter in litters_with_both_parents:
            DogIngestionService.refresh_expected_colors(db, litter)
        db.commit()
