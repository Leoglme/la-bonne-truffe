"""Where the puppy of a puppy ad stands: still offered, reserved or sold (docs/02)."""

from core.text import without_accents
from enums.listing_kind import ListingKind
from enums.puppy_ad_state import PuppyAdState
from models.listing import Listing

SOLD_STATUS_WORDS: tuple[str, ...] = ("vendu", "adopte")
RESERVED_STATUS_WORD = "reserv"
AVAILABLE_STATUS_WORD = "disponible"


class PuppyAdStateReader:
    """Reads the state of a puppy from its ad, for the puppies of the litter page and the colours of the litter."""

    @staticmethod
    def state_of(listing: Listing) -> PuppyAdState | None:
        """
        Where the puppy of a puppy ad stands, from its status line (« Femelle réservée », « Mâle vendu ») or,
        failing that, from whether the ad still offers it.

        Args:
            listing: The listing.

        Returns:
            The state, None for a litter listing or a puppy ad that tells nothing.
        """
        if listing.kind != ListingKind.PUPPY_AD:
            return None
        status_text = without_accents(str((listing.raw_json or {}).get("status") or "")).lower()
        if any(word in status_text for word in SOLD_STATUS_WORDS):
            return PuppyAdState.SOLD
        if RESERVED_STATUS_WORD in status_text:
            return PuppyAdState.RESERVED
        if listing.puppies_available == 1 or AVAILABLE_STATUS_WORD in status_text:
            return PuppyAdState.AVAILABLE
        if listing.puppies_available == 0:
            return PuppyAdState.RESERVED
        return None
