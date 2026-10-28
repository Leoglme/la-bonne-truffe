"""The common output of every collector, before it is stored."""

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any

from enums.coat_color import CoatColor
from enums.color_confidence import ColorConfidence
from enums.listing_kind import ListingKind
from enums.listing_source import ListingSource
from enums.lof_status import LofStatus


@dataclass(frozen=True)
class ColorReading:
    """One canonical colour of a listing and how sure the source is about it."""

    color: CoatColor
    confidence: ColorConfidence

    def as_json(self) -> dict[str, str]:
        """The ``{"color", "confidence"}`` form stored in ``Listing.colors``."""
        return {"color": self.color.value, "confidence": self.confidence.value}


@dataclass(frozen=True)
class RawBreeder:
    """
    A breeder as one source describes it, already cleaned. Unknown facts stay None.

    ``source_id`` is the breeder's identifier on that source; the matching across sources uses the
    SIREN first, then the phone, then the affix and the department (docs/03-modele-de-donnees.md).
    """

    source_id: str
    display_name: str | None = None
    affix: str | None = None
    siren: str | None = None
    phone_e164: str | None = None
    zip_code: str | None = None
    city: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    selection_group: int | None = None


@dataclass(frozen=True)
class RawListing:
    """
    A listing as one source describes it, already in the canonical vocabulary.

    Unknown facts stay None: a collector never fills a gap with a guess.
    """

    source: ListingSource
    external_id: str
    breed_id: int
    kind: ListingKind
    lof_status: LofStatus
    external_url: str | None = None
    litter_number: str | None = None
    mating_date: date | None = None
    birth_date: date | None = None
    male_count: int | None = None
    female_count: int | None = None
    puppies_available: int | None = None
    variety_source_id: str | None = None
    colors: tuple[ColorReading, ...] = ()
    color_text: str | None = None
    price_cents: int | None = None
    department_code: str | None = None
    zip_code: str | None = None
    city: str | None = None
    sire_name: str | None = None
    sire_rating: int | None = None
    dam_name: str | None = None
    dam_rating: int | None = None
    litter_rating: float | None = None
    photos: tuple[str, ...] = ()
    description: str | None = None
    breeder: RawBreeder | None = None
    published_at: datetime | None = None
    raw_json: dict[str, Any] = field(default_factory=dict)
