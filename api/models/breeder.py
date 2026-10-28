"""Breeder model: the anchor of the deduplication between sources."""

from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base
from models.timestamps import TimestampMixin


class Breeder(TimestampMixin, Base):
    """
    A breeder (or a private seller), matched across sources by SIREN, then phone, then affix and department.

    Attributes:
        id: Primary key.
        display_name: Name shown in the dashboard (affix, or the name the source gives).
        affix: Kennel affix, null for a breeder without one.
        affix_normalized: Affix lowercased, accents and articles removed, used to match.
        siren: French company number, unique when known.
        phone_e164: Phone in E.164 format.
        email: Contact email.
        zip_code: Postal code.
        city: Town.
        department_code: Department code.
        latitude: Latitude of the breeding, when a source gives it.
        longitude: Longitude of the breeding, when a source gives it.
        website: Breeder's website.
        scc_breeder_id: Breeder identifier at the Centrale Canine (``n_breeder_id``).
        scc_selection_group: Centrale Canine group: 1 selected, 2 with affix, 3 without affix.
        notes: Free notes.
    """

    __tablename__ = "breeders"

    id: Mapped[int] = mapped_column(primary_key=True)
    display_name: Mapped[str | None] = mapped_column(String(255))
    affix: Mapped[str | None] = mapped_column(String(255))
    affix_normalized: Mapped[str | None] = mapped_column(String(255), index=True)
    siren: Mapped[str | None] = mapped_column(String(9), unique=True)
    phone_e164: Mapped[str | None] = mapped_column(String(20), index=True)
    email: Mapped[str | None] = mapped_column(String(255))
    zip_code: Mapped[str | None] = mapped_column(String(10))
    city: Mapped[str | None] = mapped_column(String(120))
    department_code: Mapped[str | None] = mapped_column(ForeignKey("departments.code"), index=True)
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)
    website: Mapped[str | None] = mapped_column(String(500))
    scc_breeder_id: Mapped[str | None] = mapped_column(String(40), unique=True)
    scc_selection_group: Mapped[int | None]
    notes: Mapped[str | None] = mapped_column(Text)

    def __repr__(self) -> str:
        return f"<Breeder id={self.id} display_name={self.display_name}>"
