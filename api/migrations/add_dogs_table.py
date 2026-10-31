"""Migration: create ``dogs`` (parents, reproducers and puppies read one by one, docs/03).

Idempotent — creating the table is a no-op when it already exists.
"""

from sqlalchemy import Engine

from core.database import Base
from models.dog import Dog


def run_migration(database_engine: Engine) -> None:
    """
    Create the table.

    Args:
        database_engine: Engine of the database to migrate.
    """
    Base.metadata.tables[Dog.__tablename__].create(database_engine, checkfirst=True)
