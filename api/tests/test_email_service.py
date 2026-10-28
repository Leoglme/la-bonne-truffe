"""Delivery of the account emails through Resend."""

import json

import httpx
import pytest

from core.config import settings
from services.account_emails import AccountEmails
from services.email_service import RESEND_EMAILS_URL, EmailMessage, EmailService

MESSAGE: EmailMessage = AccountEmails.password_reset(
    "marie@exemple.fr", "Marie", "http://localhost:3000/nouveau-mot-de-passe?token=abc", 30
)


def test_the_email_goes_to_resend_with_the_configured_sender(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "resend_api_key", "re_test")
    requests: list[httpx.Request] = []

    def answer(request: httpx.Request) -> httpx.Response:
        """Record the request and accept it, as Resend does."""
        requests.append(request)
        return httpx.Response(200, json={"id": "email-1"})

    was_sent = EmailService(transport=httpx.MockTransport(answer)).send(MESSAGE)

    assert was_sent is True
    assert str(requests[0].url) == RESEND_EMAILS_URL
    assert requests[0].headers["Authorization"] == "Bearer re_test"
    body = json.loads(requests[0].content)
    assert body["from"] == settings.email_from
    assert body["to"] == ["marie@exemple.fr"]
    assert "token=abc" in body["html"]


def test_a_refusal_from_resend_is_logged_not_raised(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "resend_api_key", "re_test")

    def refuse(_request: httpx.Request) -> httpx.Response:
        """Answer as Resend does for an unverified sender domain."""
        return httpx.Response(403, json={"message": "The domain is not verified"})

    assert EmailService(transport=httpx.MockTransport(refuse)).send(MESSAGE) is False


def test_without_a_key_the_email_is_written_to_the_log(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    monkeypatch.setattr(settings, "resend_api_key", "")

    was_sent = EmailService().send(MESSAGE)

    assert was_sent is False
    assert "token=abc" in caplog.text
