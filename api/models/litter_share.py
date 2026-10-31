"""LitterShare model: a private link to a litter, opened without an account."""

from datetime import datetime

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from core.clock import naive_utc_now
from core.database import Base


class LitterShare(Base):
    """
    A litter shared by a user: anyone holding the link reads its page until the link expires.

    Attributes:
        id: Primary key.
        token: Secret part of the link, unguessable.
        user_id: Who shared it; the page shows their first name.
        litter_group_id: The litter; the link dies with it.
        message: Word left for the people the link is sent to, null for none.
        created_at: Sharing time.
        expires_at: After it, the page answers that the link expired.
    """

    __tablename__ = "litter_shares"

    id: Mapped[int] = mapped_column(primary_key=True)
    token: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    litter_group_id: Mapped[int] = mapped_column(
        ForeignKey("litter_groups.id", ondelete="CASCADE"), nullable=False, index=True
    )
    message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(default=naive_utc_now, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(nullable=False)

    def __repr__(self) -> str:
        return f"<LitterShare id={self.id} litter_group_id={self.litter_group_id}>"
