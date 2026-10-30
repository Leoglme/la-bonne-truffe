"""Login and the session read by the dashboard, renewed once the token is past half its life."""

from datetime import timedelta
from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from core.config import settings
from models.user import User
from services.auth_service import AuthService
from tests.conftest import TEST_PASSWORD


def read_session(client: TestClient, token: str) -> dict[str, Any]:
    """Call GET /auth/me with a token and return its JSON."""
    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    session: dict[str, Any] = response.json()
    return session


def test_login_returns_a_token_that_opens_me(client: TestClient, user: User) -> None:
    login = client.post("/api/v1/auth/login", json={"email": user.email, "password": TEST_PASSWORD})

    assert login.status_code == 200
    session = read_session(client, login.json()["access_token"])
    assert session["user"]["email"] == user.email
    assert session["renewed_token"] is None


def test_login_refuses_a_wrong_password(client: TestClient, user: User) -> None:
    response = client.post("/api/v1/auth/login", json={"email": user.email, "password": "mauvais"})

    assert response.status_code == 401


def test_login_refuses_an_inactive_account(client: TestClient, user: User, db: Session) -> None:
    user.is_active = False
    db.commit()

    response = client.post("/api/v1/auth/login", json={"email": user.email, "password": TEST_PASSWORD})

    assert response.status_code == 401


def test_me_requires_a_valid_token(client: TestClient, user: User) -> None:
    assert client.get("/api/v1/auth/me").status_code == 401
    assert client.get("/api/v1/auth/me", headers={"Authorization": "Bearer pas-un-jwt"}).status_code == 401


def test_me_renews_a_token_past_half_its_life(client: TestClient, user: User) -> None:
    ageing_token = AuthService.create_access_token(
        user.email, expires_delta=timedelta(minutes=settings.access_token_expire_minutes // 4)
    )

    session = read_session(client, ageing_token)

    renewed_token = session["renewed_token"]
    assert isinstance(renewed_token, str) and renewed_token != ageing_token
    renewed_session = read_session(client, renewed_token)
    assert renewed_session["user"]["email"] == user.email
    assert renewed_session["renewed_token"] is None


def test_me_refuses_an_expired_token(client: TestClient, user: User) -> None:
    expired_token = AuthService.create_access_token(user.email, expires_delta=timedelta(minutes=-1))

    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {expired_token}"})

    assert response.status_code == 401
