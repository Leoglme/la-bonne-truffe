"""Notification model: history of the notifications sent, for the bell and the idempotence."""

from datetime import datetime
from typing import TypedDict

from sqlalchemy import JSON, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from core.clock import naive_utc_now
from core.database import Base
from enums.notification_kind import NotificationKind
from models.enum_column import str_enum_column


class DigestLitterEntry(TypedDict):
    """A litter of an evening digest, with the ``MatchEventKind`` value that put it there."""

    litter_group_id: int
    event: str


class Notification(Base):
    """
    A notification sent to the user.

    Attributes:
        id: Primary key.
        user_id: Recipient.
        kind: ``NotificationKind`` value.
        title: What and who, in a few words (« Portée née · De Kerlann »).
        body: One sentence: colour, place, sexes.
        url: In-app path opened by a tap.
        litter_group_id: Litter the notification is about, if any.
        digest_litters: Litters of an evening digest, each ``{"litter_group_id", "event"}``; empty otherwise.
        sent_at: Sending time.
        read_at: Time the bell marked it read, null while unread.
        delivered_count: Subscriptions that accepted the push.
        failed_count: Subscriptions that refused it.
    """

    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    kind: Mapped[NotificationKind] = mapped_column(str_enum_column(NotificationKind), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    litter_group_id: Mapped[int | None] = mapped_column(ForeignKey("litter_groups.id", ondelete="SET NULL"))
    digest_litters: Mapped[list[DigestLitterEntry]] = mapped_column(JSON, default=list, nullable=False)
    sent_at: Mapped[datetime] = mapped_column(default=naive_utc_now, nullable=False, index=True)
    read_at: Mapped[datetime | None]
    delivered_count: Mapped[int] = mapped_column(default=0, nullable=False)
    failed_count: Mapped[int] = mapped_column(default=0, nullable=False)

    def __repr__(self) -> str:
        return f"<Notification id={self.id} kind={self.kind}>"
