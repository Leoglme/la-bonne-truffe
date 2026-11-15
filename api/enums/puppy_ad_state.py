"""Where the puppy of an ad stands: still offered, being reserved, reserved, or sold."""

from enum import StrEnum


class PuppyAdState(StrEnum):
    """
    Where the puppy of an ad stands: still offered, being reserved (a family asked for it and the breeder waits
    for its deposit: the puppy may come back), reserved, or sold.
    """

    AVAILABLE = "available"
    BEING_RESERVED = "being_reserved"
    RESERVED = "reserved"
    SOLD = "sold"
