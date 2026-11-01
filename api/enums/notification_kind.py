"""Event a sent notification reports (see docs/04-correspondance-et-notifications.md)."""

from enum import StrEnum


class NotificationKind(StrEnum):
    """Event a sent notification reports (see docs/04-correspondance-et-notifications.md)."""

    NEW_PREFERRED = "new_preferred"
    BORN = "born"
    UPGRADED = "upgraded"
    EVENING_DIGEST = "evening_digest"
    SOURCE_DOWN = "source_down"
    SOURCE_SILENT = "source_silent"
    SIGNUP_REQUEST = "signup_request"
    FOLLOW_UP_REMINDER = "follow_up_reminder"
    BREEDER_NEW_MATING = "breeder_new_mating"
    BREEDER_BIRTH = "breeder_birth"
    BREEDER_NEW_PHOTOS = "breeder_new_photos"
    BREEDER_NEW_AD = "breeder_new_ad"
    BREEDER_FOLLOW_REMINDER = "breeder_follow_reminder"
