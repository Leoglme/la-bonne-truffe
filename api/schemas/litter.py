"""Litter schemas: the cards of the home screen and the detail screen."""

from datetime import date, datetime

from pydantic import BaseModel, Field

from enums.coat_color import CoatColor
from enums.color_confidence import ColorConfidence
from enums.follow_up_status import FollowUpStatus
from enums.listing_kind import ListingKind
from enums.listing_source import ListingSource
from enums.lof_status import LofStatus
from enums.match_flag import MatchFlag
from enums.match_tier import MatchTier


class LitterColor(BaseModel):
    """One colour of a litter and how sure it is."""

    color: CoatColor
    confidence: ColorConfidence


class LitterCard(BaseModel):
    """A litter as the home screen lists it."""

    id: int
    name: str
    place: str | None = Field(description="Town when known, else department name")
    town: str | None
    department_code: str | None
    department_name: str | None
    kind: ListingKind
    tier: MatchTier | None
    score: int | None
    colors: list[LitterColor]
    lof_status: LofStatus
    male_count: int | None
    female_count: int | None
    birth_date: date | None
    expected_birth_date: date | None
    available_from: date | None
    photo_url: str | None
    first_seen_at: datetime
    is_active: bool
    sources: list[ListingSource]
    follow_up_status: FollowUpStatus | None


class LitterReason(BaseModel):
    """One line of « Pourquoi ce score »."""

    text: str
    points: int


class LitterParent(BaseModel):
    """Father or mother of a litter."""

    name: str
    rating: int | None


class LitterBreeder(BaseModel):
    """What is known of the breeder; every field may be unknown."""

    display_name: str | None
    affix: str | None
    city: str | None
    phone_e164: str | None
    siren: str | None
    website: str | None
    is_selected_breeding: bool
    has_affix: bool | None


class LitterSourceListing(BaseModel):
    """The litter as one source shows it (« Vu sur »); for a puppy ad, one puppy of the litter."""

    source: ListingSource
    kind: ListingKind
    external_url: str | None
    litter_number: str | None
    last_seen_at: datetime
    is_active: bool
    male_count: int | None
    female_count: int | None
    colors: list[LitterColor]
    photos: list[str]


class FollowUpNoteResponse(BaseModel):
    """A dated note of a follow-up."""

    id: int
    created_at: datetime
    text: str


class LitterFollowUp(BaseModel):
    """Where the user stands with the breeder."""

    status: FollowUpStatus
    next_reminder_at: datetime | None
    last_contact_at: datetime | None
    notes: list[FollowUpNoteResponse]


class LitterDetail(LitterCard):
    """A litter as the detail screen shows it."""

    reasons: list[LitterReason]
    flags: list[MatchFlag]
    litter_number: str | None
    mating_date: date | None
    sire: LitterParent | None
    dam: LitterParent | None
    breeder: LitterBreeder | None
    photos: list[str]
    listings: list[LitterSourceListing]
    follow_up: LitterFollowUp | None


class ColorConfirmation(BaseModel):
    """Colours confirmed by hand after a call; an empty list removes the confirmation."""

    colors: list[CoatColor] = Field(..., max_length=4)


class FollowUpUpdate(BaseModel):
    """Status and reminder of a follow-up."""

    status: FollowUpStatus
    next_reminder_at: datetime | None = None
    last_contact_at: datetime | None = None


class FollowUpNoteCreate(BaseModel):
    """A note to add to a follow-up."""

    text: str = Field(..., min_length=1, max_length=4000)


class FollowUpCard(BaseModel):
    """A followed litter as the follow-up screen lists it."""

    litter: LitterCard
    status: FollowUpStatus
    next_reminder_at: datetime | None
    last_contact_at: datetime | None
    last_note: FollowUpNoteResponse | None
