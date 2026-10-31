"""Source an announcement, a declaration, a breeder profile or a dog was read from."""

from enum import StrEnum


class ListingSource(StrEnum):
    """
    Source an announcement or a declaration was read from, and the readings that bring breeders and dogs
    instead of litters (docs/05, « Nouveaux relevés »): each has its own runs and its own status.
    """

    CENTRALE_CANINE = "centrale_canine"
    CHIENS_DE_FRANCE = "chiens_de_france"
    CHIOTS_DE_FRANCE = "chiots_de_france"
    WHOOF = "whoof"
    COEUR_DE_COCKER = "coeur_de_cocker"
    SCC_BREEDERS = "scc_breeders"
    SCC_DOGS = "scc_dogs"
    CHIENS_DE_FRANCE_SITES = "chiens_de_france_sites"
