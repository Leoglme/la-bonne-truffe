"""Signup, signup requests while signups are closed, and forgotten password routes."""

from urllib.parse import parse_qs, urlparse

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from api.v1.routes import auth as auth_routes
from core.config import settings
from enums.notification_kind import NotificationKind
from models.notification import Notification
from models.search_profile import SearchProfile
from models.signup_request import SignupRequest
from models.user import User
from services.account_service import AccountService
from services.auth_service import AuthService
from services.email_service import EmailMessage, EmailService
from services.search_profile_service import STARTING_PROFILE_NAME
from tests.conftest import TEST_PASSWORD

NEW_PASSWORD = "nouvelle-truffe-35"


class RecordingEmailService(EmailService):
    """Keeps the emails the API sends instead of handing them to Resend."""

    def __init__(self) -> None:
        super().__init__()
        self.sent_messages: list[EmailMessage] = []

    def send(self, message: EmailMessage) -> bool:
        """
        Keep the message.

        Args:
            message: The email.

        Returns:
            Always True, as Resend does when it accepts a message.
        """
        self.sent_messages.append(message)
        return True


@pytest.fixture
def sent_emails(monkeypatch: pytest.MonkeyPatch) -> list[EmailMessage]:
    """The emails the routes send during the test, through a fresh account service that has sent nothing yet."""
    mailer = RecordingEmailService()
    monkeypatch.setattr(auth_routes, "account_service", AccountService(mailer))
    return mailer.sent_messages


@pytest.fixture
def open_signups(monkeypatch: pytest.MonkeyPatch) -> None:
    """Signups open for the test (``SIGNUP_ENABLED=true``); they are closed by default."""
    monkeypatch.setattr(settings, "signup_enabled", True)


def reset_token_of(message: EmailMessage) -> str:
    """The token of the link written in a reset email."""
    link = next(word for word in message.text.split() if word.startswith("http"))
    return parse_qs(urlparse(link).query)["token"][0]


@pytest.mark.usefixtures("open_signups")
def test_signup_signs_in_with_the_starting_profile(client: TestClient, db: Session) -> None:
    response = client.post(
        "/api/v1/auth/signup", json={"name": "  Marie ", "email": "marie@exemple.fr", "password": "gold-et-redon-35"}
    )

    assert response.status_code == 201
    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {response.json()['access_token']}"})
    assert me.json()["user"]["name"] == "Marie"
    account = db.query(User).filter(User.email == "marie@exemple.fr").one()
    profile = db.query(SearchProfile).filter(SearchProfile.user_id == account.id).one()
    assert profile.name == STARTING_PROFILE_NAME
    assert profile.department_codes[0] == "35"


@pytest.mark.usefixtures("open_signups")
def test_signup_stores_the_email_in_lowercase_and_login_ignores_case(client: TestClient) -> None:
    client.post("/api/v1/auth/signup", json={"name": "Marie", "email": "Marie@Exemple.FR", "password": "gold-35-gold"})

    login = client.post("/api/v1/auth/login", json={"email": "MARIE@exemple.fr", "password": "gold-35-gold"})

    assert login.status_code == 200


@pytest.mark.usefixtures("open_signups")
def test_signup_refuses_an_email_that_has_an_account(client: TestClient, user: User) -> None:
    response = client.post(
        "/api/v1/auth/signup", json={"name": "Léo", "email": user.email.upper(), "password": "gold-et-redon-35"}
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Un compte existe déjà avec cette adresse."


@pytest.mark.parametrize("password", ["court-1", "sans-aucun-chiffre"])
def test_signup_refuses_a_password_below_the_announced_rule(client: TestClient, password: str) -> None:
    response = client.post(
        "/api/v1/auth/signup", json={"name": "Marie", "email": "marie@exemple.fr", "password": password}
    )

    assert response.status_code == 422


def test_signup_is_closed_by_default(client: TestClient, db: Session) -> None:
    response = client.post(
        "/api/v1/auth/signup", json={"name": "Marie", "email": "marie@exemple.fr", "password": "gold-et-redon-35"}
    )

    assert response.status_code == 403
    assert db.query(User).count() == 0


def test_signup_availability_follows_the_setting(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    closed = client.get("/api/v1/auth/signup-availability").json()
    monkeypatch.setattr(settings, "signup_enabled", True)
    opened = client.get("/api/v1/auth/signup-availability").json()

    assert (closed, opened) == ({"is_open": False}, {"is_open": True})


def test_a_signup_request_is_kept_and_pushed_to_the_admin_once(client: TestClient, db: Session, user: User) -> None:
    first = client.post("/api/v1/auth/signup-requests", json={"name": "Marie", "email": "marie@exemple.fr"})
    again = client.post("/api/v1/auth/signup-requests", json={"name": "Marie-Anne", "email": "Marie@Exemple.fr"})

    assert first.status_code == again.status_code == 202
    assert first.json() == again.json() == {"email": "marie@exemple.fr"}
    signup_request = db.query(SignupRequest).one()
    assert (signup_request.name, signup_request.email) == ("Marie-Anne", "marie@exemple.fr")
    notification = db.query(Notification).one()
    assert (notification.user_id, notification.kind) == (user.id, NotificationKind.SIGNUP_REQUEST)
    assert notification.body == "Demande d’inscription : Marie (marie@exemple.fr) aimerait utiliser La Bonne Truffe."


def test_a_signup_request_from_an_account_is_answered_alike_and_not_kept(
    client: TestClient, db: Session, user: User
) -> None:
    response = client.post("/api/v1/auth/signup-requests", json={"name": "Léo", "email": user.email.upper()})

    assert response.status_code == 202
    assert response.json() == {"email": user.email}
    assert db.query(SignupRequest).count() == db.query(Notification).count() == 0


def test_forgot_password_emails_a_link_that_opens_the_reset_screen(
    client: TestClient, user: User, sent_emails: list[EmailMessage]
) -> None:
    response = client.post("/api/v1/auth/forgot-password", json={"email": user.email})

    assert response.status_code == 202
    assert response.json() == {"expires_in_minutes": 30, "resend_delay_seconds": 45}
    assert [message.to_email for message in sent_emails] == [user.email]
    assert f"{settings.web_base_url}/nouveau-mot-de-passe?token=" in sent_emails[0].text
    verify = client.post("/api/v1/auth/reset-password/verify", json={"token": reset_token_of(sent_emails[0])})
    assert verify.json() == {"email": user.email}


def test_forgot_password_answers_the_same_for_an_address_without_account(
    client: TestClient, user: User, sent_emails: list[EmailMessage]
) -> None:
    known = client.post("/api/v1/auth/forgot-password", json={"email": user.email})
    unknown = client.post("/api/v1/auth/forgot-password", json={"email": "personne@exemple.fr"})

    assert unknown.status_code == known.status_code == 202
    assert unknown.json() == known.json()
    assert len(sent_emails) == 1


def test_forgot_password_waits_before_sending_another_link(
    client: TestClient, user: User, sent_emails: list[EmailMessage]
) -> None:
    client.post("/api/v1/auth/forgot-password", json={"email": user.email})
    client.post("/api/v1/auth/forgot-password", json={"email": user.email})

    assert len(sent_emails) == 1


def test_reset_password_changes_the_password_and_signs_in(
    client: TestClient, user: User, sent_emails: list[EmailMessage]
) -> None:
    client.post("/api/v1/auth/forgot-password", json={"email": user.email})

    response = client.post(
        "/api/v1/auth/reset-password", json={"token": reset_token_of(sent_emails[0]), "password": NEW_PASSWORD}
    )

    assert response.status_code == 200
    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {response.json()['access_token']}"})
    assert me.json()["user"]["email"] == user.email
    old_login = client.post("/api/v1/auth/login", json={"email": user.email, "password": TEST_PASSWORD})
    new_login = client.post("/api/v1/auth/login", json={"email": user.email, "password": NEW_PASSWORD})
    assert (old_login.status_code, new_login.status_code) == (401, 200)


def test_a_reset_link_works_once(client: TestClient, user: User, sent_emails: list[EmailMessage]) -> None:
    client.post("/api/v1/auth/forgot-password", json={"email": user.email})
    token = reset_token_of(sent_emails[0])
    client.post("/api/v1/auth/reset-password", json={"token": token, "password": NEW_PASSWORD})

    second_reset = client.post("/api/v1/auth/reset-password", json={"token": token, "password": "encore-une-35"})
    verify = client.post("/api/v1/auth/reset-password/verify", json={"token": token})

    assert (second_reset.status_code, verify.status_code) == (400, 400)
    assert verify.json()["detail"] == "Ce lien a expiré ou a déjà servi."


def test_a_reset_link_expires(client: TestClient, user: User, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "password_reset_token_expire_minutes", -1)
    token = AuthService.create_password_reset_token(user)

    response = client.post("/api/v1/auth/reset-password/verify", json={"token": token})

    assert response.status_code == 400


def test_reset_password_refuses_a_password_below_the_rule(client: TestClient, user: User) -> None:
    token = AuthService.create_password_reset_token(user)

    response = client.post("/api/v1/auth/reset-password", json={"token": token, "password": "sans-chiffre"})

    assert response.status_code == 422


def test_reset_and_access_tokens_cannot_stand_in_for_each_other(client: TestClient, user: User) -> None:
    reset_token = AuthService.create_password_reset_token(user)
    access_token = AuthService.create_access_token(user.email)

    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {reset_token}"})
    verify = client.post("/api/v1/auth/reset-password/verify", json={"token": access_token})

    assert (me.status_code, verify.status_code) == (401, 400)
