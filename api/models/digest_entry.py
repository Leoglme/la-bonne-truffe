"""DigestEntry model: a litter waiting for the evening digest."""

from datetime import datetime

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from core.clock import naive_utc_now
from core.database import Base
from enums.match_event_kind import MatchEventKind
from models.enum_column import str_enum_column


class DigestEntry(Base):
    """
    An event kept for the evening digest instead of an immediate push (« nouvelle portée acceptable »).

    Attributes:
        id: Primary key.
        user_id: Recipient.
        litter_group_id: Litter the entry is about.
        event_kind: ``MatchEventKind`` of the entry.
        created_at: Time the event was detected.
        sent_at: Time the digest carrying it was sent, null while pending.
    """

    __tablename__ = "digest_entries"
    __table_args__ = (UniqueConstraint("user_id", "litter_group_id", "event_kind", name="uq_digest_entry_event"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    litter_group_id: Mapped[int] = mapped_column(
        ForeignKey("litter_groups.id", ondelete="CASCADE"), nullable=False, index=True
    )
    event_kind: Mapped[MatchEventKind] = mapped_column(str_enum_column(MatchEventKind), nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=naive_utc_now, nullable=False)
    sent_at: Mapped[datetime | None] = mapped_column(index=True)

    def __repr__(self) -> str:
        return f"<DigestEntry group={self.litter_group_id} kind={self.event_kind} sent={self.sent_at is not None}>"
