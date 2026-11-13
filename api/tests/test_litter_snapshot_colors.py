"""The colours a litter shows when its ads, its parents and its Centrale Canine variety do not say the same."""

from datetime import datetime

from enums.listing_kind import ListingKind
from enums.listing_source import ListingSource
from enums.lof_status import LofStatus
from models.listing import Listing
from models.litter_group import LitterGroup
from services.matching.snapshot_builder import LitterSnapshotBuilder

SEEN_AT = datetime(2026, 11, 10, 9, 0)
GOLD_VARIETY_ID = "158"
ONE_GOLD_PUPPY_IN_TWO: list[dict[str, str | float]] = [
    {"color": "gold", "confidence": "ambiguous", "reason": "Gold possible, un chiot sur deux", "puppy_odds": 0.5},
    {"color": "noir_et_feu", "confidence": "ambiguous", "reason": "Gold possible, un chiot sur deux"},
]


def litter_group(expected_colors: list[dict[str, str | float]]) -> LitterGroup:
    """
    A litter group, with the colours its parents imply.

    Args:
        expected_colors: What the genotypes of the parents give, empty while their pages are not read.

    Returns:
        The group, not stored.
    """
    return LitterGroup(id=1, breed_id=1, first_seen_at=SEEN_AT, last_seen_at=SEEN_AT, expected_colors=expected_colors)


def litter_declared_under_the_gold_variety() -> Listing:
    """
    A born litter as the Centrale Canine declares it, filed under « rouge et doré ».

    Returns:
        The listing, not stored.
    """
    return Listing(
        source=ListingSource.CENTRALE_CANINE,
        external_id="4315368",
        breed_id=1,
        kind=ListingKind.LITTER_BORN,
        lof_status=LofStatus.LOF,
        variety_source_id=GOLD_VARIETY_ID,
        colors=[{"color": "gold", "confidence": "certain"}],
        is_active=True,
        first_seen_at=SEEN_AT,
        last_seen_at=SEEN_AT,
    )


def puppy_ad(colors: list[dict[str, str]]) -> Listing:
    """
    A puppy ad of the breeder's site, with the colours it states.

    Args:
        colors: The colours of the ad, as stored.

    Returns:
        The listing, not stored.
    """
    return Listing(
        source=ListingSource.CHIENS_DE_FRANCE,
        external_id="chiot-2211112",
        breed_id=1,
        kind=ListingKind.PUPPY_AD,
        lof_status=LofStatus.LOF,
        colors=colors,
        is_active=True,
        first_seen_at=SEEN_AT,
        last_seen_at=SEEN_AT,
    )


def colors_of(group: LitterGroup, listings: list[Listing]) -> list[tuple[str, str]]:
    """
    The colours the snapshot of a group keeps.

    Args:
        group: The group.
        listings: Its listings.

    Returns:
        Each colour with its confidence, in order.
    """
    snapshot = LitterSnapshotBuilder.build_from_listings(group, listings, breed=None, breeder=None, department=None)
    assert snapshot is not None
    return [(reading.color.value, reading.confidence.value) for reading in snapshot.colors]


def test_a_gold_mother_and_a_father_that_only_carries_the_gold_do_not_make_a_gold_litter() -> None:
    colors = colors_of(litter_group(ONE_GOLD_PUPPY_IN_TWO), [litter_declared_under_the_gold_variety()])

    assert colors == [("gold", "ambiguous"), ("noir_et_feu", "ambiguous")]


def test_the_variety_tells_the_colour_while_nothing_is_known_of_the_parents() -> None:
    colors = colors_of(litter_group([]), [litter_declared_under_the_gold_variety()])

    assert colors == [("gold", "certain")]


def test_the_colour_an_ad_states_wins_over_the_parents_and_the_variety() -> None:
    listings = [
        litter_declared_under_the_gold_variety(),
        puppy_ad([{"color": "noir_et_feu", "confidence": "certain"}]),
    ]

    assert colors_of(litter_group(ONE_GOLD_PUPPY_IN_TWO), listings) == [("noir_et_feu", "certain")]


def test_a_bundle_an_ad_states_wins_over_the_variety_when_the_parents_tell_nothing() -> None:
    listings = [
        litter_declared_under_the_gold_variety(),
        puppy_ad([{"color": "gold", "confidence": "ambiguous"}, {"color": "noir_et_feu", "confidence": "ambiguous"}]),
    ]

    assert colors_of(litter_group([]), listings) == [("gold", "ambiguous"), ("noir_et_feu", "ambiguous")]
