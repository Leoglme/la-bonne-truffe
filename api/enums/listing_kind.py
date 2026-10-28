"""Listing kind enum."""

from enum import StrEnum


class ListingKind(StrEnum):
    """What a listing describes: a born litter, a declared mating, or a puppy ad."""

    LITTER_BORN = "litter_born"
    LITTER_EXPECTED = "litter_expected"
    PUPPY_AD = "puppy_ad"
