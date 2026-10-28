"""Source an announcement or a declaration was read from."""

from enum import StrEnum


class ListingSource(StrEnum):
    """Source an announcement or a declaration was read from."""

    CENTRALE_CANINE = "centrale_canine"
    CHIENS_DE_FRANCE = "chiens_de_france"
    CHIOTS_DE_FRANCE = "chiots_de_france"
