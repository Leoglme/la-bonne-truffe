"""Keeps the social accounts of a breeding with where each one was found (docs/03, ``social_link_origins``)."""

from enums.social_link_origin import SocialLinkOrigin
from models.breeder import Breeder


class BreederSocialLinks:
    """Writes a Facebook, Instagram or YouTube address on a breeder, and notes where it comes from."""

    @staticmethod
    def keep(breeder: Breeder, account: str, address: str | None, origin: SocialLinkOrigin) -> bool:
        """
        Store one account: an address added by hand replaces any other; the one a Centrale Canine site declares
        replaces all but a hand-added one; the one a breeder's site shows only fills an empty place.

        Args:
            breeder: The breeder.
            account: ``facebook``, ``instagram`` or ``youtube``.
            address: The address found, None when none.
            origin: Where it was found.

        Returns:
            Whether the breeder changed.
        """
        if address is None:
            return False
        current_address: str | None = getattr(breeder, f"{account}_url")
        current_origin = breeder.social_link_origins.get(account)
        if current_address is not None:
            if origin == SocialLinkOrigin.BREEDER_SITE:
                return False
            if origin == SocialLinkOrigin.CENTRALE_CANINE and current_origin == SocialLinkOrigin.ADDED_BY_HAND:
                return False
        if current_address == address and current_origin == origin:
            return False
        setattr(breeder, f"{account}_url", address)
        breeder.social_link_origins = {**breeder.social_link_origins, account: origin.value}
        return True
