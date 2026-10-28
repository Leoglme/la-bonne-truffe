"""
Database configuration and session management (SQLite).
"""

import logging
from collections.abc import Iterator
from pathlib import Path

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.engine.url import make_url
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from core.config import settings

logging.getLogger("sqlalchemy.engine").setLevel(logging.ERROR)


class Base(DeclarativeBase):
    """Base class for all database models."""


def create_database_engine(database_url: str) -> Engine:
    """
    Create the engine, the SQLite folder included, with foreign keys enforced.

    SQLite ignores foreign keys unless every connection turns them on, so ``ON DELETE CASCADE``
    would silently do nothing without the pragma.

    Args:
        database_url: SQLAlchemy URL, ``sqlite:///./data/la-bonne-truffe.db`` by default.

    Returns:
        The engine.
    """
    url = make_url(database_url)
    is_sqlite = url.get_backend_name() == "sqlite"
    if is_sqlite and url.database and url.database != ":memory:":
        Path(url.database).parent.mkdir(parents=True, exist_ok=True)

    connect_args: dict[str, object] = {"check_same_thread": False} if is_sqlite else {}
    database_engine = create_engine(database_url, connect_args=connect_args, echo=False)

    if is_sqlite:

        @event.listens_for(database_engine, "connect")
        def enable_sqlite_foreign_keys(dbapi_connection: object, _connection_record: object) -> None:
            """Turn foreign keys on for every new SQLite connection."""
            cursor = dbapi_connection.cursor()  # type: ignore[attr-defined]
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return database_engine


engine = create_database_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Iterator[Session]:
    """
    Database dependency for FastAPI routes.

    Yields:
        A session, closed once the request is over.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db(database_engine: Engine | None = None) -> None:
    """
    Create the table of every model that has none yet; an existing table is never altered.

    The ``models`` package imports every model, which registers its table.

    Args:
        database_engine: Engine to create the tables on, the application one by default.
    """
    import models  # noqa: F401

    Base.metadata.create_all(bind=database_engine or engine)
