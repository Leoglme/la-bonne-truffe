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

# LOF Select writes the colour in abbreviations (« F.Or. »), which breeders copy without their dots (« F.OR »).
COLOR_WORD_PATTERN = re.compile(r"[a-z]+")
HIP_SCORE_PATTERN = re.compile(r"\bhd-?[a-e]\b")
GOLD_BASE_WORDS: frozenset[str] = frozenset({"f", "fau", "rou", "gol", "or", "ora", "cit"})
GOLD_COAT_COLORS: frozenset[CoatColor] = frozenset({CoatColor.GOLD, CoatColor.ORANGE_ROUAN})
GOLD_WITH_WHITE_WORDS: tuple[str, ...] = ("orange", "citron", "fauve", "rouge", "gold", "dore")
BROWN_COAT_COLORS: frozenset[CoatColor] = frozenset({CoatColor.MARRON, CoatColor.MARRON_ET_FEU, CoatColor.MARRON_ROUAN})
BROWN_WITH_WHITE_WORDS: tuple[str, ...] = ("marron", "chocolat", "choco", "foie", "liver", "brown")

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
BLACK_WORDS: frozenset[str] = frozenset({"noi"})
BROWN_WORDS: frozenset[str] = frozenset({"mar", "cho", "foi"})
TAN_WORDS: frozenset[str] = frozenset({"fau", "feu"})
ROAN_WORDS: frozenset[str] = frozenset({"rou", "roa", "gri"})
WHITE_WORDS: frozenset[str] = frozenset({"bla", "pan"})
BLUE_WORDS: frozenset[str] = frozenset({"ble", "blu"})
TRICOLOUR_WORDS: frozenset[str] = frozenset({"tri"})
SABLE_WORDS: frozenset[str] = frozenset({"zib", "sab"})
SHADE_WORDS: frozenset[str] = frozenset({"cl", "fo", "mou"})
LOF_SELECT_WORDS: frozenset[str] = (
    GOLD_BASE_WORDS
    | BLACK_WORDS
    | BROWN_WORDS
    | TAN_WORDS
    | ROAN_WORDS
    | WHITE_WORDS
    | BLUE_WORDS
    | TRICOLOUR_WORDS
    | SABLE_WORDS
    | SHADE_WORDS
)

WHITE_CHEST_MARK_PATTERN = re.compile(r"\b(?:cravate|plastron|tache|liste)s? blanc(?:he)?s?\b")

# The colour words of the sites that write it in full (« Noire et blanche », « Golden », « Noir et feu »).
PLAIN_TEXT_COLORS: tuple[tuple[tuple[str, ...], CoatColor], ...] = (
    (("bleu", "blue", "grisonne"), CoatColor.BLEU_ROUAN),
    (("orange rouan", "orange roan", "rouan orange"), CoatColor.ORANGE_ROUAN),
    (("marron rouan", "chocolat rouan", "foie rouan", "liver roan"), CoatColor.MARRON_ROUAN),
    (("tricolore", "tricolor"), CoatColor.TRICOLORE),
    (("zibeline", "sable"), CoatColor.ZIBELINE),
    (("noir et feu", "noire et feu", "noir feu", "noire feu", "noir marque", "noire marquee"), CoatColor.NOIR_ET_FEU),
    (("black and tan", "black & tan"), CoatColor.NOIR_ET_FEU),
    (
        ("marron et feu", "chocolat et feu", "choco et feu", "marron feu", "chocolat feu", "choco feu", "foie et feu"),
        CoatColor.MARRON_ET_FEU,
    ),
    (("marron marque", "marron marquee", "chocolat marque", "chocolat marquee"), CoatColor.MARRON_ET_FEU),
    (("liver and tan",), CoatColor.MARRON_ET_FEU),
    (("et blanc", "blanche", "blanc", "particolore", "bicolore", "panache"), CoatColor.PARTICOLORE),
    (("golden", "gold", "dore", "doree", "rouge", "roux", "fauve", "orange", "red"), CoatColor.GOLD),
    (("noir", "noire", "black"), CoatColor.NOIR),
    (("marron", "chocolat", "foie", "liver", "brown"), CoatColor.MARRON),
)

# The most specific colour first: « noirs feu » must be read before « noirs ».
SENTENCE_COLOR_PATTERNS: tuple[tuple[re.Pattern[str], CoatColor], ...] = (
    (re.compile(r"\b(?:bleue?s? rouane?s?|blue roans?)\b"), CoatColor.BLEU_ROUAN),
    (re.compile(r"\boranges? (?:rouans?|roans?)\b"), CoatColor.ORANGE_ROUAN),
    (re.compile(r"\b(?:(?:marrons?|chocolats?|foie) rouans?|liver roans?)\b"), CoatColor.MARRON_ROUAN),
    (re.compile(r"\btricolores?\b"), CoatColor.TRICOLORE),
    (re.compile(r"\bzibelines?\b"), CoatColor.ZIBELINE),
    (re.compile(r"\b(?:noire?s?(?: et)? feux?|black (?:and|et) tan)\b"), CoatColor.NOIR_ET_FEU),
    (
        re.compile(r"\b(?:(?:marrons?|chocolats?|chocos?|foie)(?: et)? feux?|liver (?:and|et) tan)\b"),
        CoatColor.MARRON_ET_FEU,
    ),
    (re.compile(r"\b(?:particolores?|(?:noire?s?|marrons?|oranges?) et blanc(?:he)?s?)\b"), CoatColor.PARTICOLORE),
    (re.compile(r"\b(?:golden|golds?|dorees?|dores?|rouges?|fauves?)\b"), CoatColor.GOLD),
    (re.compile(r"\bbleue?s?\b"), CoatColor.BLEU_ROUAN),
    (re.compile(r"\bnoire?s?\b"), CoatColor.NOIR),
    (re.compile(r"\b(?:marrons?|chocolats?)\b"), CoatColor.MARRON),
)
SENTENCE_SEPARATOR_PATTERN = re.compile(r"[^a-z0-9]+")
NOT_THE_COAT_PATTERN = re.compile(r"\b(?:colliers?|yeux|truffes?)(?: de couleur| couleur)? [a-z]+")


@dataclass(frozen=True)
class ParentColorFacts:
    """
    What is known of a parent's colour: its canonical colour, its E locus genotype when tested, whether one of its
    own parents had a coat of the gold family, and whether its own coat is brown, with white or not.
    """

    color: CoatColor
    e_locus: str | None = None
    has_gold_parent: bool = False
    has_brown_coat: bool = False

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
            code: « F.Or. », « Noi. Mar.Fau. », « Noi. Pan.Bla.Gri. », « Noire et blanche », « Golden », « Bleue »…

        Returns:
            The colour, ``inconnue`` when the code is not understood (the raw code is kept apart).
        """
        if not code:
            return CoatColor.INCONNUE
        lowered = without_accents(code).lower().strip()
        lof_select_words = DogColorInference._lof_select_words(lowered)
        if lof_select_words is not None:
            return DogColorInference._color_of_lof_select_words(lof_select_words)
        return DogColorInference._color_of_plain_text(lowered)

    @classmethod
    def has_gold_coat(cls, code: str | None) -> bool:
        """
        Whether a coat belongs to the gold family, which only a dog with two « e » shows: gold, red, orange or
        lemon, roan or with white.

        Args:
            code: The colour as the source writes it (« F.Or. », « Fau. Pan.Bla.Rou. », « Golden », « Blanc et orange »).

        Returns:
            True for a coat of the gold family.
        """
        if not code:
            return False
        lowered = without_accents(code).lower().strip()
        lof_select_words = cls._lof_select_words(lowered)
        if lof_select_words is not None:
            return lof_select_words[0] in GOLD_BASE_WORDS
        color = cls._color_of_plain_text(lowered)
        is_gold_with_white = color == CoatColor.PARTICOLORE and any(word in lowered for word in GOLD_WITH_WHITE_WORDS)
        return color in GOLD_COAT_COLORS or is_gold_with_white

    @classmethod
    def has_brown_coat(cls, code: str | None) -> bool:
        """
        Whether a coat is brown, which only a dog with two « b » shows: marron, marron et feu, marron rouan, or
        marron and white.

        Args:
            code: The colour as the source writes it (« Mar. Pan.Bla. », « Chocolat et feu », « Marron et blanc »).

        Returns:
            True for a brown coat.
        """
        if not code:
            return False
        lowered = without_accents(code).lower().strip()
        lof_select_words = cls._lof_select_words(lowered)
        if lof_select_words is not None:
            return lof_select_words[0] in BROWN_WORDS
        color = cls._color_of_plain_text(lowered)
        is_brown_with_white = color in (CoatColor.PARTICOLORE, CoatColor.TRICOLORE) and any(
            word in lowered for word in BROWN_WITH_WHITE_WORDS
        )
        return color in BROWN_COAT_COLORS or is_brown_with_white

    @staticmethod
    def colors_named_in(sentence: str) -> tuple[CoatColor, ...]:
        """
        The colours a sentence names, each read once and never twice from the same words: « noirs feu » is black
        and tan, not black; and the colour of a collar, of the eyes or of the nose is left out.

        Args:
            sentence: A title or a text written by a breeder (« Chiots LOF noirs feu disponibles à la réservation »).

        Returns:
            The colours, in the order the sentence names them; empty when it names none.
        """
        words = SENTENCE_SEPARATOR_PATTERN.sub(" ", without_accents(sentence).lower().replace("&", " et ")).strip()
        words = NOT_THE_COAT_PATTERN.sub(lambda other_match: " " * len(other_match.group()), words)
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
        puppies, a gold parent and a carrier one gold puppy in two, two carriers one in four, and a parent tested
        ``E/E`` none. Two brown parents give no black puppy.

        Args:
            sire: What is known of the father, None while his page is not read.
            dam: What is known of the mother, None while her page is not read.

        Returns:
            The expected colours, empty when nothing can be said.
        """
        if sire is None or dam is None:
            return ()
        if sire.color in WHITE_MARKED_COLORS and dam.color in WHITE_MARKED_COLORS:
            return cls._colors_of_two_parents_with_white(sire, dam)
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
            return cls._colors_without_gold_parent(sire, dam)
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
    def _colors_without_gold_parent(sire: ParentColorFacts, dam: ParentColorFacts) -> tuple[ExpectedColor, ...]:
        """
        The colours of two parents neither of which is gold, when what is known of them excludes a colour: a parent
        tested ``E/E`` gives every puppy an « E », so no puppy is gold; two brown parents give every puppy two « b »,
        so no puppy is black.

        Args:
            sire: The father.
            dam: The mother.

        Returns:
            The colours of the parents, each once, with the reason; empty when nothing is excluded.
        """
        parent_colors = [color for color in dict.fromkeys((sire.color, dam.color)) if color != CoatColor.INCONNUE]
        if not parent_colors:
            return ()
        if sire.genotype == NON_CARRIER_GENOTYPE:
            reason = "Pas de gold : le père, testé E/E, ne transmet pas le gold"
        elif dam.genotype == NON_CARRIER_GENOTYPE:
            reason = "Pas de gold : la mère, testée E/E, ne transmet pas le gold"
        elif sire.has_brown_coat and dam.has_brown_coat:
            reason = "Pas de noir : les deux parents sont marron, leurs chiots le seront aussi"
        else:
            return ()
        return tuple(ExpectedColor(color, ColorConfidence.AMBIGUOUS, reason) for color in parent_colors)

    @staticmethod
    def _colors_of_two_parents_with_white(sire: ParentColorFacts, dam: ParentColorFacts) -> tuple[ExpectedColor, ...]:
        """
        The colours of two parents that both have white in their coat: their puppies have white too.

        Args:
            sire: The father.
            dam: The mother.

        Returns:
            The colours of the parents, each once.
        """
        reason = "Pas de gold uni : les deux parents ont du blanc dans leur robe, leurs chiots en auront aussi"
        return tuple(
            ExpectedColor(parent_color, ColorConfidence.AMBIGUOUS, reason)
            for parent_color in dict.fromkeys((sire.color, dam.color))
        )

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
    def _lof_select_words(code: str) -> list[str] | None:
        """
        The abbreviations of a colour written the LOF Select way, with or without their dots.

        Args:
            code: Lower-case text without accents (« noi. pan.bla.gri. », « f.or », « noi pan bla », « f. cl. hd-a »).

        Returns:
            Its words without the hip score (« noi », « pan », « bla », « gri »), or None for a colour written in
            full (« noire et blanche »).
        """
        words = COLOR_WORD_PATTERN.findall(HIP_SCORE_PATTERN.sub(" ", code))
        if words and all(word in LOF_SELECT_WORDS for word in words):
            return words
        return None

    @staticmethod
    def _color_of_lof_select_words(words: list[str]) -> CoatColor:
        """
        Read the abbreviations of LOF Select: the first word is the base colour, the others its marks. « Gri. »
        (grisonné) is the roan of a black coat: « Noi. Pan.Bla.Gri. » is what breeders call a blue roan.

        Args:
            words: The abbreviations, without dots (« noi », « mar », « fau » for « Noi. Mar.Fau. »).

        Returns:
            The canonical colour.
        """
        first, marks = words[0], set(words[1:])
        if first in BLUE_WORDS:
            return CoatColor.BLEU_ROUAN
        if first in TRICOLOUR_WORDS:
            return CoatColor.TRICOLORE
        if first in SABLE_WORDS:
            return CoatColor.ZIBELINE
        if first in BLACK_WORDS:
            if marks & TAN_WORDS:
                return CoatColor.TRICOLORE if marks & WHITE_WORDS else CoatColor.NOIR_ET_FEU
            if marks & ROAN_WORDS:
                return CoatColor.BLEU_ROUAN
            if marks & WHITE_WORDS:
                return CoatColor.PARTICOLORE
            return CoatColor.NOIR
        if first in BROWN_WORDS:
            if marks & TAN_WORDS:
                return CoatColor.TRICOLORE if marks & WHITE_WORDS else CoatColor.MARRON_ET_FEU
            if marks & ROAN_WORDS:
                return CoatColor.MARRON_ROUAN
            if marks & WHITE_WORDS:
                return CoatColor.PARTICOLORE
            return CoatColor.MARRON
        if first in GOLD_BASE_WORDS:
            if marks & ROAN_WORDS:
                return CoatColor.ORANGE_ROUAN
            if marks & WHITE_WORDS:
                return CoatColor.PARTICOLORE
            return CoatColor.GOLD
        return CoatColor.INCONNUE

    @staticmethod
    def _color_of_plain_text(text: str) -> CoatColor:
        """
        Read a colour written in full, the most specific phrase first. A white mark on the chest is left out:
        « Noire cravate blanche » is a black dog.

        Args:
            text: Lower-case text without accents.

        Returns:
            The canonical colour, ``inconnue`` when no word is known.
        """
        coat_text = WHITE_CHEST_MARK_PATTERN.sub(" ", text)
        for phrases, color in PLAIN_TEXT_COLORS:
            if any(phrase in coat_text for phrase in phrases):
                return color
        return CoatColor.INCONNUE
