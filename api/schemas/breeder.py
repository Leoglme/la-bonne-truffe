"""Breeder schemas: the cards of the Éleveurs tab, the search, the detail, the follow and the manual creation."""

from datetime import date, datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from enums.breeder_follow_status import BreederFollowStatus
from enums.coat_color import CoatColor
from enums.dog_role import DogRole
from enums.dog_sex import DogSex
from enums.listing_source import ListingSource
from schemas.litter import LitterCard


class BreederFilter(StrEnum):
    """Which breeders the list shows."""

    ALL = "all"
    FOLLOWED = "followed"
    GOLD = "gold"
    CLUB = "club"
    ACTIVE_LITTER = "active_litter"


class BreederSort(StrEnum):
    """Order of the Éleveurs list."""

    PROMISING = "promising"
    NAME = "name"


class BreederLink(BaseModel):
    """A link Léo added by hand (Facebook, Instagram, a site)."""

    label: str = Field(..., min_length=1, max_length=80)
    url: str = Field(..., min_length=1, max_length=500)


class BreederFollowNoteResponse(BaseModel):
    """A dated note of a followed breeder."""

    id: int
    created_at: datetime
    text: str


class BreederFollowResponse(BaseModel):
    """What the user asked of a followed breeder, and where the exchange stands."""

    status: BreederFollowStatus
    notify_new_mating: bool
    notify_birth: bool
    notify_new_photos: bool
    notify_ignored_colors: bool
    next_reminder_at: datetime | None
    last_contact_at: datetime | None
    notes: list[BreederFollowNoteResponse]


class BreederFollowUpdate(BaseModel):
    """Follow a breeder, or change the alerts and the status."""

    status: BreederFollowStatus = BreederFollowStatus.TO_CONTACT
    notify_new_mating: bool = True
    notify_birth: bool = True
    notify_new_photos: bool = True
    notify_ignored_colors: bool = False
    next_reminder_at: datetime | None = None
    last_contact_at: datetime | None = None


class BreederFollowNoteCreate(BaseModel):
    """A note to add to a followed breeder."""

    text: str = Field(..., min_length=1, max_length=4000)


class BreederColorShare(BaseModel):
    """How many known litters of a breeder were of one colour."""

    color: CoatColor
    litters_count: int


class BreederCard(BaseModel):
    """A breeder as the Éleveurs list shows it."""

    id: int
    name: str = Field(description="The affix, else the name of the breeding, as the cards name it")
    person_name: str | None = Field(description="Name of the person or the company, when it differs from the affix")
    affix: str | None
    city: str | None
    zip_code: str | None
    department_code: str | None
    department_name: str | None
    latitude: float | None
    longitude: float | None
    logo_url: str | None
    photo_url: str | None = Field(description="The first photo known of the breeding: its sites, else a litter")
    is_selected_breeding: bool
    is_breed_club_member: bool
    has_siren: bool
    has_chiens_de_france_site: bool
    is_manual: bool
    sources: list[ListingSource] = Field(description="Where the breeder is listed")
    gold_litters_count: int = Field(description="Litters known gold, certain or confirmed")
    litters_count: int = Field(description="Litters known, every colour")
    last_litter_date: date | None = Field(description="Birth, or expected birth, or mating of the latest litter known")
    litters_last_year_count: int | None = Field(description="As Chiens de France writes it, when it does")
    breeding_females_count: int | None
    current_litter: LitterCard | None = Field(description="The litter to talk about now, when there is one")
    is_followed: bool
    follow_status: BreederFollowStatus | None


class BreederDog(BaseModel):
    """A reproducer or a parent the breeder shows, as the detail lists it."""

    id: int
    role: DogRole
    name: str | None
    full_name: str | None
    sex: DogSex
    birth_date: date | None
    color: CoatColor
    color_code: str | None
    rating: int | None
    health_codes: list[str]
    e_locus: str | None
    photos: list[str]
    external_url: str | None
    availability_text: str | None


class BreederDetail(BreederCard):
    """A breeder as the detail screen shows it."""

    phone_e164: str | None
    siren: str | None
    website: str | None
    chiens_de_france_site_url: str | None
    facebook_url: str | None = Field(description="Facebook page the Centrale Canine site of the breeding declares")
    instagram_url: str | None = Field(description="Instagram account that site declares")
    youtube_url: str | None = Field(description="YouTube channel that site declares")
    scc_breeder_id: str | None
    links: list[BreederLink]
    notes: str | None
    chiens_de_france_registered_on: date | None
    scc_last_litter_at: datetime | None
    scc_directory_seen_at: datetime | None
    litters: list[LitterCard] = Field(description="Every litter known, the current ones first")
    color_shares: list[BreederColorShare]
    reproducers: list[BreederDog]
    photos: list[str] = Field(description="Photos of the breeding on its Centrale Canine site")
    follow: BreederFollowResponse | None


class BreederSearchResults(BaseModel):
    """The suggestions of the search: breeders, then litters."""

    breeders: list[BreederCard]
    litters: list[LitterCard]


class BreederCreate(BaseModel):
    """A breeder Léo adds by hand."""

    display_name: str = Field(..., min_length=1, max_length=255)
    city: str | None = Field(default=None, max_length=120)
    zip_code: str | None = Field(default=None, max_length=10)
    phone: str | None = Field(default=None, max_length=30)
    links: list[BreederLink] = Field(default_factory=list, max_length=10)
    notes: str | None = Field(default=None, max_length=4000)
    follow: bool = True


class BreederUpdate(BaseModel):
    """What Léo may change on a breeder: its links, its phone, its site, his notes."""

    links: list[BreederLink] | None = Field(default=None, max_length=10)
    phone: str | None = Field(default=None, max_length=30)
    website: str | None = Field(default=None, max_length=500)
    notes: str | None = Field(default=None, max_length=4000)
