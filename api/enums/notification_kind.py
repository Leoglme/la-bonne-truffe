"""Event a sent notification reports (see docs/04-correspondance-et-notifications.md)."""

from enum import StrEnum


class NotificationKind(StrEnum):
    """Event a sent notification reports (see docs/04-correspondance-et-notifications.md)."""

    NEW_PREFERRED = "new_preferred"
    BORN = "born"
    UPGRADED = "upgraded"
    EVENING_DIGEST = "evening_digest"
    SOURCE_DOWN = "source_down"
    SIGNUP_REQUEST = "signup_request"
    TEST = "test"
