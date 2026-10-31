"""Where the user stands with a followed breeder (docs/04, « Les alertes d'éleveur »)."""

from enum import StrEnum


class BreederFollowStatus(StrEnum):
    """Where the user stands with a followed breeder: to contact, contacted, on the waiting list, deposit paid."""

    TO_CONTACT = "to_contact"
    CONTACTED = "contacted"
    WAITING = "waiting"
    DEPOSIT = "deposit"
