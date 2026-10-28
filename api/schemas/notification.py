"""Web Push notification schemas: VAPID key, subscription payload, test result, history."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PushKeys(BaseModel):
    """Client encryption keys from a browser PushSubscription."""

    p256dh: str
    auth: str


class PushSubscriptionCreate(BaseModel):
    """A browser push subscription registered by the PWA."""

    endpoint: str = Field(..., max_length=500)
    keys: PushKeys
    user_agent: str = Field(default="", max_length=400)


class PushSubscriptionDelete(BaseModel):
    """Endpoint to unregister."""

    endpoint: str = Field(..., max_length=500)


class VapidKeyResponse(BaseModel):
    """Public VAPID key exposed to the browser to subscribe."""

    public_key: str | None = None
    configured: bool = False


class TestNotificationResult(BaseModel):
    """Diagnostic returned by the test endpoint so the PWA can tell where push breaks."""

    configured: bool = False
    subscriptions: int = 0
    delivered: int = 0
    failed: int = 0
    detail: str | None = None


class NotificationResponse(BaseModel):
    """One sent notification, as the bell lists it."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    kind: str
    title: str
    body: str
    url: str
    litter_group_id: int | None
    sent_at: datetime
    read_at: datetime | None


class NotificationListResponse(BaseModel):
    """A page of the notification history plus the unread count that lights the bell."""

    items: list[NotificationResponse]
    unread_count: int
