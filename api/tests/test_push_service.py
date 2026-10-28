"""PushService: delivery, stale endpoint pruning, VAPID key generation."""

import base64
from types import SimpleNamespace

import pytest
from pywebpush import WebPushException
from sqlalchemy.orm import Session

from core.config import settings
from models.push_subscription import PushSubscription
from models.user import User
from services import push_service as push_service_module
from services.push_service import push_service
from services.vapid_key_generator import VapidKeyGenerator


@pytest.fixture
def vapid_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    """A freshly generated VAPID pair in the settings."""
    key_pair = VapidKeyGenerator.generate()
    monkeypatch.setattr(settings, "vapid_public_key", key_pair.public_key)
    monkeypatch.setattr(settings, "vapid_private_key_b64", key_pair.private_key_b64)


def subscribe(db: Session, user: User, endpoint: str) -> None:
    """Register one browser for the user."""
    db.add(PushSubscription(user_id=user.id, endpoint=endpoint, p256dh="k", auth="a"))
    db.commit()


def test_generated_public_key_is_an_uncompressed_p256_point() -> None:
    public_key = VapidKeyGenerator.generate().public_key

    point = base64.urlsafe_b64decode(public_key + "=" * (-len(public_key) % 4))

    assert len(point) == 65
    assert point[0] == 0x04


def test_send_delivers_to_every_subscription(
    db: Session, user: User, vapid_configured: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    subscribe(db, user, "https://push.example/one")
    subscribe(db, user, "https://push.example/two")
    sent_payloads: list[str] = []
    monkeypatch.setattr(push_service_module, "webpush", lambda **kwargs: sent_payloads.append(kwargs["data"]))

    result = push_service.send(db, user.id, "La Bonne Truffe", "Une portée gold", "/portees/1")

    assert (result.delivered, result.failed) == (2, 0)
    assert '"url": "/portees/1"' in sent_payloads[0]


def test_send_prunes_endpoints_the_push_service_forgot(
    db: Session, user: User, vapid_configured: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    subscribe(db, user, "https://push.example/gone")

    def answer_gone(**_kwargs: object) -> None:
        """Behave like a push service that no longer knows the endpoint."""
        raise WebPushException("Gone", response=SimpleNamespace(status_code=410))

    monkeypatch.setattr(push_service_module, "webpush", answer_gone)

    result = push_service.send(db, user.id, "t", "b", "/")

    assert result.failed == 1
    assert db.query(PushSubscription).count() == 0
