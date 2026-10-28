"""Shared test setup: an in-memory database per test, the app wired to it, a seeded user."""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import models  # noqa: F401
from core.config import settings
from core.database import Base, get_db
from main import app
from models.user import User
from services.auth_service import AuthService

TEST_PASSWORD = "truffe-de-test"


@pytest.fixture
def engine() -> Engine:
    """An empty in-memory SQLite database with every table and foreign keys enforced."""
    database_engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)

    @event.listens_for(database_engine, "connect")
    def enable_foreign_keys(dbapi_connection: object, _connection_record: object) -> None:
        """Turn foreign keys on, as the application engine does."""
        cursor = dbapi_connection.cursor()  # type: ignore[attr-defined]
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(database_engine)
    return database_engine


@pytest.fixture
def db(engine: Engine) -> Iterator[Session]:
    """A session on the test's database, closed afterwards."""
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(engine: Engine) -> Iterator[TestClient]:
    """The FastAPI app, every request served by the test's database."""
    session_factory = sessionmaker(bind=engine)

    def override_get_db() -> Iterator[Session]:
        """Yield a session on the test database."""
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def user(db: Session) -> User:
    """The single dashboard user, with a known password."""
    account = User(
        name="Léo",
        email=settings.admin_email,
        hashed_password=AuthService.hash_password(TEST_PASSWORD),
        is_active=True,
    )
    db.add(account)
    db.commit()
    return account


@pytest.fixture
def auth_headers(user: User) -> dict[str, str]:
    """Bearer header of the seeded user."""
    return {"Authorization": f"Bearer {AuthService.create_access_token(user.email)}"}
