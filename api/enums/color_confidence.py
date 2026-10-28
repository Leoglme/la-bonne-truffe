"""How sure a listing's colour is."""

from enum import StrEnum


class ColorConfidence(StrEnum):
    """How sure a listing's colour is: certain, ambiguous source bundle, or confirmed by hand."""

    CERTAIN = "certain"
    AMBIGUOUS = "ambiguous"
    CONFIRMED = "confirmed"
