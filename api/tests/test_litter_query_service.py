"""LitterQueryService: the parents of the detail come from the listings that name them, Centrale Canine first."""

from datetime import date, datetime

from sqlalchemy.orm import Session

from enums.listing_kind import ListingKind
from enums.listing_source import ListingSource
from enums.lof_status import LofStatus
from models.breed import Breed
from models.breeder import Breeder
from models.listing import Listing
from models.litter_group import LitterGroup
from models.user import User
from seeders.run_seeders import SeederRunner
from services.litter_query_service import LitterQueryService

SEEN_AT = datetime(2026, 10, 28, 9, 0)


def add_listing_of_group(
    db: Session,
    group: LitterGroup,
    source: ListingSource,
    kind: ListingKind,
    sire_rating: int | None,
    dam_name: str | None,
) -> Listing:
    """
    Store a listing of the group that names the father « Père de test », with or without his rating.

    Args:
        db: Database session.
        group: The group.
        source: Source of the listing.
        kind: Puppy ad or birth declaration.
        sire_rating: Rating of the father, when the source gives it.
        dam_name: Name of the mother, when the source gives it.

    Returns:
        The listing, flushed.
    """
    listing = Listing(
        source=source,
        external_id=f"{source.value}-1",
        breed_id=group.breed_id,
        breeder_id=group.breeder_id,
        litter_group_id=group.id,
        kind=kind,
        lof_status=LofStatus.LOF,
        birth_date=date(2026, 9, 1),
        male_count=1,
        female_count=0,
        sire_name="Père de test",
        sire_rating=sire_rating,
        dam_name=dam_name,
        dam_rating=3 if dam_name else None,
        first_seen_at=SEEN_AT,
        last_seen_at=SEEN_AT,
    )
    db.add(listing)
    db.flush()
    return listing


def test_the_parents_take_the_rating_of_the_centrale_canine_even_when_another_source_came_first(db: Session) -> None:
    SeederRunner.run(db)
    breeder = Breeder(affix="Du Clos de test", department_code="35")
    db.add(breeder)
    db.flush()
    group = LitterGroup(
        breed_id=db.query(Breed).one().id,
        breeder_id=breeder.id,
        birth_date=date(2026, 9, 1),
        first_seen_at=SEEN_AT,
        last_seen_at=SEEN_AT,
    )
    db.add(group)
    db.flush()
    add_listing_of_group(
        db, group, ListingSource.CHIENS_DE_FRANCE, ListingKind.PUPPY_AD, sire_rating=None, dam_name=None
    )
    add_listing_of_group(
        db, group, ListingSource.CENTRALE_CANINE, ListingKind.LITTER_BORN, sire_rating=4, dam_name="Mère de test"
    )
    db.commit()

    detail = LitterQueryService.detail(db, db.query(User).one().id, group.id)

    assert detail.sire is not None and (detail.sire.name, detail.sire.rating) == ("Père de test", 4)
    assert detail.dam is not None and (detail.dam.name, detail.dam.rating) == ("Mère de test", 3)
