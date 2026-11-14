"""Hand-made listings of one breeder, for the tests of the grouping and of the joining of split litters."""

from datetime import date, datetime

from sqlalchemy.orm import Session

from enums.listing_kind import ListingKind
from enums.listing_source import ListingSource
from models.breed import Breed
from models.breeder import Breeder
from models.listing import Listing
from seeders.run_seeders import SeederRunner

NOW = datetime(2026, 10, 28, 12, 0)


def add_listing(
    db: Session,
    breeder: Breeder,
    source: ListingSource,
    external_id: str,
    kind: ListingKind,
    dam_name: str | None,
    birth_date: date | None = None,
    mating_date: date | None = None,
    male_count: int | None = None,
    female_count: int | None = None,
    puppies_available: int | None = None,
    mating_number: str | None = None,
    available_from: date | None = None,
) -> Listing:
    """
    Store a listing of the cocker for a breeder.

    Args:
        db: Database session.
        breeder: Its breeder.
        source: Its source.
        external_id: Its identifier on the source.
        kind: Puppy ad, born or expected litter.
        dam_name: Name of the mother, if known.
        birth_date: Birth date, if known.
        mating_date: Mating date, if known.
        male_count: Males, if known.
        female_count: Females, if known.
        puppies_available: Puppies still offered, if the ad says.
        mating_number: Mating declaration number on the source, if given.
        available_from: Day the ad says the puppies may leave, if it gives one.

    Returns:
        The listing, flushed.
    """
    cocker = db.query(Breed).one()
    listing = Listing(
        source=source,
        external_id=external_id,
        breed_id=cocker.id,
        breeder_id=breeder.id,
        kind=kind,
        dam_name=dam_name,
        birth_date=birth_date,
        mating_date=mating_date,
        male_count=male_count,
        female_count=female_count,
        puppies_available=puppies_available,
        mating_number=mating_number,
        available_from=available_from,
        first_seen_at=NOW,
        last_seen_at=NOW,
    )
    db.add(listing)
    db.flush()
    return listing


def seeded_breeder(db: Session) -> Breeder:
    """The seeds, and one breeder."""
    SeederRunner.run(db)
    breeder = Breeder(display_name="Éleveur de test")
    db.add(breeder)
    db.flush()
    return breeder
