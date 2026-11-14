"""The colour codes of the sources, and what a couple of parents implies for their puppies."""

import pytest

from enums.coat_color import CoatColor
from enums.color_confidence import ColorConfidence
from services.dog_color_inference import DogColorInference, ParentColorFacts
from services.dog_name import DogName


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
        ("Noi. Pan.Bla.Gri.", CoatColor.BLEU_ROUAN),
        ("Noi. Pan.Bla.Mou.", CoatColor.PARTICOLORE),
        ("F.OR", CoatColor.GOLD),
        ("F. Cl. HD-A", CoatColor.GOLD),
        ("Noi pan bla", CoatColor.PARTICOLORE),
        ("Noi.Mar.Fau", CoatColor.NOIR_ET_FEU),
        ("Bleue", CoatColor.BLEU_ROUAN),
        ("Noir panaché blanc grisonné", CoatColor.BLEU_ROUAN),
        ("Noir marqué fauve", CoatColor.NOIR_ET_FEU),
        ("Choco et feu", CoatColor.MARRON_ET_FEU),
        ("Noire cravate blanche", CoatColor.NOIR),
        ("", CoatColor.INCONNUE),
        (None, CoatColor.INCONNUE),
        ("Xyz.", CoatColor.INCONNUE),
    ],
)
def test_a_colour_code_becomes_a_canonical_colour(code: str | None, color: CoatColor) -> None:
    assert DogColorInference.canonical_color(code) == color


@pytest.mark.parametrize(
    ("sentence", "colors"),
    [
        ("Chiots LOF Noirs feu disponibles à la réservation", (CoatColor.NOIR_ET_FEU,)),
        ("Naissance de nos bébés : 2 mâles noir & feu et 3 femelles dorées", (CoatColor.NOIR_ET_FEU, CoatColor.GOLD)),
        ("Chiots golden et chiots noirs disponibles", (CoatColor.GOLD, CoatColor.NOIR)),
        ("Une portée de bleus rouans et de tricolores", (CoatColor.BLEU_ROUAN, CoatColor.TRICOLORE)),
        ("Chiots chocolat et feu, chiots noire et blanche", (CoatColor.MARRON_ET_FEU, CoatColor.PARTICOLORE)),
        ("Deux bleus, une bleue rouane et un choco feu", (CoatColor.BLEU_ROUAN, CoatColor.MARRON_ET_FEU)),
        ("Mâle collier bleu, femelle aux yeux noirs", ()),
        ("Femelle noire et feu collier rose", (CoatColor.NOIR_ET_FEU,)),
        ("Chiots disponibles à la réservation", ()),
        ("", ()),
    ],
)
def test_a_sentence_names_each_of_its_colours_once(sentence: str, colors: tuple[CoatColor, ...]) -> None:
    assert DogColorInference.colors_named_in(sentence) == colors


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
        ("Blanc et orange", True),
        ("F.OR", True),
        ("Noir marqué fauve", False),
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


def test_two_parents_with_white_never_announce_a_solid_gold_even_when_both_carry_it() -> None:
    expected = DogColorInference.expected_colors(
        ParentColorFacts(CoatColor.PARTICOLORE, e_locus="E/e"), ParentColorFacts(CoatColor.TRICOLORE, e_locus="E/e")
    )
    with_a_solid_parent = DogColorInference.expected_colors(
        ParentColorFacts(CoatColor.NOIR, e_locus="E/e"), ParentColorFacts(CoatColor.PARTICOLORE, e_locus="E/e")
    )

    assert [(color.color, color.confidence, color.puppy_odds) for color in expected] == [
        (CoatColor.PARTICOLORE, ColorConfidence.AMBIGUOUS, None),
        (CoatColor.TRICOLORE, ColorConfidence.AMBIGUOUS, None),
    ]
    assert with_a_solid_parent[0].color == CoatColor.GOLD
    assert DogColorInference.gold_exclusion_of([color.as_json() for color in expected]) == (
        "Le père et la mère portent le gold, mais tous deux ont du blanc dans leur robe : un chiot sur quatre peut "
        "naître orange avec du blanc, aucun ne sera gold uni."
    )


def test_the_gold_card_tells_why_no_puppy_will_be_gold() -> None:
    def exclusion(sire: ParentColorFacts, dam: ParentColorFacts) -> str | None:
        return DogColorInference.gold_exclusion_of(
            [color.as_json() for color in DogColorInference.expected_colors(sire, dam)]
        )

    assert exclusion(ParentColorFacts(CoatColor.BLEU_ROUAN), ParentColorFacts(CoatColor.PARTICOLORE)) == (
        "Les deux parents ont du blanc dans leur robe, leurs chiots en auront aussi, aucun ne sera gold uni."
    )
    assert exclusion(ParentColorFacts(CoatColor.GOLD), ParentColorFacts(CoatColor.NOIR, e_locus="E/E")) == (
        "Un parent est gold, mais l’autre, noir, testé E/E, ne transmet pas le gold : aucun chiot ne sera gold."
    )
    assert exclusion(ParentColorFacts(CoatColor.NOIR, e_locus="E/E"), ParentColorFacts(CoatColor.NOIR_ET_FEU)) == (
        "Le père, testé E/E, ne transmet pas le gold : aucun chiot ne sera gold."
    )
    assert exclusion(ParentColorFacts(CoatColor.GOLD), ParentColorFacts(CoatColor.NOIR, e_locus="E/e")) is None


def test_a_parent_tested_e_e_rules_out_the_gold_even_without_a_gold_parent() -> None:
    expected = DogColorInference.expected_colors(
        ParentColorFacts(CoatColor.NOIR_ET_FEU, e_locus="E/e"), ParentColorFacts(CoatColor.NOIR, e_locus="E/E")
    )

    assert [(color.color, color.confidence) for color in expected] == [
        (CoatColor.NOIR_ET_FEU, ColorConfidence.AMBIGUOUS),
        (CoatColor.NOIR, ColorConfidence.AMBIGUOUS),
    ]
    assert expected[0].reason == "Pas de gold : la mère, testée E/E, ne transmet pas le gold"


def test_two_brown_parents_rule_out_the_black_puppies() -> None:
    brown_and_white = ParentColorFacts(
        DogColorInference.canonical_color("Mar. Pan.Bla."),
        has_brown_coat=DogColorInference.has_brown_coat("Mar. Pan.Bla."),
    )
    brown_and_tan = ParentColorFacts(CoatColor.MARRON_ET_FEU, has_brown_coat=True)
    black_and_tan = ParentColorFacts(CoatColor.NOIR_ET_FEU)

    expected = DogColorInference.expected_colors(brown_and_white, brown_and_tan)

    assert [color.color for color in expected] == [CoatColor.PARTICOLORE, CoatColor.MARRON_ET_FEU]
    assert expected[0].reason == "Pas de noir : les deux parents sont marron, leurs chiots le seront aussi"
    assert DogColorInference.expected_colors(black_and_tan, brown_and_tan) == ()


@pytest.mark.parametrize(
    ("code", "has_brown_coat"),
    [
        ("Mar. Pan.Bla.", True),
        ("Mar. Mar.Fau.", True),
        ("Chocolat et feu", True),
        ("Marron et blanc", True),
        ("Noi. Mar.Fau.", False),
        ("F.Or.", False),
        (None, False),
    ],
)
def test_the_brown_coats_are_told_apart(code: str | None, has_brown_coat: bool) -> None:
    assert DogColorInference.has_brown_coat(code) is has_brown_coat


def test_a_dog_name_is_compared_without_case_accents_punctuation_nor_the_missing_affix() -> None:
    assert DogName.key_of("Viggo Du Clos De L'Écotay") == DogName.key_of("Viggo du Clos de l'Ecotay")
    assert DogName.key_of("Valko (Sans Affixe)") == "valko"
    assert DogName.key_of(None) == ""
