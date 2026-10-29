"""The texts the sources publish, made comparable from one source to the other."""

import unicodedata


def without_accents(text: str) -> str:
    """
    The text with each accented letter replaced by its plain letter: « Élevage du Mâle » gives « Elevage du Male ».

    Args:
        text: Any text.

    Returns:
        The text without accents, its case kept.
    """
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(character for character in decomposed if not unicodedata.combining(character))
