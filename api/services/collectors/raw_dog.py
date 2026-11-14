"""The common output of the collectors that read dogs and breeder profiles, before it is stored."""

from dataclasses import dataclass
from datetime import date, datetime

from enums.coat_color import CoatColor
from enums.dog_role import DogRole
from enums.dog_sex import DogSex
from enums.listing_source import ListingSource


@dataclass(frozen=True)
class RawDog:
    """
    A dog as one source describes it, already in the canonical vocabulary. Unknown facts stay None.

    ``external_id`` is the dog's identifier on that source: the LOF Select id at the Centrale Canine, the
    ``/chien/<id>`` of a breeder's site on Chiens de France. ``breeder_source_id`` names the breeding that
    presents the dog, with the identifier the listings of the same source use for it.
    """

    source: ListingSource
    external_id: str
    role: DogRole
    external_url: str | None = None
    litter_group_id: int | None = None
    breeder_source_id: str | None = None
    name: str | None = None
    affix: str | None = None
    full_name: str | None = None
    sex: DogSex = DogSex.UNKNOWN
    birth_date: date | None = None
    lof_number: str | None = None
    identifier: str | None = None
    color_code: str | None = None
    color: CoatColor = CoatColor.INCONNUE
    rating: int | None = None
    health_codes: tuple[str, ...] = ()
    e_locus: str | None = None
    has_dna_profile: bool | None = None
    sire_external_id: str | None = None
    dam_external_id: str | None = None
    sire_color_code: str | None = None
    dam_color_code: str | None = None
    photos: tuple[str, ...] = ()
    availability_text: str | None = None


@dataclass(frozen=True)
class RawBreederProfile:
    """
    A breeder as the Centrale Canine directory, or the Spaniel Club directory, lists it.

    ``source_id`` is the Centrale Canine breeder identifier (``u_breeder_id``), the one the litters carry as
    ``n_breeder_id``; the matching across sources follows docs/03 (SIREN, identifier, phone, affix and department).
    """

    source_id: str
    scc_user_id: str | None = None
    breeder_number: str | None = None
    display_name: str | None = None
    affix: str | None = None
    siren: str | None = None
    phone_e164: str | None = None
    zip_code: str | None = None
    city: str | None = None
    department_code: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    logo_url: str | None = None
    site_slug: str | None = None
    variety_ids: tuple[str, ...] = ()
    last_litter_at: datetime | None = None
    is_breed_club_member: bool | None = None
    is_selected: bool | None = None


@dataclass(frozen=True)
class RawBreederSiteLitter:
    """
    A litter the « Chiots nés chez nous » page of a breeder's site lists: when it was born, its parents, and the
    number of its page (``/chiots-a-vendre/<id>``).
    """

    birth_date: date
    sire_name: str | None = None
    dam_name: str | None = None
    litter_id: str | None = None


@dataclass(frozen=True)
class RawBreederSiteFacts:
    """
    What the site of a breeder on Chiens de France says of the breeding itself, beyond its litters for sale and its
    dogs. ``litters_born`` stays None when the « Chiots nés chez nous » page could not be read.
    """

    breeder_source_id: str
    site_url: str
    cover_photo_url: str | None = None
    breeding_females_count: int | None = None
    litters_last_year_count: int | None = None
    registered_on: date | None = None
    facebook_url: str | None = None
    instagram_url: str | None = None
    youtube_url: str | None = None
    litters_born: tuple[RawBreederSiteLitter, ...] | None = None


@dataclass(frozen=True)
class RawSiteDirectoryEntry:
    """A breeder as the regional list of the breeders of a breed on Chiens de France shows it, with its site."""

    site_url: str
    name: str
    zip_code: str | None = None
    town: str | None = None
