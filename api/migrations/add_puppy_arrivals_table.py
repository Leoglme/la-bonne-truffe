"""Migration: create ``puppy_arrivals`` (the puppy found pauses the search).

Idempotent — creating the table is a no-op when it already exists.
"""

from sqlalchemy import Engine

from core.database import Base
from models.puppy_arrival import PuppyArrival


def run_migration(database_engine: Engine) -> None:
    """
    Create the table.

    Args:
        database_engine: Engine of the database to migrate.
    """
    Base.metadata.tables[PuppyArrival.__tablename__].create(database_engine, checkfirst=True)
