"""Litter schemas: the cards of the home screen and the detail screen."""

from datetime import date, datetime
from typing import Self

from pydantic import BaseModel, Field, model_validator

from enums.coat_color import CoatColor
from enums.color_confidence import ColorConfidence
from enums.dog_sex import DogSex
from enums.follow_up_status import FollowUpStatus
from enums.genetic_screening import GeneticScreening
from enums.listing_kind import ListingKind
from enums.listing_source import ListingSource
from enums.lof_status import LofStatus
from enums.match_flag import MatchFlag
from enums.match_tier import MatchTier
from enums.puppy_ad_state import PuppyAdState

MAX_PUPPIES_PER_SEX = 20


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
    breeder_latitude: float | None = Field(description="Position of the breeding, when a source gives it")
    breeder_longitude: float | None = Field(description="Position of the breeding, when a source gives it")
    kind: ListingKind
    tier: MatchTier | None
    score: int | None
    colors: list[LitterColor]
    lof_status: LofStatus
    male_count: int | None
    female_count: int | None
    has_confirmed_sexes: bool = Field(description="Whether the sexes were confirmed by hand after a call")
    puppies_available: int | None = Field(
        description="Puppies still offered across the active listings, null while no source tells"
    )
    price_cents: int | None = Field(description="Lowest price of the active listings, null while no source gives one")
    highest_price_cents: int | None = Field(
        default=None, description="Highest price of the active listings, the same as the lowest when all ask one price"
    )
    birth_date: date | None
    expected_birth_date: date | None
    available_from: date | None = Field(
        description="Day the puppies may leave: the day the ads announce, else the birth (or expected birth) + 56 days"
    )
    photo_url: str | None
    first_seen_at: datetime
    latest_listing_appeared_at: datetime = Field(
        description="When its newest listing first showed: the litter itself, or a later ad, such as one of a puppy"
    )
    last_seen_at: datetime = Field(description="Last time a source still showed one of its listings")
    is_active: bool
    sources: list[ListingSource]
    follow_up_status: FollowUpStatus | None
    genetic_screening: GeneticScreening | None = Field(
        description="APR and NF screening the ratings of the parents guarantee, none when they guarantee nothing"
    )
    gold_puppy_odds: float | None = Field(
        default=None, description="Share of gold puppies the genotypes of the parents give (1, 0.5, 0.25), when known"
    )


class LitterReason(BaseModel):
    """One line of « Pourquoi ce score »."""

    text: str
    points: int


class LitterParent(BaseModel):
    """Father or mother of a litter, with what its Centrale Canine page adds once read."""

    name: str
    rating: int | None
    color: CoatColor | None = Field(default=None, description="Colour read on its Centrale Canine page")
    color_code: str | None = None
    e_locus: str | None = Field(default=None, description="E locus genotype, when tested (« e/e »)")
    carries_gold_by_parents: bool = Field(
        default=False, description="Untested, but one of its own parents had a coat of the gold family"
    )
    health_codes: list[str] = Field(default_factory=list)
    scc_url: str | None = None
    photo_url: str | None = Field(default=None, description="First photo of the dog on its breeder's site, by chip")


class LitterBreeder(BaseModel):
    """What is known of the breeder; every field may be unknown."""

    id: int | None = Field(default=None, description="The breeder, to open its page in the Éleveurs tab")
    display_name: str | None
    affix: str | None
    city: str | None
    phone_e164: str | None
    siren: str | None
    website: str | None
    is_selected_breeding: bool
    has_affix: bool | None
    is_breed_club_member: bool = Field(
        description="Member of the club of the breed, the Spaniel Club Français for the cocker"
    )


class LitterSourceListing(BaseModel):
    """The litter as one source shows it (« Vu sur »); for a puppy ad, one puppy of the litter."""

    source: ListingSource
    kind: ListingKind
    external_url: str | None = Field(
        description="Page of the listing: on the breeder's own site when it was read there (for a puppy, the page of "
        "its litter pointed at its number), else on the main site of the source"
    )
    litter_number: str | None
    last_seen_at: datetime
    is_active: bool
    male_count: int | None
    female_count: int | None
    colors: list[LitterColor]
    photos: list[str]
    puppy_state: PuppyAdState | None = Field(default=None, description="Where the puppy of a puppy ad stands")
    price_cents: int | None = None


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


class LitterExpectedColor(BaseModel):
    """A colour the parents of a litter imply, and why."""

    color: CoatColor
    confidence: ColorConfidence
    reason: str
    puppy_odds: float | None = Field(default=None, description="Share of the puppies of that colour, when known")


class LitterPuppy(BaseModel):
    """A registered puppy of a litter, read at the Centrale Canine."""

    id: int
    name: str | None
    sex: DogSex
    color: CoatColor
    color_code: str | None
    identifier: str | None
    lof_number: str | None
    external_url: str | None


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
    puppies: list[LitterPuppy] = Field(default_factory=list, description="The registered puppies, read one by one")
    expected_colors: list[LitterExpectedColor] = Field(
        default_factory=list, description="The colours the parents imply, and why"
    )
    photos_added_at: datetime | None = Field(
        default=None, description="Last time new photos reached one of its listings, naive UTC"
    )


class ColorConfirmation(BaseModel):
    """Colours confirmed by hand after a call; an empty list removes the confirmation."""

    colors: list[CoatColor] = Field(..., max_length=4)


class SexConfirmation(BaseModel):
    """Males and females heard from the breeder; both left empty go back to what the sources say."""

    male_count: int | None = Field(default=None, ge=0, le=MAX_PUPPIES_PER_SEX)
    female_count: int | None = Field(default=None, ge=0, le=MAX_PUPPIES_PER_SEX)

    @model_validator(mode="after")
    def check_both_or_none(self) -> Self:
        """
        Refuse one sex without the other.

        Returns:
            The confirmation.

        Raises:
            ValueError: When only one count is given.
        """
        if (self.male_count is None) != (self.female_count is None):
            raise ValueError("Donne les mâles et les femelles ensemble, ou aucun des deux")
        return self


class FollowUpUpdate(BaseModel):
    """Status and reminder of a follow-up."""

    status: FollowUpStatus
    next_reminder_at: datetime | None = None
    last_contact_at: datetime | None = None


class FollowUpNoteCreate(BaseModel):
    """A note to add to a follow-up."""

    text: str = Field(..., min_length=1, max_length=4000)


class LitterVisit(BaseModel):
    """The previous look at the home list: the litters first seen after it are the new ones."""

    previous_visit_at: datetime | None


class FollowUpCard(BaseModel):
    """A followed litter as the follow-up screen lists it."""

    litter: LitterCard
    status: FollowUpStatus
    next_reminder_at: datetime | None
    last_contact_at: datetime | None
    last_note: FollowUpNoteResponse | None
