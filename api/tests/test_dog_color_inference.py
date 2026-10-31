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
        ("Noi. Pan.Bla.", CoatColor.PARTICOLORE),
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


def test_two_gold_parents_make_a_gold_litter_certain() -> None:
    expected = DogColorInference.expected_colors(
        ParentColorFacts(CoatColor.GOLD), ParentColorFacts(CoatColor.GOLD, e_locus="e/e")
    )

    assert [(color.color, color.confidence) for color in expected] == [(CoatColor.GOLD, ColorConfidence.INFERRED)]
    assert expected[0].reason == "Gold : les deux parents sont gold"


def test_one_gold_parent_makes_gold_possible_beside_the_other_colour() -> None:
    expected = DogColorInference.expected_colors(
        ParentColorFacts(CoatColor.NOIR_ET_FEU), ParentColorFacts(CoatColor.GOLD)
    )

    assert [(color.color, color.confidence) for color in expected] == [
        (CoatColor.GOLD, ColorConfidence.AMBIGUOUS),
        (CoatColor.NOIR_ET_FEU, ColorConfidence.AMBIGUOUS),
    ]
    assert expected[0].reason == "Gold possible : un parent gold, l’autre noir et feu"


def test_a_carrier_parent_is_said_so() -> None:
    expected = DogColorInference.expected_colors(
        ParentColorFacts(CoatColor.GOLD), ParentColorFacts(CoatColor.NOIR, e_locus="E/e")
    )

    assert expected[0].reason == "Gold possible : un parent gold, l’autre noir porteur du gold"


def test_a_parent_that_does_not_carry_the_gold_rules_it_out() -> None:
    expected = DogColorInference.expected_colors(
        ParentColorFacts(CoatColor.GOLD), ParentColorFacts(CoatColor.NOIR, e_locus="E/E")
    )

    assert [(color.color, color.confidence) for color in expected] == [(CoatColor.NOIR, ColorConfidence.AMBIGUOUS)]


def test_nothing_is_said_without_both_parents_or_without_a_gold_one() -> None:
    assert DogColorInference.expected_colors(ParentColorFacts(CoatColor.GOLD), None) == ()
    assert DogColorInference.expected_colors(ParentColorFacts(CoatColor.NOIR), ParentColorFacts(CoatColor.MARRON)) == ()
