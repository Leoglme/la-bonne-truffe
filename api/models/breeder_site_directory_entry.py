"""BreederSiteDirectoryEntry model: a breeder site a regional list of Chiens de France names, and where it is."""

from datetime import datetime

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from core.clock import naive_utc_now
from core.database import Base


class BreederSiteDirectoryEntry(Base):
    """
    One box of a regional list of breeders on Chiens de France, kept to place the breedings the Centrale Canine
    lists without an address (docs/02, « Les élevages qui cachent leur adresse »).

    Attributes:
        id: Primary key.
        site_url: Root of the breeder's site (``https://<nom>.chiens-de-france.com``).
        name: Name of the breeding as the list writes it.
        zip_code: Postal code the list gives, when it gives one.
        town: Town the list gives, when it gives one.
        seen_at: Last time a list showed it.
    """

    __tablename__ = "breeder_site_directory_entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    site_url: Mapped[str] = mapped_column(String(500), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    zip_code: Mapped[str | None] = mapped_column(String(10))
    town: Mapped[str | None] = mapped_column(String(120))
    seen_at: Mapped[datetime] = mapped_column(default=naive_utc_now, nullable=False)

    def __repr__(self) -> str:
        return f"<BreederSiteDirectoryEntry id={self.id} name={self.name!r} zip_code={self.zip_code}>"
