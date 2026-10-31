"""Migration: create ``litter_shares`` (private links to a litter, opened without an account).

Idempotent — creating the table is a no-op when it already exists.
"""

from sqlalchemy import Engine

from core.database import Base
from models.litter_share import LitterShare


def run_migration(database_engine: Engine) -> None:
    """
    Create the table.

    Args:
        database_engine: Engine of the database to migrate.
    """
    Base.metadata.tables[LitterShare.__tablename__].create(database_engine, checkfirst=True)
