"""MatchingService: the pure evaluation of a litter against a profile (docs/04)."""

from dataclasses import dataclass
from datetime import date

from enums.match_flag import MatchFlag
from enums.match_tier import MatchTier
from services.matching.criteria import LitterSnapshot, ProfileCriteria
from services.matching.scoring import ScoreCalculator, ScoreReason
from services.matching.tiers import TierRules


@dataclass(frozen=True)
class MatchVerdict:
    """Tier, score, reasons and flags of a litter for a profile."""

    tier: MatchTier
    score: int
    reasons: tuple[ScoreReason, ...]
    flags: tuple[MatchFlag, ...]


class MatchingService:
    """Evaluates a litter against a profile. Pure: no database, no clock, no side effect."""

    @staticmethod
    def evaluate(snapshot: LitterSnapshot, criteria: ProfileCriteria, today: date) -> MatchVerdict:
        """
        Run the three steps of docs/04: hard filters, tier, score. The score never changes the tier.

        Args:
            snapshot: The litter.
            criteria: The profile.
            today: Day of the evaluation, in French time.

        Returns:
            The verdict.
        """
        reasons = ScoreCalculator.reasons_for(snapshot, criteria, today)
        return MatchVerdict(
            tier=TierRules.tier_of(snapshot, criteria),
            score=ScoreCalculator.score_of(reasons),
            reasons=tuple(reasons),
            flags=tuple(TierRules.flags_of(snapshot, criteria)),
        )
