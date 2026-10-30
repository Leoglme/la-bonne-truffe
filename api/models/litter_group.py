"""LitterGroup model: one real litter, seen on one or several sources."""

from datetime import date, datetime

from sqlalchemy import JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from core.clock import naive_utc_now
from core.database import Base
from models.timestamps import TimestampMixin


class LitterGroup(TimestampMixin, Base):
    """
    A real litter, grouping the listings of every source that describe it.

    Attributes:
        id: Primary key.
        breed_id: Breed of the litter.
        breeder_id: Breeder, null when unknown.
        birth_date: Declared birth date.
        expected_birth_date: Mating date + 63 days while the birth is not declared.
        mating_date: Declared mating date.
        available_from: Birth (or expected birth) + 56 days, the legal handover age.
        is_active: False once every listing is gone, or six months after the birth.
        is_grouping_probable: True when listings were grouped on a guess (no birth date, single candidate).
        confirmed_colors: Canonical colours confirmed by hand after a call; they override every source.
        confirmed_male_count: Males confirmed by hand after a call, with the females; they override every source.
        confirmed_female_count: Females confirmed by hand after a call, with the males.
        puppies_available: Puppies the litter still offers across its active listings, null while no source tells.
        first_seen_at: First time a source showed this litter.
        last_seen_at: Last time a source showed this litter.
    """

    __tablename__ = "litter_groups"

    id: Mapped[int] = mapped_column(primary_key=True)
    breed_id: Mapped[int] = mapped_column(ForeignKey("breeds.id"), nullable=False, index=True)
    breeder_id: Mapped[int | None] = mapped_column(ForeignKey("breeders.id", ondelete="SET NULL"), index=True)
    birth_date: Mapped[date | None]
    expected_birth_date: Mapped[date | None]
    mating_date: Mapped[date | None]
    available_from: Mapped[date | None]
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False, index=True)
    is_grouping_probable: Mapped[bool] = mapped_column(default=False, nullable=False)
    confirmed_colors: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    confirmed_male_count: Mapped[int | None]
    confirmed_female_count: Mapped[int | None]
    puppies_available: Mapped[int | None]
    first_seen_at: Mapped[datetime] = mapped_column(default=naive_utc_now, nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(default=naive_utc_now, nullable=False)

    def __repr__(self) -> str:
        return f"<LitterGroup id={self.id} breeder_id={self.breeder_id}>"
