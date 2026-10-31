"""Search profile schemas: the criteria screen reads and saves them."""

from pydantic import BaseModel, ConfigDict, Field

from enums.coat_color import CoatColor
from enums.color_preference_level import ColorPreferenceLevel
from enums.lof_preference import LofPreference
from enums.sex_preference import SexPreference


class SearchProfileFields(BaseModel):
    """The editable criteria, shared by the read and the update payloads."""

    name: str = Field(..., min_length=1, max_length=120)
    is_active: bool
    breed_ids: list[str] = Field(..., min_length=1)
    department_codes: list[str] = Field(..., min_length=1, description="Ordered from the closest to the farthest")
    include_expected_litters: bool
    sex_preference: SexPreference
    lof_preference: LofPreference
    color_preferences: dict[CoatColor, ColorPreferenceLevel]
    price_max_cents: int | None = Field(default=None, ge=0)
    notify_preferred_immediately: bool
    notify_acceptable_in_digest: bool
    digest_hour: int = Field(..., ge=0, le=23)
    notify_birth_of_followed: bool
    max_puppy_age_days: int | None = Field(
        default=None,
        ge=7,
        le=365,
        description="Hide a litter born more than this many days ago unless an ad says puppies remain; null keeps all",
    )


class SearchProfileUpdate(SearchProfileFields):
    """Criteria saved from the criteria screen."""


class SearchProfileResponse(SearchProfileFields):
    """A stored profile."""

    model_config = ConfigDict(from_attributes=True)

    id: int
