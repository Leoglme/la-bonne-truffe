"""Readers for the breeder details the sources publish: names, towns, phones, SIREN."""

import re
import unicodedata

LOWERCASE_NAME_WORDS: frozenset[str] = frozenset(
    {"de", "du", "des", "la", "le", "les", "et", "en", "sur", "sous", "aux", "au", "à"}
)
ELIDED_ARTICLES: frozenset[str] = frozenset({"l", "d"})
AFFIX_KEY_IGNORED_WORDS: frozenset[str] = frozenset({"de", "du", "des", "la", "le", "les", "l", "d"})
APOSTROPHES: tuple[str, ...] = ("'", "’")
NON_DIGIT_PATTERN = re.compile(r"\D")
NON_LETTER_OR_DIGIT_PATTERN = re.compile(r"[^a-z0-9]+")
FRENCH_NATIONAL_PHONE_LENGTH = 10
FRENCH_COUNTRY_CODE = "33"
SIREN_LENGTH = 9
SIRET_LENGTH = 14
POSTAL_CODE_LENGTH = 5


class BreederContactParser:
    """Turns the raw breeder details of a source into the clean values stored on a ``Breeder``."""

    @classmethod
    def readable_name(cls, text: str | None) -> str | None:
        """
        Write an upper-case name the way a French reader expects it; a name already in mixed case is kept.

        Args:
            text: Name as published (« DU CLOS DE L'ÉCOTAY », « SAINT-AUBIN-DU-CORMIER »).

        Returns:
            « Du Clos de l'Écotay », « Saint-Aubin-du-Cormier », or None when empty.
        """
        cleaned = " ".join((text or "").split())
        if not cleaned:
            return None
        if cleaned != cleaned.upper():
            return cleaned
        words = cleaned.lower().split(" ")
        return " ".join(cls._capitalize_word(word, is_first_word=index == 0) for index, word in enumerate(words))

    @staticmethod
    def affix_key(affix: str | None) -> str | None:
        """
        The form of an affix used to match a breeder across sources: lowercase, no accent, no article.

        Args:
            affix: Affix as published (« DU CLOS DE L'ÉCOTAY »).

        Returns:
            « clos ecotay », or None when empty.
        """
        decomposed = unicodedata.normalize("NFKD", affix or "")
        without_accents = "".join(character for character in decomposed if not unicodedata.combining(character))
        words = NON_LETTER_OR_DIGIT_PATTERN.sub(" ", without_accents.lower()).split()
        kept_words = [word for word in words if word not in AFFIX_KEY_IGNORED_WORDS]
        return " ".join(kept_words) or None

    @staticmethod
    def phone_e164(text: str | None) -> str | None:
        """
        Write a published phone number in E.164.

        Args:
            text: Phone as published (« 0679846555 », « 06 79 84 65 55 », « +33 6 79 84 65 55 »).

        Returns:
            « +33679846555 », or None when it is not a readable French number.
        """
        digits = NON_DIGIT_PATTERN.sub("", text or "")
        if len(digits) == FRENCH_NATIONAL_PHONE_LENGTH and digits.startswith("0"):
            return f"+{FRENCH_COUNTRY_CODE}{digits[1:]}"
        if len(digits) == FRENCH_NATIONAL_PHONE_LENGTH + 1 and digits.startswith(FRENCH_COUNTRY_CODE):
            return f"+{digits}"
        return None

    @staticmethod
    def siren(text: str | None) -> str | None:
        """
        Read a SIREN, or the SIREN part of a SIRET.

        Args:
            text: Number as published, spaces allowed.

        Returns:
            The nine digits, or None when the number has another length.
        """
        digits = NON_DIGIT_PATTERN.sub("", text or "")
        if len(digits) in (SIREN_LENGTH, SIRET_LENGTH):
            return digits[:SIREN_LENGTH]
        return None

    @staticmethod
    def postal_code(text: str | None) -> str | None:
        """
        Read a French postal code.

        Args:
            text: Code as published.

        Returns:
            The five digits, or None when unreadable.
        """
        digits = NON_DIGIT_PATTERN.sub("", text or "")
        return digits if len(digits) == POSTAL_CODE_LENGTH else None

    @classmethod
    def _capitalize_word(cls, word: str, is_first_word: bool) -> str:
        """
        Capitalize one word of a name, hyphenated parts included.

        Args:
            word: Lower-case word (« saint-aubin-du-cormier »).
            is_first_word: Whether the word opens the name, which is always capitalized.

        Returns:
            The capitalized word.
        """
        parts = word.split("-")
        return "-".join(
            cls._capitalize_part(part, is_name_start=is_first_word and index == 0) for index, part in enumerate(parts)
        )

    @staticmethod
    def _capitalize_part(part: str, is_name_start: bool) -> str:
        """
        Capitalize one hyphenated part: « d'opale » becomes « d'Opale », « o'neil » « O'Neil »,
        « dublin's » « Dublin's », and « de » stays « de ».

        Args:
            part: Lower-case part.
            is_name_start: Whether the part opens the name.

        Returns:
            The capitalized part.
        """
        for apostrophe in APOSTROPHES:
            if apostrophe in part:
                elision, _, rest = part.partition(apostrophe)
                if is_name_start or elision not in ELIDED_ARTICLES:
                    elision = elision.capitalize()
                if len(elision) == 1:
                    rest = rest[:1].upper() + rest[1:]
                return f"{elision}{apostrophe}{rest}"
        if part in LOWERCASE_NAME_WORDS and not is_name_start:
            return part
        return part[:1].upper() + part[1:]
