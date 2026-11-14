"""Migration: read again the colour of every dog from its code (docs/03, « Le vocabulaire canonique des couleurs »).

Since 14/11/2026 « Noi. Pan.Bla.Gri. » is a blue roan, not a particoloured coat, and the codes breeders copy
without their dots (« F.OR », « Noi pan bla ») or the blue they write in full (« Bleue ») are understood. The
colours stored before kept the old reading, and so did the colours the parents of each litter imply, which now
also rule out the gold when a parent is tested E/E and the black when both parents are brown.

Runs once (recorded in ``schema_migrations``): each later reading of a dog stores its colour afresh.
"""

from sqlalchemy import Engine
from sqlalchemy.orm import Session

from models.dog import Dog
from models.litter_group import LitterGroup
from services.dog_color_inference import DogColorInference
from services.dog_ingestion import DogIngestionService


def run_migration(database_engine: Engine) -> None:
    """
    Store again the colour of every dog that has a colour code, then the expected colours of every litter whose
    two parents are read.

    Args:
        database_engine: Engine of the database to migrate.
    """
    with Session(database_engine) as db:
        for dog in db.query(Dog).filter(Dog.color_code.is_not(None)).all():
            dog.color = DogColorInference.canonical_color(dog.color_code)
        db.flush()
        litters_with_both_parents = (
            db.query(LitterGroup)
            .filter(LitterGroup.sire_dog_id.is_not(None), LitterGroup.dam_dog_id.is_not(None))
            .all()
        )
        for litter in litters_with_both_parents:
            DogIngestionService.refresh_expected_colors(db, litter)
        db.commit()
