"""What a link added to a breeder by hand leads to: its site on Chiens de France, a social account, or another site."""

from enum import StrEnum


class BreederLinkKind(StrEnum):
    """What a link added to a breeder by hand leads to: its site on Chiens de France, a social account, or another site."""

    CHIENS_DE_FRANCE_SITE = "chiens_de_france_site"
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    YOUTUBE = "youtube"
    WEBSITE = "website"
