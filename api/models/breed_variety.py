"""BreedVariety model: a colour bundle as one source knows it."""

from sqlalchemy import JSON, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base
from enums.listing_source import ListingSource
from models.enum_column import str_enum_column
from models.timestamps import TimestampMixin


class BreedVariety(TimestampMixin, Base):
    """
    A colour bundle of a breed on one source, mapped to canonical colours.

    The Centrale Canine lumps « noir, noir et feu, marron, marron et feu » into one variety, so a
    variety may cover several canonical colours: it is then ambiguous.

    Attributes:
        id: Primary key.
        breed_id: Breed the variety belongs to.
        source: ``ListingSource`` value.
        source_variety_id: Identifier on the source (``317``), unknown until read from the source.
        label: Label as the source writes it (« rouge et doré »).
        covered_colors: Canonical ``CoatColor`` values the variety covers.
        is_ambiguous: Whether the variety covers more than one canonical colour.
    """

    __tablename__ = "breed_varieties"
    __table_args__ = (UniqueConstraint("breed_id", "source", "label", name="uq_breed_variety_label"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    breed_id: Mapped[int] = mapped_column(ForeignKey("breeds.id", ondelete="CASCADE"), nullable=False, index=True)
    source: Mapped[ListingSource] = mapped_column(str_enum_column(ListingSource), nullable=False)
    source_variety_id: Mapped[str | None] = mapped_column(String(40))
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    covered_colors: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    is_ambiguous: Mapped[bool] = mapped_column(default=False, nullable=False)

    def __repr__(self) -> str:
        return f"<BreedVariety id={self.id} source={self.source} source_variety_id={self.source_variety_id}>"
