"""Where the puppy of an ad stands: still offered, reserved, or sold."""

from enum import StrEnum


class PuppyAdState(StrEnum):
    """Where the puppy of an ad stands: still offered, reserved, or sold."""

    AVAILABLE = "available"
    RESERVED = "reserved"
    SOLD = "sold"
