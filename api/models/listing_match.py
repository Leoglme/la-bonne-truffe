"""ListingMatch model: the verdict of a litter group against a search profile."""

from datetime import datetime

from sqlalchemy import JSON, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from core.clock import naive_utc_now
from core.database import Base
from enums.match_tier import MatchTier
from models.enum_column import str_enum_column


class ListingMatch(Base):
    """
    Tier, score and reasons of a litter group for a profile, recomputed at every run.

    Attributes:
        id: Primary key.
        litter_group_id: Litter evaluated.
        profile_id: Profile it was evaluated against.
        tier: ``MatchTier`` value; it decides the notification.
        score: 0 to 100; it orders the list.
        reasons: Readable reasons, each ``{"text": str, "points": int}``.
        flags: Unknown facts that lowered the tier (``color_to_confirm``, ``sex_unknown``…).
        computed_at: Time of the evaluation.
        notified_events: Event kind → ISO date it was notified, so each event is pushed once.
    """

    __tablename__ = "listing_matches"
    __table_args__ = (UniqueConstraint("litter_group_id", "profile_id", name="uq_listing_match_group_profile"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    litter_group_id: Mapped[int] = mapped_column(
        ForeignKey("litter_groups.id", ondelete="CASCADE"), nullable=False, index=True
    )
    profile_id: Mapped[int] = mapped_column(
        ForeignKey("search_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    tier: Mapped[MatchTier] = mapped_column(
        str_enum_column(MatchTier), default=MatchTier.ACCEPTABLE, nullable=False, index=True
    )
    score: Mapped[int] = mapped_column(default=0, nullable=False)
    reasons: Mapped[list[dict[str, str | int]]] = mapped_column(JSON, default=list, nullable=False)
    flags: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    computed_at: Mapped[datetime] = mapped_column(default=naive_utc_now, nullable=False)
    notified_events: Mapped[dict[str, str]] = mapped_column(JSON, default=dict, nullable=False)

    def __repr__(self) -> str:
        return f"<ListingMatch group={self.litter_group_id} profile={self.profile_id} tier={self.tier}>"
