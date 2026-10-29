"""FollowUp and FollowUpNote models: the personal tracking of the exchanges with breeders."""

from datetime import datetime

from sqlalchemy import ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from core.clock import naive_utc_now
from core.database import Base
from enums.follow_up_status import FollowUpStatus
from models.enum_column import str_enum_column
from models.timestamps import TimestampMixin


class FollowUp(TimestampMixin, Base):
    """
    Where the user stands with the breeder of a litter.

    Attributes:
        id: Primary key.
        user_id: Owner.
        litter_group_id: Followed litter.
        status: ``FollowUpStatus`` value.
        next_reminder_at: When to call back, null for no reminder.
        reminder_sent_at: When the reminder was pushed, null until then.
        last_contact_at: Last call or message.
    """

    __tablename__ = "follow_ups"
    __table_args__ = (UniqueConstraint("user_id", "litter_group_id", name="uq_follow_up_user_group"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    litter_group_id: Mapped[int] = mapped_column(
        ForeignKey("litter_groups.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[FollowUpStatus] = mapped_column(
        str_enum_column(FollowUpStatus), default=FollowUpStatus.NEW, nullable=False
    )
    next_reminder_at: Mapped[datetime | None]
    reminder_sent_at: Mapped[datetime | None]
    last_contact_at: Mapped[datetime | None]

    def __repr__(self) -> str:
        return f"<FollowUp id={self.id} status={self.status}>"


class FollowUpNote(Base):
    """
    A dated note on a follow-up (« Appel du 24 oct. Liste d'attente ouverte… »).

    Attributes:
        id: Primary key.
        follow_up_id: Follow-up the note belongs to.
        created_at: Time the note was written.
        text: The note.
    """

    __tablename__ = "follow_up_notes"

    id: Mapped[int] = mapped_column(primary_key=True)
    follow_up_id: Mapped[int] = mapped_column(
        ForeignKey("follow_ups.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(default=naive_utc_now, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)

    def __repr__(self) -> str:
        return f"<FollowUpNote id={self.id} follow_up_id={self.follow_up_id}>"
