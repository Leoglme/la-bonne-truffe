"""The two inputs of the matching, as plain typed values: what is wanted, and what a litter is."""

from dataclasses import dataclass
from datetime import date

from enums.coat_color import CoatColor
from enums.color_confidence import ColorConfidence
from enums.color_preference_level import ColorPreferenceLevel
from enums.listing_kind import ListingKind
from enums.lof_preference import LofPreference
from enums.lof_status import LofStatus
from enums.sex_preference import SexPreference
from models.search_profile import SearchProfile
from services.collectors.raw_listing import ColorReading


@dataclass(frozen=True)
class ProfileCriteria:
    """The criteria of a search profile, typed."""

    profile_id: int
    breed_slugs: frozenset[str]
    department_codes: tuple[str, ...]
    include_expected_litters: bool
    sex_preference: SexPreference
    lof_preference: LofPreference
    color_levels: dict[CoatColor, ColorPreferenceLevel]
    price_max_cents: int | None

    @classmethod
    def from_profile(cls, profile: SearchProfile) -> "ProfileCriteria":
        """
        Read the criteria of a stored profile. A colour left out of the profile is ``ignored``.

        Args:
            profile: Stored profile.

        Returns:
            The typed criteria.
        """
        return cls(
            profile_id=profile.id,
            breed_slugs=frozenset(profile.breed_ids),
            department_codes=tuple(profile.department_codes),
            include_expected_litters=profile.include_expected_litters,
            sex_preference=profile.sex_preference,
            lof_preference=profile.lof_preference,
            color_levels={
                CoatColor(color): ColorPreferenceLevel(level) for color, level in profile.color_preferences.items()
            },
            price_max_cents=profile.price_max_cents,
        )

    def level_of(self, color: CoatColor) -> ColorPreferenceLevel:
        """
        Level the profile gives to a colour.

        Args:
            color: Canonical colour.

        Returns:
            Its level, ``ignored`` when the profile does not list it.
        """
        return self.color_levels.get(color, ColorPreferenceLevel.IGNORED)


@dataclass(frozen=True)
class LitterSnapshot:
    """
    What is known of a litter group, merged across its active listings. Unknown stays None.

    ``colors`` holds the confirmed colours when Léo confirmed one, otherwise the certain ones when a
    source is sure, otherwise the ambiguous bundle; empty means the colour is unknown.

    ``appeared_on`` is the day the litter went online on a source (the earliest one), or the day a
    collection first saw it when no source gives that date.
    """

    group_id: int
    breed_slug: str
    kind: ListingKind
    department_code: str | None
    department_name: str | None
    colors: tuple[ColorReading, ...]
    lof_status: LofStatus
    male_count: int | None
    female_count: int | None
    price_cents: int | None
    appeared_on: date
    birth_date: date | None
    expected_birth_date: date | None
    available_from: date | None
    breeder_selection_group: int | None
    sire_rating: int | None
    dam_rating: int | None

    @property
    def has_certain_colors(self) -> bool:
        """Whether the colours are certain or confirmed, not an ambiguous bundle."""
        return bool(self.colors) and all(reading.confidence != ColorConfidence.AMBIGUOUS for reading in self.colors)

    @property
    def is_born(self) -> bool:
        """Whether the litter is born (its sexes are then known at the Centrale Canine)."""
        return self.kind == ListingKind.LITTER_BORN
