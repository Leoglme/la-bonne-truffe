"""Migration: create ``breeder_follows``, ``breeder_follow_notes`` and ``breeder_follow_events`` (docs/03).

Idempotent — creating a table is a no-op when it already exists.
"""

from sqlalchemy import Engine

from core.database import Base
from models.breeder_follow import BreederFollow, BreederFollowEvent, BreederFollowNote


def run_migration(database_engine: Engine) -> None:
    """
    Create the three tables, the follows first.

    Args:
        database_engine: Engine of the database to migrate.
    """
    for model in (BreederFollow, BreederFollowNote, BreederFollowEvent):
        Base.metadata.tables[model.__tablename__].create(database_engine, checkfirst=True)
