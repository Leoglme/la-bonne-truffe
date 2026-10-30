"""Listing model: one announcement or one declaration, as one source publishes it."""

from datetime import date, datetime
from typing import Any

from sqlalchemy import JSON, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from core.clock import naive_utc_now
from core.database import Base
from enums.listing_kind import ListingKind
from enums.listing_source import ListingSource
from enums.lof_status import LofStatus
from models.enum_column import str_enum_column
from models.timestamps import TimestampMixin


class Listing(TimestampMixin, Base):
    """
    An announcement or a declaration read from a source, one row per ``source`` + ``external_id``.

    Attributes:
        id: Primary key.
        source: ``ListingSource`` value.
        external_id: Identifier on the source.
        external_url: Public page of the listing on the source.
        breed_id: Breed.
        breeder_id: Breeder, once matched.
        litter_group_id: Real litter the listing belongs to, once grouped.
        kind: ``ListingKind`` value.
        lof_status: ``LofStatus`` value.
        litter_number: LOF litter number, empty for a mating.
        mating_date: Mating date.
        birth_date: Birth date.
        male_count: Number of males at birth (0 before the birth at the Centrale Canine).
        female_count: Number of females at birth.
        puppies_available: Puppies still available, when the ad says so.
        variety_source_id: Colour variety identifier on the source.
        colors: Canonical colours, each ``{"color": CoatColor, "confidence": ColorConfidence}``.
        color_text: Free colour text as the source writes it.
        price_cents: Price, when published.
        department_code: Department code.
        zip_code: Postal code.
        city: Town.
        sire_name: Father's name.
        sire_rating: Father's Centrale Canine rating (1 to 6).
        dam_name: Mother's name.
        dam_rating: Mother's Centrale Canine rating (1 to 6).
        litter_rating: Litter's overall rating.
        photos: Photo URLs.
        description: Free text of the ad.
        published_at: When the source put the listing online, when it says so (Centrale Canine ``n_created``).
        first_seen_at: First collection that saw the listing.
        last_seen_at: Last collection that saw the listing.
        last_changed_at: Last collection that saw a field change.
        missed_run_count: Consecutive runs that did not see the listing; two make it inactive.
        is_active: False once the listing has left its source.
        raw_json: Raw snapshot from the source.
    """

    __tablename__ = "listings"
    __table_args__ = (UniqueConstraint("source", "external_id", name="uq_listing_source_external_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    source: Mapped[ListingSource] = mapped_column(str_enum_column(ListingSource), nullable=False, index=True)
    external_id: Mapped[str] = mapped_column(String(80), nullable=False)
    external_url: Mapped[str | None] = mapped_column(String(500))
    breed_id: Mapped[int] = mapped_column(ForeignKey("breeds.id"), nullable=False, index=True)
    breeder_id: Mapped[int | None] = mapped_column(ForeignKey("breeders.id", ondelete="SET NULL"), index=True)
    litter_group_id: Mapped[int | None] = mapped_column(ForeignKey("litter_groups.id", ondelete="SET NULL"), index=True)
    kind: Mapped[ListingKind] = mapped_column(
        str_enum_column(ListingKind), default=ListingKind.LITTER_BORN, nullable=False
    )
    lof_status: Mapped[LofStatus] = mapped_column(str_enum_column(LofStatus), default=LofStatus.UNKNOWN, nullable=False)
    litter_number: Mapped[str | None] = mapped_column(String(60))
    mating_date: Mapped[date | None]
    birth_date: Mapped[date | None]
    male_count: Mapped[int | None]
    female_count: Mapped[int | None]
    puppies_available: Mapped[int | None]
    variety_source_id: Mapped[str | None] = mapped_column(String(40))
    colors: Mapped[list[dict[str, str]]] = mapped_column(JSON, default=list, nullable=False)
    color_text: Mapped[str | None] = mapped_column(String(255))
    price_cents: Mapped[int | None]
    department_code: Mapped[str | None] = mapped_column(ForeignKey("departments.code"), index=True)
    zip_code: Mapped[str | None] = mapped_column(String(10))
    city: Mapped[str | None] = mapped_column(String(120))
    sire_name: Mapped[str | None] = mapped_column(String(255))
    sire_rating: Mapped[int | None]
    dam_name: Mapped[str | None] = mapped_column(String(255))
    dam_rating: Mapped[int | None]
    litter_rating: Mapped[float | None]
    photos: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    published_at: Mapped[datetime | None]
    first_seen_at: Mapped[datetime] = mapped_column(default=naive_utc_now, nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(default=naive_utc_now, nullable=False)
    last_changed_at: Mapped[datetime | None]
    missed_run_count: Mapped[int] = mapped_column(default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False, index=True)
    raw_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    def __repr__(self) -> str:
        return f"<Listing id={self.id} source={self.source} external_id={self.external_id}>"
