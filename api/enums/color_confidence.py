"""How sure a listing's colour is."""

from enum import StrEnum


class ColorConfidence(StrEnum):
    """
    How sure a colour is: certain, ambiguous source bundle, confirmed by hand, or inferred from the parents.

    An inferred colour counts as certain for the tier and the score (docs/04, « Les couleurs données par les
    chiens »): two gold parents only give gold puppies.
    """

    CERTAIN = "certain"
    AMBIGUOUS = "ambiguous"
    CONFIRMED = "confirmed"
    INFERRED = "inferred"
