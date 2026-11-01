"""Where the app found a social account of a breeding: its Centrale Canine site, its own site, or added by hand."""

from enum import StrEnum


class SocialLinkOrigin(StrEnum):
    """Where the app found a social account of a breeding: its Centrale Canine site, its own site, or added by hand."""

    CENTRALE_CANINE = "centrale_canine"
    BREEDER_SITE = "breeder_site"
    ADDED_BY_HAND = "added_by_hand"
