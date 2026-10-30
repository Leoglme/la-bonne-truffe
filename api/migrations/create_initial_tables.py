"""Migration: create every table of docs/03-modele-de-donnees.md (the V1 baseline).

Idempotent — creating a table is a no-op when it already exists. Later migrations alter these
tables with explicit SQL, one file per change.
"""

from sqlalchemy import Engine

import models
from core.database import Base

BASELINE_MODELS: tuple[type[Base], ...] = (
    models.User,
    models.PushSubscription,
    models.Breed,
    models.BreedVariety,
    models.Department,
    models.Breeder,
    models.LitterGroup,
    models.Listing,
    models.ListingChange,
    models.SearchProfile,
    models.ListingMatch,
    models.FollowUp,
    models.FollowUpNote,
    models.SourceRun,
    models.Notification,
)


def run_migration(database_engine: Engine) -> None:
    """
    Create the baseline tables, parents before children.

    Args:
        database_engine: Engine of the database to migrate.
    """
    for model in BASELINE_MODELS:
        Base.metadata.tables[model.__tablename__].create(database_engine, checkfirst=True)
