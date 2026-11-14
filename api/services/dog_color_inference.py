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

E_LOCUS_CODE_PATTERN = re.compile(r"^LocE\w*-(.+)$")
RECESSIVE_E_ALLELE = "e"
GOLD_GENOTYPE = "e/e"
CARRIER_GENOTYPE = "E/e"
NON_CARRIER_GENOTYPE = "E/E"
GOLD_PUPPY_ODDS_OF_GOLD_COUPLE = 1.0
GOLD_PUPPY_ODDS_WITH_ONE_CARRIER = 0.5
GOLD_PUPPY_ODDS_OF_TWO_CARRIERS = 0.25

# LOF Select writes the colour in abbreviations (« F.Or. », « Noi. Mar.Fau. »): each token is one word.
LOF_SELECT_TOKEN_PATTERN = re.compile(r"[a-z]+\.?")
GOLD_TOKENS: frozenset[str] = frozenset(
    {"f.", "f.or.", "f.cl.", "f.fo.", "fau.", "rou.", "gol.", "or.", "ora.", "cit."}
)
GOLD_COAT_COLORS: frozenset[CoatColor] = frozenset({CoatColor.GOLD, CoatColor.ORANGE_ROUAN})

# The coats with white. The solid coat is dominant: two parents with white only give puppies with white.
WHITE_MARKED_COLORS: frozenset[CoatColor] = frozenset(
    {
        CoatColor.BLEU_ROUAN,
        CoatColor.ORANGE_ROUAN,
        CoatColor.MARRON_ROUAN,
        CoatColor.TRICOLORE,
        CoatColor.PARTICOLORE,
    }
)
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

# The most specific colour first: « noirs feu » must be read before « noirs ».
SENTENCE_COLOR_PATTERNS: tuple[tuple[re.Pattern[str], CoatColor], ...] = (
    (re.compile(r"\b(?:bleus? rouans?|blue roans?)\b"), CoatColor.BLEU_ROUAN),
    (re.compile(r"\boranges? (?:rouans?|roans?)\b"), CoatColor.ORANGE_ROUAN),
    (re.compile(r"\b(?:(?:marrons?|chocolats?|foie) rouans?|liver roans?)\b"), CoatColor.MARRON_ROUAN),
    (re.compile(r"\btricolores?\b"), CoatColor.TRICOLORE),
    (re.compile(r"\bzibelines?\b"), CoatColor.ZIBELINE),
    (re.compile(r"\b(?:noire?s?(?: et)? feux?|black (?:and|et) tan)\b"), CoatColor.NOIR_ET_FEU),
    (re.compile(r"\b(?:(?:marrons?|chocolats?|foie)(?: et)? feux?|liver (?:and|et) tan)\b"), CoatColor.MARRON_ET_FEU),
    (re.compile(r"\b(?:particolores?|(?:noire?s?|marrons?|oranges?) et blanc(?:he)?s?)\b"), CoatColor.PARTICOLORE),
    (re.compile(r"\b(?:golden|golds?|dorees?|dores?|rouges?|fauves?)\b"), CoatColor.GOLD),
    (re.compile(r"\bnoire?s?\b"), CoatColor.NOIR),
    (re.compile(r"\b(?:marrons?|chocolats?)\b"), CoatColor.MARRON),
)
SENTENCE_SEPARATOR_PATTERN = re.compile(r"[^a-z0-9]+")


@dataclass(frozen=True)
class ParentColorFacts:
    """
    What is known of a parent's colour: its canonical colour, its E locus genotype when tested, and whether one
    of its own parents had a coat of the gold family.
    """

    color: CoatColor
    e_locus: str | None = None
    has_gold_parent: bool = False

    @property
    def genotype(self) -> str | None:
        """
        The E locus genotype: the tested one, else ``e/e`` for a gold dog (gold is recessive), else ``E/e`` for a
        dog one of whose parents had two « e » and gave it one, else unknown.

        Returns:
            « e/e », « E/e », « E/E », or None while unknown.
        """
        if self.e_locus is not None:
            return self.e_locus
        if self.color == CoatColor.GOLD:
            return GOLD_GENOTYPE
        return CARRIER_GENOTYPE if self.has_gold_parent else None

    @property
    def carries_gold_by_parents(self) -> bool:
        """
        Whether the dog carries the gold because one of its parents had a coat of the gold family, without a test.

        Returns:
            True when the carrier genotype comes from its parents.
        """
        return self.e_locus is None and self.color != CoatColor.GOLD and self.has_gold_parent


@dataclass(frozen=True)
class ExpectedColor:
    """One colour the parents imply for the puppies, how sure it is, why, and the share of puppies of that colour."""

    color: CoatColor
    confidence: ColorConfidence
    reason: str
    puppy_odds: float | None = None

    def as_json(self) -> dict[str, str | float]:
        """
        The form stored in ``LitterGroup.expected_colors``.

        Returns:
            The colour, its confidence and its reason, and the odds of each puppy when the genotypes tell them.
        """
        stored: dict[str, str | float] = {
            "color": self.color.value,
            "confidence": self.confidence.value,
            "reason": self.reason,
        }
        if self.puppy_odds is not None:
            stored["puppy_odds"] = self.puppy_odds
        return stored


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

    @classmethod
    def has_gold_coat(cls, code: str | None) -> bool:
        """
        Whether a coat belongs to the gold family, which only a dog with two « e » shows: gold, red, orange or
        lemon, roan or with white.

        Args:
            code: The colour as the source writes it (« F.Or. », « Fau. Pan.Bla.Rou. », « Golden »).

        Returns:
            True for a coat of the gold family.
        """
        if not code:
            return False
        lowered = without_accents(code).lower().strip()
        tokens = LOF_SELECT_TOKEN_PATTERN.findall(lowered)
        if tokens and all(token.endswith(".") or token in TAN_TOKENS for token in tokens):
            return tokens[0] in GOLD_TOKENS or tokens[0].startswith("f.")
        return cls._color_of_plain_text(lowered) in GOLD_COAT_COLORS

    @staticmethod
    def colors_named_in(sentence: str) -> tuple[CoatColor, ...]:
        """
        The colours a sentence names, each read once and never twice from the same words: « noirs feu » is black
        and tan, not black.

        Args:
            sentence: A title or a text written by a breeder (« Chiots LOF noirs feu disponibles à la réservation »).

        Returns:
            The colours, in the order the sentence names them; empty when it names none.
        """
        words = SENTENCE_SEPARATOR_PATTERN.sub(" ", without_accents(sentence).lower().replace("&", " et ")).strip()
        place_by_color: dict[CoatColor, int] = {}
        for pattern, color in SENTENCE_COLOR_PATTERNS:
            for color_match in pattern.finditer(words):
                place_by_color.setdefault(color, color_match.start())
            words = pattern.sub(lambda color_match: " " * len(color_match.group()), words)
        return tuple(sorted(place_by_color, key=lambda color: place_by_color[color]))

    @staticmethod
    def e_locus_of(health_codes: tuple[str, ...] | list[str]) -> str | None:
        """
        The E locus genotype among the health test codes, written with « E » for any dominant allele: the mask
        « Em » of « LocEm-Em/e » is one.

        Args:
            health_codes: Codes as LOF Select lists them (« FN-1.1 », « LocE-e/e », « LocEm-Em/e »).

        Returns:
            « e/e », « E/e » or « E/E », or None when the locus is not tested.
        """
        for code in health_codes:
            code_match = E_LOCUS_CODE_PATTERN.match(code.strip())
            if code_match is None:
                continue
            alleles = [allele.strip() for allele in code_match.group(1).split("/")]
            if len(alleles) != 2 or not all(alleles):
                return None
            dominant_first = sorted(
                RECESSIVE_E_ALLELE if allele.startswith(RECESSIVE_E_ALLELE) else "E" for allele in alleles
            )
            return "/".join(dominant_first)
        return None

    @classmethod
    def expected_colors(cls, sire: ParentColorFacts | None, dam: ParentColorFacts | None) -> tuple[ExpectedColor, ...]:
        """
        The colours a couple of parents implies. Two parents with white in their coat only give puppies with white,
        never a solid gold, whatever their E locus. Else the E locus tells: two ``e/e`` parents only give gold
        puppies, a gold parent and a carrier one gold puppy in two, two carriers one in four.

        Args:
            sire: What is known of the father, None while his page is not read.
            dam: What is known of the mother, None while her page is not read.

        Returns:
            The expected colours, empty when nothing can be said.
        """
        if sire is None or dam is None:
            return ()
        if sire.color in WHITE_MARKED_COLORS and dam.color in WHITE_MARKED_COLORS:
            reason = "Pas de gold uni : les deux parents ont du blanc dans leur robe, leurs chiots en auront aussi"
            return tuple(
                ExpectedColor(parent_color, ColorConfidence.AMBIGUOUS, reason)
                for parent_color in dict.fromkeys((sire.color, dam.color))
            )
        sire_genotype, dam_genotype = sire.genotype, dam.genotype
        if sire_genotype == GOLD_GENOTYPE and dam_genotype == GOLD_GENOTYPE:
            return (
                ExpectedColor(
                    CoatColor.GOLD,
                    ColorConfidence.INFERRED,
                    "Gold : les deux parents sont gold",
                    GOLD_PUPPY_ODDS_OF_GOLD_COUPLE,
                ),
            )
        if sire_genotype == CARRIER_GENOTYPE and dam_genotype == CARRIER_GENOTYPE:
            return cls._colors_of_two_carriers(sire, dam)
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
        if other_genotype == CARRIER_GENOTYPE:
            reason = f"Gold possible, un chiot sur deux : un parent gold, l’autre {other_label} porteur du gold"
            gold_odds: float | None = GOLD_PUPPY_ODDS_WITH_ONE_CARRIER
        else:
            reason = f"Gold possible : un parent gold, l’autre {other_label}"
            gold_odds = None
        expected = [ExpectedColor(CoatColor.GOLD, ColorConfidence.AMBIGUOUS, reason, gold_odds)]
        if other_parent.color not in (CoatColor.INCONNUE, CoatColor.GOLD):
            expected.append(ExpectedColor(other_parent.color, ColorConfidence.AMBIGUOUS, reason))
        return tuple(expected)

    @staticmethod
    def _colors_of_two_carriers(sire: ParentColorFacts, dam: ParentColorFacts) -> tuple[ExpectedColor, ...]:
        """
        The colours of two parents that both carry the gold without being gold: gold for one puppy in four, their
        own colours for the others.

        Args:
            sire: The father.
            dam: The mother.

        Returns:
            Gold first, then the colours of the parents, each once.
        """
        reason = "Gold possible, un chiot sur quatre : les deux parents portent le gold"
        expected = [ExpectedColor(CoatColor.GOLD, ColorConfidence.AMBIGUOUS, reason, GOLD_PUPPY_ODDS_OF_TWO_CARRIERS)]
        for parent_color in dict.fromkeys((sire.color, dam.color)):
            if parent_color not in (CoatColor.INCONNUE, CoatColor.GOLD):
                expected.append(ExpectedColor(parent_color, ColorConfidence.AMBIGUOUS, reason))
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
                return CoatColor.TRICOLORE if marks & WHITE_TOKENS else CoatColor.NOIR_ET_FEU
            if marks & ROAN_TOKENS:
                return CoatColor.BLEU_ROUAN
            if marks & WHITE_TOKENS:
                return CoatColor.PARTICOLORE
            return CoatColor.NOIR
        if first in BROWN_TOKENS:
            if marks & TAN_TOKENS:
                return CoatColor.TRICOLORE if marks & WHITE_TOKENS else CoatColor.MARRON_ET_FEU
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
