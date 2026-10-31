"""First and second steps of docs/04: the hard filters, then the tier."""

from datetime import date

from enums.color_preference_level import ColorPreferenceLevel
from enums.listing_kind import ListingKind
from enums.lof_preference import LofPreference
from enums.lof_status import LofStatus
from enums.match_flag import MatchFlag
from enums.match_tier import MatchTier
from enums.sex_preference import SexPreference
from services.matching.criteria import LitterSnapshot, ProfileCriteria


class TierRules:
    """Decides the tier of a litter for a profile. An unknown fact never filters: it raises a flag."""

    @classmethod
    def tier_of(cls, snapshot: LitterSnapshot, criteria: ProfileCriteria, today: date) -> MatchTier:
        """
        Apply the hard filters, then pick the tier.

        Args:
            snapshot: The litter.
            criteria: The profile.
            today: Day of the evaluation, in French time.

        Returns:
            ``excluded``, ``ignored``, ``acceptable`` or ``preferred``.
        """
        if cls.is_excluded(snapshot, criteria, today):
            return MatchTier.EXCLUDED
        levels = [criteria.level_of(reading.color) for reading in snapshot.colors]
        if (
            levels
            and not snapshot.has_certain_colors
            and all(level == ColorPreferenceLevel.IGNORED for level in levels)
        ):
            return MatchTier.IGNORED
        has_preferred_certain_color = snapshot.has_certain_colors and ColorPreferenceLevel.PREFERRED in levels
        if (
            has_preferred_certain_color
            and cls._is_lof_as_wanted(snapshot, criteria)
            and cls._has_wanted_sex(snapshot, criteria)
        ):
            return MatchTier.PREFERRED
        return MatchTier.ACCEPTABLE

    @classmethod
    def is_excluded(cls, snapshot: LitterSnapshot, criteria: ProfileCriteria, today: date) -> bool:
        """
        The hard filters of docs/04, first step. A litter whose every puppy is reserved, sold or adopted is
        excluded too, as is one whose puppies are past the age they leave at: nothing left to call about.

        Args:
            snapshot: The litter.
            criteria: The profile.
            today: Day of the evaluation, in French time.

        Returns:
            Whether the litter is excluded.
        """
        if snapshot.breed_slug not in criteria.breed_slugs:
            return True
        if snapshot.department_code is not None and snapshot.department_code not in criteria.department_codes:
            return True
        if snapshot.kind == ListingKind.LITTER_EXPECTED and not criteria.include_expected_litters:
            return True
        if snapshot.has_certain_colors and all(
            criteria.level_of(reading.color) == ColorPreferenceLevel.IGNORED for reading in snapshot.colors
        ):
            return True
        if criteria.lof_preference == LofPreference.REQUIRED and snapshot.lof_status == LofStatus.NON_LOF:
            return True
        if cls._is_wanted_sex_known_absent(snapshot, criteria):
            return True
        if snapshot.puppies_available == 0:
            return True
        if cls._are_puppies_probably_gone(snapshot, criteria, today):
            return True
        return (
            snapshot.price_cents is not None
            and criteria.price_max_cents is not None
            and snapshot.price_cents > criteria.price_max_cents
        )

    @staticmethod
    def _are_puppies_probably_gone(snapshot: LitterSnapshot, criteria: ProfileCriteria, today: date) -> bool:
        """
        Whether the puppies are older than the profile's limit while no active ad says some remain: a puppy
        leaves the breeding at about two months, so such a litter is almost surely gone. A declared mating
        whose expected birth is that old counts too: born and gone, or never declared.

        Args:
            snapshot: The litter.
            criteria: The profile.
            today: Day of the evaluation, in French time.

        Returns:
            True when the litter should leave the home screen.
        """
        birth_day = snapshot.birth_date or snapshot.expected_birth_date
        if criteria.max_puppy_age_days is None or birth_day is None:
            return False
        if snapshot.puppies_available is not None and snapshot.puppies_available > 0:
            return False
        return (today - birth_day).days > criteria.max_puppy_age_days

    @staticmethod
    def flags_of(snapshot: LitterSnapshot, criteria: ProfileCriteria) -> list[MatchFlag]:
        """
        The unknown facts worth confirming with the breeder.

        Args:
            snapshot: The litter.
            criteria: The profile.

        Returns:
            The flags, in a stable order.
        """
        flags: list[MatchFlag] = []
        if not snapshot.has_certain_colors:
            flags.append(MatchFlag.COLOR_TO_CONFIRM)
        if snapshot.male_count is None or snapshot.female_count is None:
            flags.append(MatchFlag.SEX_UNKNOWN)
        if snapshot.lof_status == LofStatus.UNKNOWN:
            flags.append(MatchFlag.LOF_UNKNOWN)
        if criteria.price_max_cents is not None and snapshot.price_cents is None:
            flags.append(MatchFlag.PRICE_UNKNOWN)
        if snapshot.department_code is None:
            flags.append(MatchFlag.DEPARTMENT_UNKNOWN)
        return flags

    @staticmethod
    def _is_lof_as_wanted(snapshot: LitterSnapshot, criteria: ProfileCriteria) -> bool:
        """
        Whether the LOF status matches the preference (« peu importe » always does).

        Args:
            snapshot: The litter.
            criteria: The profile.

        Returns:
            True when the LOF side allows the preferred tier.
        """
        return criteria.lof_preference == LofPreference.ANY or snapshot.lof_status == LofStatus.LOF

    @staticmethod
    def _wanted_sex_count(snapshot: LitterSnapshot, criteria: ProfileCriteria) -> int | None:
        """
        Number of puppies of the wanted sex, or of all puppies for « peu importe ».

        Args:
            snapshot: The litter.
            criteria: The profile.

        Returns:
            The count, or None while unknown.
        """
        if criteria.sex_preference == SexPreference.MALE:
            return snapshot.male_count
        if criteria.sex_preference == SexPreference.FEMALE:
            return snapshot.female_count
        if snapshot.male_count is None or snapshot.female_count is None:
            return None
        return snapshot.male_count + snapshot.female_count

    @classmethod
    def _has_wanted_sex(cls, snapshot: LitterSnapshot, criteria: ProfileCriteria) -> bool:
        """
        Whether the wanted sex is present, or the preference is « peu importe ».

        Args:
            snapshot: The litter.
            criteria: The profile.

        Returns:
            True when the sex side allows the preferred tier.
        """
        if criteria.sex_preference == SexPreference.ANY:
            return True
        count = cls._wanted_sex_count(snapshot, criteria)
        return count is not None and count > 0

    @classmethod
    def _is_wanted_sex_known_absent(cls, snapshot: LitterSnapshot, criteria: ProfileCriteria) -> bool:
        """
        Whether a wanted sex is known to be absent (count at 0 after the birth).

        Args:
            snapshot: The litter.
            criteria: The profile.

        Returns:
            True when the litter has none of the wanted sex.
        """
        if criteria.sex_preference == SexPreference.ANY:
            return False
        return cls._wanted_sex_count(snapshot, criteria) == 0
