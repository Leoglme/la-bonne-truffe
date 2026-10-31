"""Dog model: a parent, a reproducer or a puppy known from a source (docs/03, « dogs »)."""

from datetime import date, datetime

from sqlalchemy import JSON, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base
from enums.coat_color import CoatColor
from enums.dog_role import DogRole
from enums.dog_sex import DogSex
from enums.listing_source import ListingSource
from models.enum_column import str_enum_column
from models.timestamps import TimestampMixin


class Dog(TimestampMixin, Base):
    """
    A dog as a source describes it: the parent of a litter, a reproducer a breeder shows, or a puppy of a litter.

    Only what describes the dog is kept (identity, colour, health, rating, parents), never the contact details
    of its owner (docs/01, « Données personnelles »).

    Attributes:
        id: Primary key.
        breeder_id: Breeding that presents the dog or bred the litter it belongs to, null when unknown.
        source: ``ListingSource`` the dog was read from: the Centrale Canine or a breeder's site on Chiens de France.
        external_id: Identifier on the source: the LOF Select id (``ws.chien.id``) or the ``/chien/<id>`` of a site.
        external_url: Public page of the dog on the source.
        role: ``DogRole`` value.
        litter_group_id: Litter the puppy belongs to, null for a parent or a reproducer.
        name: Name without the affix (« Balti »).
        affix: Affix (« des Joyaux des Ki'millacs »).
        full_name: Name with the affix, as the source writes it.
        sex: ``DogSex`` value.
        birth_date: Birth date.
        lof_number: LOF number.
        identifier: Chip or tattoo.
        color_code: Colour as the source writes it (« F.Or. », « Noire et blanche »).
        color: Canonical colour, ``inconnue`` while the code is not understood.
        rating: Centrale Canine rating, 0 to 6.
        health_codes: Health test codes (« FN-1.1 », « PRCD-1.1 », « LocE-e/e »).
        e_locus: Genotype of the E locus (« e/e », « E/e », « E/E »), read from the health codes.
        has_dna_profile: Whether a DNA profile is recorded.
        sire_external_id: Identifier of the father on the source, when given.
        dam_external_id: Identifier of the mother on the source, when given.
        photos: Photo URLs.
        availability_text: What the source says of the dog (« Disponible pour saillie », « En vente »).
        fetched_at: Last time the page of the dog was read.
    """

    __tablename__ = "dogs"
    __table_args__ = (UniqueConstraint("source", "external_id", name="uq_dog_source_external_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    breeder_id: Mapped[int | None] = mapped_column(ForeignKey("breeders.id", ondelete="SET NULL"), index=True)
    source: Mapped[ListingSource] = mapped_column(str_enum_column(ListingSource), nullable=False)
    external_id: Mapped[str] = mapped_column(String(80), nullable=False)
    external_url: Mapped[str | None] = mapped_column(String(500))
    role: Mapped[DogRole] = mapped_column(str_enum_column(DogRole), nullable=False, index=True)
    litter_group_id: Mapped[int | None] = mapped_column(ForeignKey("litter_groups.id", ondelete="SET NULL"), index=True)
    name: Mapped[str | None] = mapped_column(String(120))
    affix: Mapped[str | None] = mapped_column(String(255))
    full_name: Mapped[str | None] = mapped_column(String(255))
    sex: Mapped[DogSex] = mapped_column(str_enum_column(DogSex), default=DogSex.UNKNOWN, nullable=False)
    birth_date: Mapped[date | None]
    lof_number: Mapped[str | None] = mapped_column(String(40))
    identifier: Mapped[str | None] = mapped_column(String(40))
    color_code: Mapped[str | None] = mapped_column(String(80))
    color: Mapped[CoatColor] = mapped_column(str_enum_column(CoatColor), default=CoatColor.INCONNUE, nullable=False)
    rating: Mapped[int | None]
    health_codes: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    e_locus: Mapped[str | None] = mapped_column(String(10))
    has_dna_profile: Mapped[bool | None]
    sire_external_id: Mapped[str | None] = mapped_column(String(80))
    dam_external_id: Mapped[str | None] = mapped_column(String(80))
    photos: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    availability_text: Mapped[str | None] = mapped_column(String(120))
    fetched_at: Mapped[datetime | None]

    def __repr__(self) -> str:
        return f"<Dog id={self.id} source={self.source} external_id={self.external_id} role={self.role}>"
