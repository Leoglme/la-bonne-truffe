"""MatchingService: the hard filters, the tiers and the score of docs/04."""

from dataclasses import replace
from datetime import date

import pytest

from enums.coat_color import CoatColor
from enums.color_confidence import ColorConfidence
from enums.color_preference_level import ColorPreferenceLevel
from enums.listing_kind import ListingKind
from enums.lof_preference import LofPreference
from enums.lof_status import LofStatus
from enums.match_flag import MatchFlag
from enums.match_tier import MatchTier
from enums.sex_preference import SexPreference
from services.collectors.raw_listing import ColorReading
from services.matching.criteria import LitterSnapshot, ProfileCriteria
from services.matching.matching_service import MatchingService

TODAY = date(2026, 10, 28)

LEO = ProfileCriteria(
    profile_id=1,
    breed_slugs=frozenset({"cocker-spaniel-anglais"}),
    department_codes=("35", "56", "22", "29", "44", "53", "49", "72", "85"),
    include_expected_litters=True,
    sex_preference=SexPreference.ANY,
    lof_preference=LofPreference.PREFERRED,
    color_levels={
        CoatColor.GOLD: ColorPreferenceLevel.PREFERRED,
        CoatColor.NOIR_ET_FEU: ColorPreferenceLevel.ACCEPTABLE,
    },
    price_max_cents=None,
)

GOLD_BORN_IN_35 = LitterSnapshot(
    group_id=1,
    name="Du Clos de l'Élevage A",
    breed_slug="cocker-spaniel-anglais",
    kind=ListingKind.LITTER_BORN,
    department_code="35",
    department_name="Ille-et-Vilaine",
    colors=(ColorReading(CoatColor.GOLD, ColorConfidence.CERTAIN),),
    lof_status=LofStatus.LOF,
    male_count=2,
    female_count=3,
    puppies_available=None,
    price_cents=None,
    appeared_on=date(2026, 10, 24),
    birth_date=date(2026, 10, 27),
    expected_birth_date=None,
    available_from=date(2026, 12, 22),
    breeder_selection_group=2,
    sire_rating=None,
    dam_rating=None,
)

BLACK_AND_TAN_BUNDLE = (
    ColorReading(CoatColor.NOIR, ColorConfidence.AMBIGUOUS),
    ColorReading(CoatColor.NOIR_ET_FEU, ColorConfidence.AMBIGUOUS),
)


def test_gold_litter_born_in_the_closest_department_scores_96_and_is_preferred() -> None:
    verdict = MatchingService.evaluate(GOLD_BORN_IN_35, LEO, TODAY)

    assert verdict.tier == MatchTier.PREFERRED
    assert verdict.score == 96
    assert [reason.points for reason in verdict.reasons] == [40, 20, 15, 11, 10]
    assert verdict.reasons[0].text == "Gold, ta couleur préférée"
    assert verdict.flags == ()


def test_score_is_capped_at_100_with_bonuses() -> None:
    selected = replace(GOLD_BORN_IN_35, appeared_on=TODAY, breeder_selection_group=1, sire_rating=4, dam_rating=5)

    verdict = MatchingService.evaluate(selected, LEO, TODAY)

    assert verdict.score == 100
    assert sum(reason.points for reason in verdict.reasons) == 105


@pytest.mark.parametrize(
    "excluded_litter",
    [
        pytest.param(replace(GOLD_BORN_IN_35, breed_slug="berger-australien"), id="breed outside the profile"),
        pytest.param(replace(GOLD_BORN_IN_35, department_code="75"), id="department outside the list"),
        pytest.param(
            replace(GOLD_BORN_IN_35, colors=(ColorReading(CoatColor.BLEU_ROUAN, ColorConfidence.CERTAIN),)),
            id="certain ignored colour",
        ),
        pytest.param(replace(GOLD_BORN_IN_35, price_cents=300_000), id="price above the ceiling"),
    ],
)
def test_hard_filters_exclude(excluded_litter: LitterSnapshot) -> None:
    criteria = replace(LEO, price_max_cents=200_000)

    assert MatchingService.evaluate(excluded_litter, criteria, TODAY).tier == MatchTier.EXCLUDED


def test_expected_litters_are_excluded_when_the_profile_does_not_want_them() -> None:
    expected = replace(GOLD_BORN_IN_35, kind=ListingKind.LITTER_EXPECTED, male_count=None, female_count=None)

    assert MatchingService.evaluate(expected, LEO, TODAY).tier == MatchTier.PREFERRED
    assert MatchingService.evaluate(expected, replace(LEO, include_expected_litters=False), TODAY).tier == (
        MatchTier.EXCLUDED
    )


def test_wanted_sex_known_absent_excludes_but_unknown_never_filters() -> None:
    wants_a_male = replace(LEO, sex_preference=SexPreference.MALE)
    only_females = replace(GOLD_BORN_IN_35, male_count=0, female_count=4)
    not_born_yet = replace(GOLD_BORN_IN_35, kind=ListingKind.LITTER_EXPECTED, male_count=None, female_count=None)

    assert MatchingService.evaluate(only_females, wants_a_male, TODAY).tier == MatchTier.EXCLUDED
    unknown_verdict = MatchingService.evaluate(not_born_yet, wants_a_male, TODAY)
    assert unknown_verdict.tier == MatchTier.ACCEPTABLE
    assert MatchFlag.SEX_UNKNOWN in unknown_verdict.flags


def test_ambiguous_bundle_with_an_acceptable_colour_is_acceptable() -> None:
    bundle = replace(GOLD_BORN_IN_35, colors=BLACK_AND_TAN_BUNDLE)

    verdict = MatchingService.evaluate(bundle, LEO, TODAY)

    assert verdict.tier == MatchTier.ACCEPTABLE
    assert verdict.reasons[0].text == "Couleur à confirmer : noir ou noir et feu"
    assert verdict.reasons[0].points == 20
    assert MatchFlag.COLOR_TO_CONFIRM in verdict.flags


def test_ambiguous_bundle_of_ignored_colours_is_ignored_not_excluded() -> None:
    roans = (
        ColorReading(CoatColor.BLEU_ROUAN, ColorConfidence.AMBIGUOUS),
        ColorReading(CoatColor.ORANGE_ROUAN, ColorConfidence.AMBIGUOUS),
    )

    assert MatchingService.evaluate(replace(GOLD_BORN_IN_35, colors=roans), LEO, TODAY).tier == MatchTier.IGNORED


def test_lof_preferred_keeps_non_lof_visible_as_acceptable_and_required_excludes_it() -> None:
    non_lof = replace(GOLD_BORN_IN_35, lof_status=LofStatus.NON_LOF)

    assert MatchingService.evaluate(non_lof, LEO, TODAY).tier == MatchTier.ACCEPTABLE
    assert MatchingService.evaluate(non_lof, replace(LEO, lof_preference=LofPreference.REQUIRED), TODAY).tier == (
        MatchTier.EXCLUDED
    )


def test_unknown_colour_earns_10_and_stays_acceptable() -> None:
    verdict = MatchingService.evaluate(replace(GOLD_BORN_IN_35, colors=()), LEO, TODAY)

    assert verdict.tier == MatchTier.ACCEPTABLE
    assert verdict.reasons[0].points == 10


def test_proximity_decreases_with_the_rank_and_never_drops_below_2() -> None:
    second = MatchingService.evaluate(
        replace(GOLD_BORN_IN_35, department_code="56", department_name="Morbihan"), LEO, TODAY
    )
    last = MatchingService.evaluate(
        replace(GOLD_BORN_IN_35, department_code="85", department_name="Vendée"), LEO, TODAY
    )

    assert second.reasons[-1].points == 9
    assert second.reasons[-1].text == "Morbihan, 2e département de ta liste"
    assert last.reasons[-1].points == 2


def test_freshness_fades_to_nothing_after_14_days() -> None:
    old = MatchingService.evaluate(replace(GOLD_BORN_IN_35, appeared_on=date(2026, 10, 1)), LEO, TODAY)

    assert all("Apparue" not in reason.text for reason in old.reasons)
