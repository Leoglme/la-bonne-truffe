"""
The colours a dog's page gives, and the colours a couple of parents implies for their puppies (docs/03,
« Les couleurs, complément », and docs/04, « Les couleurs données par les chiens »).

Pure functions, no database: the collectors and the snapshot builder call them.
"""

import re
from dataclasses import dataclass

from core.text import without_accents
from enums.coat_color import CoatColor
from enums.color_confidence import ColorConfidence
from services.matching.scoring import COLOR_LABELS

E_LOCUS_CODE_PREFIX = "LocE-"
GOLD_GENOTYPE = "e/e"
CARRIER_GENOTYPE = "E/e"
NON_CARRIER_GENOTYPE = "E/E"

# LOF Select writes the colour in abbreviations (« F.Or. », « Noi. Mar.Fau. »): each token is one word.
LOF_SELECT_TOKEN_PATTERN = re.compile(r"[a-z]+\.?")
GOLD_TOKENS: frozenset[str] = frozenset({"f.", "f.or.", "f.cl.", "f.fo.", "fau.", "rou.", "gol.", "or.", "ora."})
BLACK_TOKENS: frozenset[str] = frozenset({"noi."})
BROWN_TOKENS: frozenset[str] = frozenset({"mar.", "cho.", "foi."})
TAN_TOKENS: frozenset[str] = frozenset({"fau.", "feu", "feu."})
ROAN_TOKENS: frozenset[str] = frozenset({"rou.", "roa."})
WHITE_TOKENS: frozenset[str] = frozenset({"bla.", "pan."})
BLUE_TOKENS: frozenset[str] = frozenset({"ble.", "blu."})
TRICOLOUR_TOKENS: frozenset[str] = frozenset({"tri."})
SABLE_TOKENS: frozenset[str] = frozenset({"zib.", "sab."})

# The colour words of the sites that write it in full (« Noire et blanche », « Golden », « Noir et feu »).
PLAIN_TEXT_COLORS: tuple[tuple[tuple[str, ...], CoatColor], ...] = (
    (("bleu rouan", "blue roan", "bleu roan"), CoatColor.BLEU_ROUAN),
    (("orange rouan", "orange roan", "rouan orange"), CoatColor.ORANGE_ROUAN),
    (("marron rouan", "chocolat rouan", "foie rouan", "liver roan"), CoatColor.MARRON_ROUAN),
    (("tricolore", "tricolor"), CoatColor.TRICOLORE),
    (("zibeline", "sable"), CoatColor.ZIBELINE),
    (("noir et feu", "noire et feu", "black and tan", "black & tan"), CoatColor.NOIR_ET_FEU),
    (("marron et feu", "chocolat et feu", "foie et feu", "liver and tan"), CoatColor.MARRON_ET_FEU),
    (("et blanc", "blanche", "blanc", "particolore", "bicolore", "panache"), CoatColor.PARTICOLORE),
    (("golden", "gold", "dore", "doree", "rouge", "roux", "fauve", "orange", "red"), CoatColor.GOLD),
    (("noir", "noire", "black"), CoatColor.NOIR),
    (("marron", "chocolat", "foie", "liver", "brown"), CoatColor.MARRON),
)


@dataclass(frozen=True)
class ParentColorFacts:
    """What is known of a parent's colour: its canonical colour, and its E locus genotype when tested."""

    color: CoatColor
    e_locus: str | None = None

    @property
    def genotype(self) -> str | None:
        """
        The E locus genotype: the tested one, else ``e/e`` for a gold dog (gold is recessive), else unknown.

        Returns:
            « e/e », « E/e », « E/E », or None while unknown.
        """
        if self.e_locus is not None:
            return self.e_locus
        return GOLD_GENOTYPE if self.color == CoatColor.GOLD else None


@dataclass(frozen=True)
class ExpectedColor:
    """One colour the parents imply for the puppies, how sure it is, and why."""

    color: CoatColor
    confidence: ColorConfidence
    reason: str

    def as_json(self) -> dict[str, str]:
        """
        The form stored in ``LitterGroup.expected_colors``.

        Returns:
            The colour, its confidence and its reason, as the litter group keeps them.
        """
        return {"color": self.color.value, "confidence": self.confidence.value, "reason": self.reason}


class DogColorInference:
    """Reads the colour codes of the sources and applies the genetics of the E locus to a couple of parents."""

    @staticmethod
    def canonical_color(code: str | None) -> CoatColor:
        """
        The canonical colour of a LOF Select code or of a colour written in full.

        Args:
            code: « F.Or. », « Noi. Mar.Fau. », « Noi. Pan.Bla. », « Noire et blanche », « Golden »…

        Returns:
            The colour, ``inconnue`` when the code is not understood (the raw code is kept apart).
        """
        if not code:
            return CoatColor.INCONNUE
        lowered = without_accents(code).lower().strip()
        tokens = LOF_SELECT_TOKEN_PATTERN.findall(lowered)
        if tokens and all(token.endswith(".") or token in TAN_TOKENS for token in tokens):
            return DogColorInference._color_of_lof_select_tokens(tokens)
        return DogColorInference._color_of_plain_text(lowered)

    @staticmethod
    def e_locus_of(health_codes: tuple[str, ...] | list[str]) -> str | None:
        """
        The E locus genotype among the health test codes.

        Args:
            health_codes: Codes as LOF Select lists them (« FN-1.1 », « LocE-e/e »).

        Returns:
            « e/e », « E/e » or « E/E », or None when the locus is not tested.
        """
        for code in health_codes:
            if code.startswith(E_LOCUS_CODE_PREFIX):
                genotype = code.removeprefix(E_LOCUS_CODE_PREFIX).strip()
                return genotype or None
        return None

    @classmethod
    def expected_colors(cls, sire: ParentColorFacts | None, dam: ParentColorFacts | None) -> tuple[ExpectedColor, ...]:
        """
        The colours a couple of parents implies, by the E locus: two ``e/e`` parents only give gold puppies.

        Args:
            sire: What is known of the father, None while his page is not read.
            dam: What is known of the mother, None while her page is not read.

        Returns:
            The expected colours, empty when nothing can be said.
        """
        if sire is None or dam is None:
            return ()
        sire_genotype, dam_genotype = sire.genotype, dam.genotype
        if sire_genotype == GOLD_GENOTYPE and dam_genotype == GOLD_GENOTYPE:
            return (ExpectedColor(CoatColor.GOLD, ColorConfidence.INFERRED, "Gold : les deux parents sont gold"),)
        gold_parent, other_parent, other_genotype = cls._gold_parent_and_other(sire, dam, sire_genotype, dam_genotype)
        if gold_parent is None or other_parent is None:
            return ()
        other_label = COLOR_LABELS[other_parent.color]
        if other_genotype == NON_CARRIER_GENOTYPE:
            if other_parent.color == CoatColor.INCONNUE:
                return ()
            return (
                ExpectedColor(
                    other_parent.color,
                    ColorConfidence.AMBIGUOUS,
                    f"Pas de gold : l’autre parent, {other_label}, ne transmet pas le gold",
                ),
            )
        reason = f"Gold possible : un parent gold, l’autre {other_label}" + (
            " porteur du gold" if other_genotype == CARRIER_GENOTYPE else ""
        )
        expected = [ExpectedColor(CoatColor.GOLD, ColorConfidence.AMBIGUOUS, reason)]
        if other_parent.color not in (CoatColor.INCONNUE, CoatColor.GOLD):
            expected.append(ExpectedColor(other_parent.color, ColorConfidence.AMBIGUOUS, reason))
        return tuple(expected)

    @staticmethod
    def _gold_parent_and_other(
        sire: ParentColorFacts, dam: ParentColorFacts, sire_genotype: str | None, dam_genotype: str | None
    ) -> tuple[ParentColorFacts | None, ParentColorFacts | None, str | None]:
        """
        Tell the gold parent from the other one, when exactly one is gold.

        Args:
            sire: The father.
            dam: The mother.
            sire_genotype: His genotype, when known.
            dam_genotype: Her genotype, when known.

        Returns:
            The gold parent, the other one and the other one's genotype; Nones when no parent is gold.
        """
        if sire_genotype == GOLD_GENOTYPE:
            return sire, dam, dam_genotype
        if dam_genotype == GOLD_GENOTYPE:
            return dam, sire, sire_genotype
        return None, None, None

    @staticmethod
    def _color_of_lof_select_tokens(tokens: list[str]) -> CoatColor:
        """
        Read the abbreviations of LOF Select: the first word is the base colour, the others its marks.

        Args:
            tokens: Lower-case words without accents (« noi. », « mar.fau. » split in « mar. » and « fau. »).

        Returns:
            The canonical colour.
        """
        first, marks = tokens[0], set(tokens[1:])
        if first in BLUE_TOKENS:
            return CoatColor.BLEU_ROUAN
        if first in TRICOLOUR_TOKENS:
            return CoatColor.TRICOLORE
        if first in SABLE_TOKENS:
            return CoatColor.ZIBELINE
        if first in BLACK_TOKENS:
            if marks & TAN_TOKENS:
                return CoatColor.NOIR_ET_FEU
            if marks & ROAN_TOKENS:
                return CoatColor.BLEU_ROUAN
            if marks & WHITE_TOKENS:
                return CoatColor.PARTICOLORE
            return CoatColor.NOIR
        if first in BROWN_TOKENS:
            if marks & TAN_TOKENS:
                return CoatColor.MARRON_ET_FEU
            if marks & ROAN_TOKENS:
                return CoatColor.MARRON_ROUAN
            if marks & WHITE_TOKENS:
                return CoatColor.PARTICOLORE
            return CoatColor.MARRON
        if first in GOLD_TOKENS or first.startswith("f."):
            if marks & ROAN_TOKENS:
                return CoatColor.ORANGE_ROUAN
            if marks & WHITE_TOKENS:
                return CoatColor.PARTICOLORE
            return CoatColor.GOLD
        return CoatColor.INCONNUE

    @staticmethod
    def _color_of_plain_text(text: str) -> CoatColor:
        """
        Read a colour written in full, the most specific phrase first.

        Args:
            text: Lower-case text without accents.

        Returns:
            The canonical colour, ``inconnue`` when no word is known.
        """
        for phrases, color in PLAIN_TEXT_COLORS:
            if any(phrase in text for phrase in phrases):
                return color
        return CoatColor.INCONNUE
