"""The text the breeder search looks into, built once per write (docs/05, ``BreederQueryService``)."""

from urllib.parse import urlparse

from core.text import without_accents
from models.breeder import Breeder
from services.collectors.breeder_contact_parser import NON_LETTER_OR_DIGIT_PATTERN


class BreederSearchText:
    """
    Normalizes what a breeder can be searched by: affix, name, town, postal code, SIREN, phone, links.

    The text holds each value with its spaces, then without them, so that « du clos » and « duclos » both
    find « Du Clos de l'Élevage A ».
    """

    @classmethod
    def normalize(cls, text: str | None) -> str:
        """
        Lower case, no accent, letters and digits only, single spaces.

        Args:
            text: Any text.

        Returns:
            The normalized text, empty for None.
        """
        plain = without_accents(text or "").lower()
        return " ".join(NON_LETTER_OR_DIGIT_PATTERN.sub(" ", plain).split())

    @classmethod
    def build(cls, breeder: Breeder) -> str:
        """
        The search text of a breeder.

        Args:
            breeder: The breeder, as stored.

        Returns:
            The normalized values, each with and without spaces.
        """
        values = [
            breeder.affix,
            breeder.display_name,
            breeder.city,
            breeder.zip_code,
            breeder.siren,
            breeder.phone_e164,
            breeder.scc_site_slug,
            cls._host_name(breeder.chiens_de_france_site_url),
            cls._host_name(breeder.website),
        ]
        values.extend(link.get("label") for link in breeder.links)
        values.extend(cls._host_name(link.get("url")) for link in breeder.links)
        if breeder.phone_e164:
            values.append("0" + breeder.phone_e164.removeprefix("+33"))
        normalized = [cls.normalize(value) for value in values if value]
        compact = [value.replace(" ", "") for value in normalized if " " in value]
        return " ".join(dict.fromkeys(normalized + compact))

    @classmethod
    def matches(cls, search_text: str | None, query: str) -> bool:
        """
        Whether every word of a query is found in a search text.

        Args:
            search_text: The stored search text.
            query: What the user typed.

        Returns:
            True when each normalized word of the query is a substring of the text.
        """
        words = cls.normalize(query).split()
        if not words or not search_text:
            return False
        return all(word in search_text for word in words)

    @classmethod
    def holds_phrase(cls, search_text: str | None, query: str) -> bool:
        """
        Whether a query is found in a search text as one phrase, with or without its spaces: « ar ti » in
        « ar ti marellek », « 06 12 34 56 78 » in « 0612345678 ».

        Args:
            search_text: The stored search text.
            query: What the user typed.

        Returns:
            True when the normalized phrase is a substring of the text.
        """
        phrase = " ".join(cls.normalize(query).split())
        if not phrase or not search_text:
            return False
        return phrase in search_text or phrase.replace(" ", "") in search_text

    @staticmethod
    def _host_name(url: str | None) -> str | None:
        """
        The host of a URL, its ``www.`` dropped.

        Args:
            url: A URL, or a bare host.

        Returns:
            The host, or None for an empty URL.
        """
        if not url:
            return None
        host = urlparse(url if "://" in url else f"https://{url}").netloc
        return host.removeprefix("www.") or None
