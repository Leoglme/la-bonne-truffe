"""Events that notify (docs/04-correspondance-et-notifications.md)."""

from enum import StrEnum


class MatchEventKind(StrEnum):
    """An event of a litter group; each (group, kind) pair is notified once, except a drop of the puppies left."""

    NEW_PREFERRED = "new_preferred"
    BORN = "born"
    NEW_ACCEPTABLE = "new_acceptable"
    UPGRADED = "upgraded"
    AVAILABILITY_CHANGE = "availability_change"
