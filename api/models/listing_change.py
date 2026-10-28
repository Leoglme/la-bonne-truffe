"""ListingChange model: history of the fields that move on a listing."""

from datetime import datetime

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from core.clock import naive_utc_now
from core.database import Base


class ListingChange(Base):
    """
    One field change seen on a listing between two runs (« les sexes sont apparus », « le prix a changé »).

    Attributes:
        id: Primary key.
        listing_id: Listing that changed.
        field: Name of the changed ``Listing`` column.
        old_value: Previous value, serialized as text.
        new_value: New value, serialized as text.
        changed_at: Run time the change was seen.
    """

    __tablename__ = "listing_changes"

    id: Mapped[int] = mapped_column(primary_key=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id", ondelete="CASCADE"), nullable=False, index=True)
    field: Mapped[str] = mapped_column(String(60), nullable=False)
    old_value: Mapped[str | None] = mapped_column(Text)
    new_value: Mapped[str | None] = mapped_column(Text)
    changed_at: Mapped[datetime] = mapped_column(default=naive_utc_now, nullable=False, index=True)

    def __repr__(self) -> str:
        return f"<ListingChange listing_id={self.listing_id} field={self.field}>"
