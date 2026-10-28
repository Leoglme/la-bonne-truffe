"""Login and signed-in user routes."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from models.user import User
from tests.conftest import TEST_PASSWORD


def test_login_returns_a_token_that_opens_me(client: TestClient, user: User) -> None:
    login = client.post("/api/v1/auth/login", json={"email": user.email, "password": TEST_PASSWORD})

    assert login.status_code == 200
    token = login.json()["access_token"]
    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == user.email


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
