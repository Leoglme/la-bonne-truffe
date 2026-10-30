"""Web Push notification schemas: VAPID key, subscription payload, test result, history."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from enums.match_event_kind import MatchEventKind
from enums.notification_kind import NotificationKind
from schemas.litter import LitterCard


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


class NotificationLitter(LitterCard):
    """A litter as a notification shows it: its card, the breeder's phone, and its part in a digest."""

    breeder_phone_e164: str | None = Field(description="Phone of the breeder, for the call button of a reminder")
    digest_event: MatchEventKind | None = Field(default=None, description="Its event in a digest; null elsewhere")


class NotificationResponse(BaseModel):
    """One sent notification, as the bell lists it, with the litters it is about."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    kind: NotificationKind
    title: str
    body: str
    url: str
    litter_group_id: int | None
    sent_at: datetime
    read_at: datetime | None
    litter: NotificationLitter | None = Field(description="The litter of the notification, when it can still be read")
    litters: list[NotificationLitter] = Field(description="The litters of an evening digest, empty elsewhere")


class NotificationListResponse(BaseModel):
    """A page of the notification history plus the unread count that lights the bell."""

    items: list[NotificationResponse]
    unread_count: int
