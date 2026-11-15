"""The litters of each mother of a breeding: her next litter, likely a year after her last one, the rhythm of the
breeding, and the mother's age and litters on the page of a litter (docs/04, « Les portées probables »)."""

from datetime import date, datetime

import pytest
from sqlalchemy.orm import Session

from enums.coat_color import CoatColor
from enums.color_confidence import ColorConfidence
from enums.dog_role import DogRole
from enums.dog_sex import DogSex
from enums.listing_kind import ListingKind
from enums.listing_source import ListingSource
from enums.lof_status import LofStatus
from models.breed import Breed
from models.breeder import Breeder
from models.dog import Dog
from models.listing import Listing
from models.litter_group import LitterGroup
from models.search_profile import SearchProfile
from models.user import User
from schemas.breeder import BreederFilter, BreederSort
from seeders.run_seeders import SeederRunner
from services.breeder_query_service import BreederQueryService
from services.dam_litter_history import DamLitterHistory
from services.litter_query_service import LitterQueryService

TODAY = date(2026, 11, 15)


@pytest.fixture
def breeder(db: Session) -> Breeder:
    """The seeds, and a breeding of Ille-et-Vilaine whose site lists the litters of its mothers."""
    SeederRunner.run(db)
    breeding = Breeder(affix="Du Clos de Test", city="Rennes", department_code="35")
    db.add(breeding)
    db.commit()
    return breeding


def add_dog(db: Session, breeder: Breeder, full_name: str, sex: DogSex, color: CoatColor, **columns: object) -> Dog:
    """
    Store a reproducer of a breeding as its site shows it.

    Args:
        db: Database session.
        breeder: The breeding.
        full_name: Its name with the affix.
        sex: Its sex.
        color: Its colour.
        columns: Other columns of the dog.

    Returns:
        The dog, flushed.
    """
    dog = Dog(
        breeder_id=breeder.id,
        source=ListingSource.CHIENS_DE_FRANCE,
        external_id=full_name,
        role=DogRole.REPRODUCER,
        full_name=full_name,
        name=full_name.split()[0],
        sex=sex,
        color=color,
    )
    for name, value in columns.items():
        setattr(dog, name, value)
    db.add(dog)
    db.flush()
    return dog


def add_born_litter(db: Session, breeder: Breeder, dam_name: str, sire_name: str, born_on: date) -> LitterGroup:
    """
    Store a born litter of the Centrale Canine with its group.

    Args:
        db: Database session.
        breeder: The breeding.
        dam_name: Its mother as the declaration names her.
        sire_name: Its father.
        born_on: Its birth.

    Returns:
        The group, flushed.
    """
    group = LitterGroup(
        breed_id=db.query(Breed).one().id,
        breeder_id=breeder.id,
        birth_date=born_on,
        first_seen_at=datetime(2026, 11, 1),
        last_seen_at=datetime(2026, 11, 1),
    )
    db.add(group)
    db.flush()
    db.add(
        Listing(
            source=ListingSource.CENTRALE_CANINE,
            external_id=f"portee-{dam_name}-{born_on.isoformat()}",
            breed_id=group.breed_id,
            breeder_id=breeder.id,
            litter_group_id=group.id,
            kind=ListingKind.LITTER_BORN,
            lof_status=LofStatus.LOF,
            birth_date=born_on,
            dam_name=dam_name,
            sire_name=sire_name,
            department_code="35",
        )
    )
    db.flush()
    return group


def test_the_mothers_join_their_litters_of_the_app_and_of_the_site_whatever_their_titles(
    db: Session, breeder: Breeder
) -> None:
    add_born_litter(db, breeder, "CH. Selune du Clos de Test", "Valentino du Clos aux Tests", date(2026, 10, 8))
    breeder.chiens_de_france_litters = [
        {"birth_date": "2026-10-09", "sire_name": "", "dam_name": "Selune Du Clos De Test"},
        {"birth_date": "2025-11-19", "sire_name": "Valentino du Clos aux Tests", "dam_name": "Selune Du Clos De Test"},
        {"birth_date": "2026-03-01", "sire_name": "Marco", "dam_name": "Sweety so love suzy Du Clos De Test"},
        {"birth_date": "2026-03-02", "sire_name": "Marco", "dam_name": "Sweety So Love Susy Du Clos De Test"},
    ]
    selune = add_dog(db, breeder, "Selune Du Clos de Test", DogSex.FEMALE, CoatColor.GOLD)
    db.commit()

    mothers = DamLitterHistory.of_breeders(db, [breeder.id])[breeder.id]

    by_key = {mother.key: mother for mother in mothers}
    assert set(by_key) == {"selune du clos de test", "sweety so love suzy du clos de test"}
    assert by_key["selune du clos de test"].birth_dates == [date(2025, 11, 19), date(2026, 10, 8)]
    assert by_key["selune du clos de test"].dogs == [selune]
    assert by_key["selune du clos de test"].name == "Selune"
    assert by_key["sweety so love suzy du clos de test"].birth_dates == [date(2026, 3, 1)]


def test_a_mother_is_the_same_whether_her_name_is_numbered_or_titled() -> None:
    assert DamLitterHistory.key_of("Violette 1 du Clos de l'Ecotay") == DamLitterHistory.key_of(
        "Violette Du Clos De L'Ecotay"
    )
    assert (
        DamLitterHistory.key_of("TR. CH. So pretty dite shanelle De kerfeuil") == "so pretty dite shanelle de kerfeuil"
    )
    assert DamLitterHistory.key_of("Selune 2") == "selune"


def test_a_mother_is_likely_to_have_her_next_litter_a_year_after_her_last_one(db: Session, breeder: Breeder) -> None:
    breeder.chiens_de_france_litters = [
        {"birth_date": "2025-11-19", "sire_name": "", "dam_name": "Selune du Clos de Test"},
        {"birth_date": "2025-12-25", "sire_name": "", "dam_name": "Reggae du Clos de Test"},
        {"birth_date": "2026-02-01", "sire_name": "", "dam_name": "Vodka du Clos de Test"},
        {"birth_date": "2026-05-01", "sire_name": "", "dam_name": "Prune du Clos de Test"},
        {"birth_date": "2025-09-01", "sire_name": "", "dam_name": "Ancienne du Clos de Test"},
        {"birth_date": "2025-12-01", "sire_name": "", "dam_name": "Retraitee du Clos de Test"},
        {"birth_date": "2025-12-01", "sire_name": "", "dam_name": "Doyenne du Clos de Test"},
    ]
    add_dog(db, breeder, "Retraitee du Clos de Test", DogSex.FEMALE, CoatColor.GOLD, availability_text="Retraitée")
    add_dog(db, breeder, "Doyenne du Clos de Test", DogSex.FEMALE, CoatColor.GOLD, birth_date=date(2018, 6, 1))
    db.commit()

    mothers = DamLitterHistory.of_breeders(db, [breeder.id])[breeder.id]
    estimates = DamLitterHistory.probable_litters(mothers, TODAY)

    assert [(estimate.dam.name, estimate.expected_on) for estimate in estimates] == [
        ("Selune du Clos de Test", date(2026, 11, 19)),
        ("Reggae du Clos de Test", date(2026, 12, 25)),
        ("Vodka du Clos de Test", date(2027, 2, 1)),
    ]


def test_a_mother_with_a_litter_announced_has_no_probable_one(db: Session, breeder: Breeder) -> None:
    breeder.chiens_de_france_litters = [
        {"birth_date": "2025-11-19", "sire_name": "", "dam_name": "Selune du Clos de Test"},
    ]
    announced = LitterGroup(
        breed_id=db.query(Breed).one().id,
        breeder_id=breeder.id,
        expected_birth_date=date(2026, 12, 20),
        first_seen_at=datetime(2026, 11, 1),
        last_seen_at=datetime(2026, 11, 1),
    )
    db.add(announced)
    db.flush()
    db.add(
        Listing(
            source=ListingSource.CENTRALE_CANINE,
            external_id="saillie-1",
            breed_id=announced.breed_id,
            breeder_id=breeder.id,
            litter_group_id=announced.id,
            kind=ListingKind.LITTER_EXPECTED,
            lof_status=LofStatus.LOF,
            dam_name="Selune du Clos de Test",
            department_code="35",
        )
    )
    db.commit()

    mothers = DamLitterHistory.of_breeders(db, [breeder.id])[breeder.id]

    assert DamLitterHistory.probable_litters(mothers, TODAY) == []


def test_the_rhythm_of_a_breeding_is_the_middle_gap_between_two_litters_of_a_mother(
    db: Session, breeder: Breeder
) -> None:
    breeder.chiens_de_france_litters = [
        {"birth_date": "2025-01-10", "sire_name": "", "dam_name": "Selune du Clos de Test"},
        {"birth_date": "2026-01-10", "sire_name": "", "dam_name": "Selune du Clos de Test"},
        {"birth_date": "2025-03-01", "sire_name": "", "dam_name": "Prune du Clos de Test"},
        {"birth_date": "2025-10-01", "sire_name": "", "dam_name": "Prune du Clos de Test"},
        {"birth_date": "2026-09-01", "sire_name": "", "dam_name": "Prune du Clos de Test"},
    ]
    db.commit()
    mothers = DamLitterHistory.of_breeders(db, [breeder.id])[breeder.id]

    assert DamLitterHistory.median_gap_months(mothers) == 11
    selune = [mother for mother in mothers if mother.key == "selune du clos de test"]
    assert DamLitterHistory.median_gap_months(selune) is None


def test_the_breeder_screens_show_the_probable_litters_of_a_wanted_colour(db: Session, breeder: Breeder) -> None:
    breeder.chiens_de_france_litters = [
        {"birth_date": "2025-11-19", "sire_name": "Valentino du Clos de Test", "dam_name": "Selune du Clos de Test"},
        {"birth_date": "2025-12-01", "sire_name": "", "dam_name": "Bleuette du Clos de Test"},
    ]
    add_dog(db, breeder, "Selune du Clos de Test", DogSex.FEMALE, CoatColor.GOLD)
    add_dog(db, breeder, "Valentino du Clos de Test", DogSex.MALE, CoatColor.GOLD)
    add_dog(db, breeder, "Bleuette du Clos de Test", DogSex.FEMALE, CoatColor.BLEU_ROUAN)
    db.commit()
    user = db.query(User).one()
    profile = db.query(SearchProfile).one()

    detail = BreederQueryService.detail(db, user.id, breeder.id)
    probable_breeders = BreederQueryService.list_cards(db, user.id, BreederFilter.PROBABLE_LITTER, BreederSort.NAME)

    assert profile.color_preferences.get("bleu_rouan") is None
    assert [(litter.dam_name, litter.expected_on) for litter in detail.probable_litters] == [
        ("Selune", date(2026, 11, 19))
    ]
    assert [(color.color, color.confidence) for color in detail.probable_litters[0].colors] == [
        (CoatColor.GOLD, ColorConfidence.INFERRED)
    ]
    assert [card.id for card in probable_breeders] == [breeder.id]
    assert probable_breeders[0].next_probable_litter == detail.probable_litters[0]


def test_the_page_of_a_litter_tells_the_age_of_the_mother_and_her_litter_before(db: Session, breeder: Breeder) -> None:
    group = add_born_litter(db, breeder, "Versace du Clos de Test", "Valko", date(2026, 10, 8))
    breeder.chiens_de_france_litters = [
        {"birth_date": "2026-03-06", "sire_name": "Valko", "dam_name": "Versace Du Clos De Test"},
    ]
    add_dog(db, breeder, "Versace du Clos de Test", DogSex.FEMALE, CoatColor.INCONNUE, birth_date=date(2024, 6, 2))
    db.commit()
    user = db.query(User).one()

    dam = LitterQueryService.detail(db, user.id, group.id).dam

    assert dam is not None
    assert (dam.age_years, dam.litter_rank, dam.months_since_previous_litter) == (2, 2, 7)
