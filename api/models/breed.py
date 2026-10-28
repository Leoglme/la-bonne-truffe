"""Breed model: the catalogue of breeds with their identifier on each source."""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base
from models.timestamps import TimestampMixin


class Breed(TimestampMixin, Base):
    """
    A dog breed and how each source names it.

    Attributes:
        id: Primary key.
        name_fr: French name (« Cocker spaniel anglais »).
        slug: Our own slug, used by the search profiles.
        scc_slug: Slug in the Centrale Canine URLs (``cocker-spaniel-anglais``).
        scc_breed_id: Breed identifier at the Centrale Canine.
        chiens_de_france_id: Breed identifier on Chiens de France, unknown until that collector exists.
        chiots_de_france_id: Breed identifier on Chiots de France, unknown until that collector exists.
        is_active: Whether the collectors read this breed.
    """

    __tablename__ = "breeds"

    id: Mapped[int] = mapped_column(primary_key=True)
    name_fr: Mapped[str] = mapped_column(String(120), nullable=False)
    slug: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    scc_slug: Mapped[str | None] = mapped_column(String(120))
    scc_breed_id: Mapped[int | None]
    chiens_de_france_id: Mapped[str | None] = mapped_column(String(120))
    chiots_de_france_id: Mapped[str | None] = mapped_column(String(120))
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    def __repr__(self) -> str:
        return f"<Breed id={self.id} slug={self.slug}>"
