"""Migration: compute again the colours the parents of each litter imply (docs/04, « Ce que donnent les parents »).

Since 14/11/2026 two parents with white in their coat (particolore, tricolore, rouan) only announce puppies with
white, never a solid gold. The colours stored when the parents were read still said « gold possible » for such a
couple that carries the gold.

Runs once (recorded in ``schema_migrations``): each later reading of a litter's parents stores its colours afresh.
"""

from sqlalchemy import Engine
from sqlalchemy.orm import Session

from models.litter_group import LitterGroup
from services.dog_ingestion import DogIngestionService


def run_migration(database_engine: Engine) -> None:
    """
    Store again the expected colours of every litter whose two parents are read.

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
