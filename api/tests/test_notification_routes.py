"""Notification routes: subscription lifecycle, VAPID key, test push, bell history."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from core.config import settings
from enums.notification_kind import NotificationKind
from models.notification import Notification
from models.push_subscription import PushSubscription
from models.user import User

SUBSCRIPTION = {
    "endpoint": "https://web.push.apple.com/abc",
    "keys": {"p256dh": "client-public-key", "auth": "client-auth"},
    "user_agent": "iPad",
}


def test_subscribe_then_resubscribe_keeps_a_single_row(
    client: TestClient, auth_headers: dict[str, str], db: Session
) -> None:
    assert client.post("/api/v1/notifications/subscribe", json=SUBSCRIPTION, headers=auth_headers).status_code == 204
    refreshed = {**SUBSCRIPTION, "keys": {"p256dh": "new-key", "auth": "new-auth"}}
    assert client.post("/api/v1/notifications/subscribe", json=refreshed, headers=auth_headers).status_code == 204

    rows = db.query(PushSubscription).all()
    assert len(rows) == 1
    assert rows[0].p256dh == "new-key"


def test_unsubscribe_removes_the_endpoint(client: TestClient, auth_headers: dict[str, str], db: Session) -> None:
    client.post("/api/v1/notifications/subscribe", json=SUBSCRIPTION, headers=auth_headers)

    response = client.request(
        "DELETE",
        "/api/v1/notifications/subscribe",
        json={"endpoint": SUBSCRIPTION["endpoint"]},
        headers=auth_headers,
    )

    assert response.status_code == 204
    assert db.query(PushSubscription).count() == 0


def test_vapid_key_reports_missing_configuration(
    client: TestClient, auth_headers: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings, "vapid_public_key", None)
    monkeypatch.setattr(settings, "vapid_private_key_b64", None)

    body = client.get("/api/v1/notifications/vapid-key", headers=auth_headers).json()

    assert body == {"public_key": None, "configured": False}


def test_test_push_explains_missing_configuration(
    client: TestClient, auth_headers: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings, "vapid_private_key_b64", None)

    body = client.post("/api/v1/notifications/test", headers=auth_headers).json()

    assert body["configured"] is False
    assert body["delivered"] == 0
    assert body["detail"] == "VAPID not configured"


def test_history_counts_unread_until_read_all(
    client: TestClient, auth_headers: dict[str, str], user: User, db: Session
) -> None:
    for index in range(3):
        db.add(Notification(user_id=user.id, kind=NotificationKind.NEW_PREFERRED, title="t", body=f"b{index}", url="/"))
    db.commit()

    history = client.get("/api/v1/notifications", headers=auth_headers).json()
    assert history["unread_count"] == 3
    assert [item["body"] for item in history["items"]] == ["b2", "b1", "b0"]

    assert client.post("/api/v1/notifications/read-all", headers=auth_headers).status_code == 204
    assert client.get("/api/v1/notifications", headers=auth_headers).json()["unread_count"] == 0


def test_notification_routes_require_authentication(client: TestClient) -> None:
    assert client.get("/api/v1/notifications/vapid-key").status_code == 401
    assert client.post("/api/v1/notifications/subscribe", json=SUBSCRIPTION).status_code == 401
