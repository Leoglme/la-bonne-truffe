"""Migration: create every table of docs/03-modele-de-donnees.md (the V1 baseline).

Idempotent — creating a table is a no-op when it already exists. Later migrations alter these
tables with explicit SQL, one file per change.

Run with:
    python migrations/run_migrations.py
"""

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

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
        model.__table__.create(database_engine, checkfirst=True)  # type: ignore[attr-defined]
