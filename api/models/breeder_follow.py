"""BreederFollow, BreederFollowNote and BreederFollowEvent models: the breeders the user follows (docs/03)."""

from datetime import datetime

from sqlalchemy import ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from core.clock import naive_utc_now
from core.database import Base
from enums.breeder_event_kind import BreederEventKind
from enums.breeder_follow_status import BreederFollowStatus
from models.enum_column import str_enum_column
from models.timestamps import TimestampMixin


class BreederFollow(TimestampMixin, Base):
    """
    A breeder the user follows: which of its events to be told of, and where the exchange stands.

    Attributes:
        id: Primary key.
        user_id: Owner.
        breeder_id: Followed breeder.
        status: ``BreederFollowStatus`` value.
        notify_new_mating: Push when the breeder declares a mating.
        notify_birth: Push when a litter of the breeder is born.
        notify_new_photos: Evening digest line when photos or an ad arrive on a litter of the breeder.
        notify_ignored_colors: Whether a litter whose colours the profile ignores notifies too.
        next_reminder_at: When to call back, null for no reminder.
        reminder_sent_at: When the reminder was pushed, null until then.
        last_contact_at: Last call or message.
    """

    __tablename__ = "breeder_follows"
    __table_args__ = (UniqueConstraint("user_id", "breeder_id", name="uq_breeder_follow_user_breeder"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    breeder_id: Mapped[int] = mapped_column(ForeignKey("breeders.id", ondelete="CASCADE"), nullable=False, index=True)
    status: Mapped[BreederFollowStatus] = mapped_column(
        str_enum_column(BreederFollowStatus), default=BreederFollowStatus.TO_CONTACT, nullable=False
    )
    notify_new_mating: Mapped[bool] = mapped_column(default=True, nullable=False)
    notify_birth: Mapped[bool] = mapped_column(default=True, nullable=False)
    notify_new_photos: Mapped[bool] = mapped_column(default=True, nullable=False)
    notify_ignored_colors: Mapped[bool] = mapped_column(default=False, nullable=False)
    next_reminder_at: Mapped[datetime | None]
    reminder_sent_at: Mapped[datetime | None]
    last_contact_at: Mapped[datetime | None]

    def __repr__(self) -> str:
        return f"<BreederFollow id={self.id} breeder_id={self.breeder_id} status={self.status}>"


class BreederFollowNote(Base):
    """
    A dated note on a followed breeder (« Appelée le 29 oct. : réservations à la naissance »).

    Attributes:
        id: Primary key.
        follow_id: Follow the note belongs to.
        created_at: Time the note was written.
        text: The note.
    """

    __tablename__ = "breeder_follow_notes"

    id: Mapped[int] = mapped_column(primary_key=True)
    follow_id: Mapped[int] = mapped_column(
        ForeignKey("breeder_follows.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(default=naive_utc_now, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)

    def __repr__(self) -> str:
        return f"<BreederFollowNote id={self.id} follow_id={self.follow_id}>"


class BreederFollowEvent(Base):
    """
    An event of a followed breeder already handled, so that it is notified once (docs/04).

    Attributes:
        id: Primary key.
        follow_id: The follow.
        litter_group_id: The litter the event is about, null for an event without litter.
        kind: ``BreederEventKind`` value.
        created_at: When the event was raised.
        sent_at: When it was pushed or put in a digest; null while it waits for the evening digest.
    """

    __tablename__ = "breeder_follow_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    follow_id: Mapped[int] = mapped_column(
        ForeignKey("breeder_follows.id", ondelete="CASCADE"), nullable=False, index=True
    )
    litter_group_id: Mapped[int | None] = mapped_column(ForeignKey("litter_groups.id", ondelete="SET NULL"))
    kind: Mapped[BreederEventKind] = mapped_column(str_enum_column(BreederEventKind), nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=naive_utc_now, nullable=False)
    sent_at: Mapped[datetime | None] = mapped_column(index=True)

    def __repr__(self) -> str:
        return f"<BreederFollowEvent id={self.id} follow_id={self.follow_id} kind={self.kind}>"
