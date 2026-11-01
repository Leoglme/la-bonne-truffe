"""The colour codes of the sources, and what a couple of parents implies for their puppies."""

import pytest

from enums.coat_color import CoatColor
from enums.color_confidence import ColorConfidence
from services.dog_color_inference import DogColorInference, ParentColorFacts


@pytest.mark.parametrize(
    ("code", "color"),
    [
        ("F.Or.", CoatColor.GOLD),
        ("F.Cl.", CoatColor.GOLD),
        ("F.Fo.", CoatColor.GOLD),
        ("Noi.", CoatColor.NOIR),
        ("Noi. Mar.Fau.", CoatColor.NOIR_ET_FEU),
        ("Noi. Mar.Fau. Pan.Bla.Gri.", CoatColor.TRICOLORE),
        ("Noi. Pan.Bla.", CoatColor.PARTICOLORE),
        ("Fau. Pan.Bla.Rou.", CoatColor.ORANGE_ROUAN),
        ("Ble. Rou.", CoatColor.BLEU_ROUAN),
        ("Mar. Fau.", CoatColor.MARRON_ET_FEU),
        ("Tri.", CoatColor.TRICOLORE),
        ("Noire et blanche", CoatColor.PARTICOLORE),
        ("Golden", CoatColor.GOLD),
        ("Noir et feu", CoatColor.NOIR_ET_FEU),
        ("Bleu rouan", CoatColor.BLEU_ROUAN),
        ("", CoatColor.INCONNUE),
        (None, CoatColor.INCONNUE),
        ("Xyz.", CoatColor.INCONNUE),
    ],
)
def test_a_colour_code_becomes_a_canonical_colour(code: str | None, color: CoatColor) -> None:
    assert DogColorInference.canonical_color(code) == color


def test_the_e_locus_is_read_among_the_health_codes() -> None:
    assert DogColorInference.e_locus_of(("FN-1.1", "PRCD-1.1", "LocE-e/e")) == "e/e"
    assert DogColorInference.e_locus_of(["LocE-E/e"]) == "E/e"
    assert DogColorInference.e_locus_of(["FN-1.1"]) is None


def test_the_mask_test_counts_as_the_e_locus() -> None:
    assert DogColorInference.e_locus_of(["PRCD-1.2", "LocEm-Em/e"]) == "E/e"
    assert DogColorInference.e_locus_of(["LocEm-Em/Em"]) == "E/E"
    assert DogColorInference.e_locus_of(["LocEm-e/Em"]) == "E/e"


@pytest.mark.parametrize(
    ("code", "has_gold_coat"),
    [
        ("F.Or.", True),
        ("Fau. Pan.Bla.Rou.", True),
        ("Golden", True),
        ("Orange rouan", True),
        ("Noi. Mar.Fau. Pan.Bla.Gri.", False),
        ("Noire et blanche", False),
        (None, False),
    ],
)
def test_the_coats_of_the_gold_family_are_told_apart(code: str | None, has_gold_coat: bool) -> None:
    assert DogColorInference.has_gold_coat(code) is has_gold_coat


def test_a_dog_with_a_gold_parent_carries_the_gold_without_a_test() -> None:
    tricolour_daughter = ParentColorFacts(CoatColor.TRICOLORE, has_gold_parent=True)
    gold_daughter = ParentColorFacts(CoatColor.GOLD, has_gold_parent=True)
    tested_daughter = ParentColorFacts(CoatColor.TRICOLORE, e_locus="E/E", has_gold_parent=True)

    assert (tricolour_daughter.genotype, tricolour_daughter.carries_gold_by_parents) == ("E/e", True)
    assert (gold_daughter.genotype, gold_daughter.carries_gold_by_parents) == ("e/e", False)
    assert (tested_daughter.genotype, tested_daughter.carries_gold_by_parents) == ("E/E", False)


def test_two_gold_parents_make_a_gold_litter_certain() -> None:
    expected = DogColorInference.expected_colors(
        ParentColorFacts(CoatColor.GOLD), ParentColorFacts(CoatColor.GOLD, e_locus="e/e")
    )

    assert [(color.color, color.confidence) for color in expected] == [(CoatColor.GOLD, ColorConfidence.INFERRED)]
    assert expected[0].reason == "Gold : les deux parents sont gold"
    assert expected[0].puppy_odds == 1.0


def test_one_gold_parent_makes_gold_possible_beside_the_other_colour() -> None:
    expected = DogColorInference.expected_colors(
        ParentColorFacts(CoatColor.NOIR_ET_FEU), ParentColorFacts(CoatColor.GOLD)
    )

    assert [(color.color, color.confidence) for color in expected] == [
        (CoatColor.GOLD, ColorConfidence.AMBIGUOUS),
        (CoatColor.NOIR_ET_FEU, ColorConfidence.AMBIGUOUS),
    ]
    assert expected[0].reason == "Gold possible : un parent gold, l’autre noir et feu"
    assert expected[0].puppy_odds is None


def test_a_carrier_parent_gives_one_gold_puppy_in_two() -> None:
    tested = DogColorInference.expected_colors(
        ParentColorFacts(CoatColor.GOLD), ParentColorFacts(CoatColor.NOIR, e_locus="E/e")
    )
    by_parents = DogColorInference.expected_colors(
        ParentColorFacts(CoatColor.GOLD), ParentColorFacts(CoatColor.TRICOLORE, has_gold_parent=True)
    )

    assert tested[0].reason == "Gold possible, un chiot sur deux : un parent gold, l’autre noir porteur du gold"
    assert (tested[0].puppy_odds, tested[1].puppy_odds) == (0.5, None)
    assert by_parents[0].puppy_odds == 0.5
    assert by_parents[0].as_json()["puppy_odds"] == 0.5


def test_two_carriers_give_one_gold_puppy_in_four() -> None:
    expected = DogColorInference.expected_colors(
        ParentColorFacts(CoatColor.NOIR, e_locus="E/e"), ParentColorFacts(CoatColor.TRICOLORE, has_gold_parent=True)
    )

    assert [(color.color, color.puppy_odds) for color in expected] == [
        (CoatColor.GOLD, 0.25),
        (CoatColor.NOIR, None),
        (CoatColor.TRICOLORE, None),
    ]
    assert expected[0].reason == "Gold possible, un chiot sur quatre : les deux parents portent le gold"


def test_a_parent_that_does_not_carry_the_gold_rules_it_out() -> None:
    expected = DogColorInference.expected_colors(
        ParentColorFacts(CoatColor.GOLD), ParentColorFacts(CoatColor.NOIR, e_locus="E/E")
    )

    assert [(color.color, color.confidence) for color in expected] == [(CoatColor.NOIR, ColorConfidence.AMBIGUOUS)]


def test_nothing_is_said_without_both_parents_or_without_a_gold_one() -> None:
    assert DogColorInference.expected_colors(ParentColorFacts(CoatColor.GOLD), None) == ()
    assert DogColorInference.expected_colors(ParentColorFacts(CoatColor.NOIR), ParentColorFacts(CoatColor.MARRON)) == ()
