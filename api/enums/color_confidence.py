"""How sure a listing's colour is."""

from enum import StrEnum


class ColorConfidence(StrEnum):
    """
    How sure a colour is: certain, ambiguous source bundle, confirmed by hand, inferred from the parents, or
    suggested by the AI from the photo of a puppy.

    An inferred colour counts as certain for the tier and the score (docs/04, « Les couleurs données par les
    chiens »): two gold parents only give gold puppies. A suggested colour counts as certain too: it is only read
    when no source gives the colour of the puppy, and the app says where it comes from.
    """

    CERTAIN = "certain"
    AMBIGUOUS = "ambiguous"
    CONFIRMED = "confirmed"
    INFERRED = "inferred"
    SUGGESTED = "suggested"
