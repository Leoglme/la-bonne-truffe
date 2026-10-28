"""The common output of every collector, before it is stored."""

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any


@dataclass(frozen=True)
class ColorReading:
    """One canonical colour of a listing and how sure the source is about it."""

    color: str
    confidence: str

    def as_json(self) -> dict[str, str]:
        """The ``{"color", "confidence"}`` form stored in ``Listing.colors``."""
        return {"color": self.color, "confidence": self.confidence}


@dataclass(frozen=True)
class RawListing:
    """
    A listing as one source describes it, already in the canonical vocabulary.

    Unknown facts stay None: a collector never fills a gap with a guess.
    """

    source: str
    external_id: str
    breed_id: int
    kind: str
    lof_status: str
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
    breeder_source_id: str | None = None
    breeder_selection_group: int | None = None
    source_changed_at: datetime | None = None
    raw_json: dict[str, Any] = field(default_factory=dict)
