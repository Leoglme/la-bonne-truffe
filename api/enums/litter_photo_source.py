"""Where the photo of a litter card comes from."""

from enum import StrEnum


class LitterPhotoSource(StrEnum):
    """An ad of the litter, else a parent: a litter without photo shows its mother, else its father."""

    LISTING = "listing"
    DAM = "dam"
    SIRE = "sire"
