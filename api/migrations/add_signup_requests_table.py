"""Migration: create ``signup_requests`` (signup attempts kept while signups are closed).

Idempotent — creating the table is a no-op when it already exists.
"""

from sqlalchemy import Engine

from core.database import Base
from models.signup_request import SignupRequest


def run_migration(database_engine: Engine) -> None:
    """
    Create the table.

    Args:
        database_engine: Engine of the database to migrate.
    """
    Base.metadata.tables[SignupRequest.__tablename__].create(database_engine, checkfirst=True)
