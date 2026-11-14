"""The name of a dog as two sources compare it, to tell the same dog on both."""

import re

from core.text import without_accents

NAME_WORD_PATTERN = re.compile(r"[a-z0-9]+")
WITHOUT_AFFIX_SUFFIX = " sans affixe"


class DogName:
    """Reads a dog's name the same way whatever the source wrote around it."""

    @staticmethod
    def key_of(name: str | None) -> str:
        """
        A dog's name as two sources compare it: lower case, without accents nor punctuation, and without the
        « (Sans Affixe) » Chiens de France writes after a dog that has no affix.

        Args:
            name: « Viggo Du Clos De L'Ecotay », « Valko (Sans Affixe) ».

        Returns:
            « viggo du clos de l ecotay », « valko »; empty for no name.
        """
        key = " ".join(NAME_WORD_PATTERN.findall(without_accents(name or "").lower()))
        return key.removesuffix(WITHOUT_AFFIX_SUFFIX)
