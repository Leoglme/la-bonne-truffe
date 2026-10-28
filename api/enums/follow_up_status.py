"""Where the exchange with a breeder stands."""

from enum import StrEnum


class FollowUpStatus(StrEnum):
    """Where the exchange with a breeder stands."""

    NEW = "new"
    TO_CONTACT = "to_contact"
    CONTACTED = "contacted"
    WAITING = "waiting"
    RESERVED = "reserved"
    DISMISSED = "dismissed"
