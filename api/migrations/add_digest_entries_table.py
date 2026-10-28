"""Migration: create ``digest_entries`` (litters waiting for the evening digest).

Idempotent — creating the table is a no-op when it already exists.
"""

from sqlalchemy import Engine

from core.database import Base
from models.digest_entry import DigestEntry


def run_migration(database_engine: Engine) -> None:
    """
    Create the table.

    Args:
        database_engine: Engine of the database to migrate.
    """
    Base.metadata.tables[DigestEntry.__tablename__].create(database_engine, checkfirst=True)
