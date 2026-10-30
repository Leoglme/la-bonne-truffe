"""The sentences of the pushes: a litter of puppy ads is born, only a declared mating is « à naître »."""

from dataclasses import replace
from datetime import date

from enums.coat_color import CoatColor
from enums.color_confidence import ColorConfidence
from enums.listing_kind import ListingKind
from enums.lof_status import LofStatus
from enums.match_event_kind import MatchEventKind
from services.collectors.raw_listing import ColorReading
from services.matching.criteria import LitterSnapshot
from services.notification_texts import NotificationTexts

GOLD_PUPPY_ADS_IN_53 = LitterSnapshot(
    group_id=1,
    name="De la Vallée de la Mayenne",
    breed_slug="cocker-spaniel-anglais",
    kind=ListingKind.PUPPY_AD,
    department_code="53",
    department_name="Mayenne",
    colors=(ColorReading(CoatColor.GOLD, ColorConfidence.CERTAIN),),
    lof_status=LofStatus.LOF,
    male_count=2,
    female_count=0,
    puppies_available=2,
    price_cents=None,
    appeared_on=date(2026, 10, 28),
    birth_date=date(2026, 9, 14),
    expected_birth_date=None,
    available_from=date(2026, 11, 9),
    breeder_selection_group=None,
    sire_rating=None,
    dam_rating=None,
)


def test_a_litter_of_puppy_ads_is_told_as_born() -> None:
    body = NotificationTexts.litter_event(MatchEventKind.NEW_PREFERRED, GOLD_PUPPY_ADS_IN_53)

    assert body.startswith("Nouvelle portée, née le 14 septembre (Mayenne) : une portée gold, 2 mâles")
    assert body.endswith("Dispo vers le 9 novembre.")


def test_only_a_declared_mating_is_told_as_expected() -> None:
    mating = replace(
        GOLD_PUPPY_ADS_IN_53,
        kind=ListingKind.LITTER_EXPECTED,
        male_count=None,
        female_count=None,
        puppies_available=None,
        birth_date=None,
        expected_birth_date=date(2026, 12, 20),
        available_from=None,
    )

    body = NotificationTexts.litter_event(MatchEventKind.NEW_PREFERRED, mating)

    assert body == "À naître (Mayenne) : une portée gold déclarée, naissance vers le 20 décembre."
