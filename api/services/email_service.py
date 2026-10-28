"""Sends the account emails through Resend, or writes them to the log when no key is configured."""

import logging
from dataclasses import dataclass

import httpx

from core.config import settings

logger = logging.getLogger(__name__)

RESEND_EMAILS_URL = "https://api.resend.com/emails"
RESEND_TIMEOUT_SECONDS = 10.0


@dataclass(frozen=True)
class EmailMessage:
    """An email ready to leave: recipient, subject, and its plain text and HTML bodies."""

    to_email: str
    subject: str
    text: str
    html: str


class EmailService:
    """Delivers the few emails the API writes, after the response has left (a FastAPI background task)."""

    def __init__(self, transport: httpx.BaseTransport | None = None) -> None:
        """
        Args:
            transport: HTTP transport override, for the tests.
        """
        self._transport = transport

    def send(self, message: EmailMessage) -> bool:
        """
        Send a message. Never raises: the visitor already has their answer, a failure only goes to the log.

        Without ``RESEND_API_KEY`` the message is written to the log, link included, so the flow can be
        followed on a development machine.

        Args:
            message: The email.

        Returns:
            Whether Resend accepted the message; False as well when it was only logged.
        """
        if not settings.resend_api_key:
            logger.warning(
                "RESEND_API_KEY is empty: email « %s » to %s not sent, here is its text:\n%s",
                message.subject,
                message.to_email,
                message.text,
            )
            return False
        try:
            with httpx.Client(transport=self._transport, timeout=RESEND_TIMEOUT_SECONDS) as client:
                response = client.post(
                    RESEND_EMAILS_URL,
                    headers={"Authorization": f"Bearer {settings.resend_api_key}"},
                    json={
                        "from": settings.email_from,
                        "to": [message.to_email],
                        "subject": message.subject,
                        "text": message.text,
                        "html": message.html,
                    },
                )
                response.raise_for_status()
        except httpx.HTTPError as error:
            logger.error("Resend did not take the email to %s: %s", message.to_email, error)
            return False
        return True


email_service = EmailService()
