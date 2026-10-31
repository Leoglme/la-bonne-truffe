"""Events of a followed breeder that notify (docs/04, « Les alertes d'éleveur »)."""

from enum import StrEnum


class BreederEventKind(StrEnum):
    """An event of a followed breeder; each (follow, litter, kind) is notified once, new photos at every batch."""

    NEW_MATING = "breeder_new_mating"
    BIRTH = "breeder_birth"
    NEW_PHOTOS = "breeder_new_photos"
    NEW_AD = "breeder_new_ad"
