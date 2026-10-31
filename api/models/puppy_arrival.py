"""PuppyArrival model: the puppy found, the day it comes home, and the preparations ticked."""

from datetime import date, datetime

from sqlalchemy import JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from core.clock import naive_utc_now
from core.database import Base


class PuppyArrival(Base):
    """
    The puppy a user found. While it exists, the search is paused: no litter alert goes out.

    Attributes:
        id: Primary key.
        user_id: Owner, one arrival per user.
        litter_group_id: Litter of the puppy, null once the litter left the database.
        arrival_on: Day the puppy comes home.
        done_items: Keys of the preparations ticked, as the web app names them.
        created_at: When the search was paused.
    """

    __tablename__ = "puppy_arrivals"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    litter_group_id: Mapped[int | None] = mapped_column(ForeignKey("litter_groups.id", ondelete="SET NULL"), index=True)
    arrival_on: Mapped[date] = mapped_column(nullable=False)
    done_items: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=naive_utc_now, nullable=False)

    def __repr__(self) -> str:
        return f"<PuppyArrival id={self.id} arrival_on={self.arrival_on}>"
