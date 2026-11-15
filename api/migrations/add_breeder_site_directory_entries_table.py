"""Migration: create ``breeder_site_directory_entries`` (the breeder sites the regional lists of Chiens de France
name, which place the breedings the Centrale Canine lists without an address).

Idempotent — creating the table is a no-op when it already exists.
"""

from sqlalchemy import Engine

from core.database import Base
from models.breeder_site_directory_entry import BreederSiteDirectoryEntry


def run_migration(database_engine: Engine) -> None:
    """
    Create the table.

    Args:
        database_engine: Engine of the database to migrate.
    """
    Base.metadata.tables[BreederSiteDirectoryEntry.__tablename__].create(database_engine, checkfirst=True)
