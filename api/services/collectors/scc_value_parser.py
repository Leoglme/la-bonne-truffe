"""Lenient readers for the Centrale Canine JSON values."""

from datetime import date, datetime
from zoneinfo import ZoneInfo

# Timestamps are read in French time: a litter born at 00:30 in Rennes is born that day.
FRENCH_TIMEZONE = ZoneInfo("Europe/Paris")


class SccValueParser:
    """
    Turns the raw JSON values into typed ones.

    The real response could not be recorded yet (docs/02-sources.md): a field may come as a number,
    a numeric string, a boolean or an empty string, so every reader accepts all of them and returns
    None for an empty or unreadable value.
    """

    @staticmethod
    def to_text(value: object) -> str | None:
        """
        Read a text value.

        Args:
            value: Raw JSON value.

        Returns:
            The stripped text, or None when empty.
        """
        if value is None or isinstance(value, bool):
            return None
        text = str(value).strip()
        return text or None

    @classmethod
    def to_int(cls, value: object) -> int | None:
        """
        Read an integer value.

        Args:
            value: Raw JSON value (``3``, ``"3"``, ``3.0``).

        Returns:
            The integer, or None when empty or not a number.
        """
        number = cls.to_float(value)
        return None if number is None else int(number)

    @classmethod
    def to_float(cls, value: object) -> float | None:
        """
        Read a decimal value; a French decimal comma is accepted.

        Args:
            value: Raw JSON value (``4.5``, ``"4,5"``).

        Returns:
            The number, or None when empty or not a number.
        """
        if isinstance(value, bool):
            return None
        if isinstance(value, int | float):
            return float(value)
        text = cls.to_text(value)
        if text is None:
            return None
        try:
            return float(text.replace(",", "."))
        except ValueError:
            return None

    @classmethod
    def to_bool(cls, value: object) -> bool | None:
        """
        Read a boolean value.

        Args:
            value: Raw JSON value (``true``, ``1``, ``"1"``, ``"true"``).

        Returns:
            The boolean, or None when empty or unreadable.
        """
        if isinstance(value, bool):
            return value
        text = cls.to_text(value)
        if text is None:
            return None
        lowered = text.lower()
        if lowered in {"1", "true", "oui", "yes"}:
            return True
        if lowered in {"0", "false", "non", "no"}:
            return False
        return None

    @classmethod
    def to_datetime(cls, value: object) -> datetime | None:
        """
        Read a Unix timestamp as naive UTC, the storage convention.

        Args:
            value: Seconds since the epoch, as a number or a numeric string.

        Returns:
            The naive UTC datetime, or None when empty or not positive.
        """
        seconds = cls.to_int(value)
        if seconds is None or seconds <= 0:
            return None
        return datetime.fromtimestamp(seconds, tz=FRENCH_TIMEZONE).astimezone(ZoneInfo("UTC")).replace(tzinfo=None)

    @classmethod
    def to_french_date(cls, value: object) -> date | None:
        """
        Read a Unix timestamp as a calendar day in French time.

        Args:
            value: Seconds since the epoch, as a number or a numeric string.

        Returns:
            The day, or None when empty or not positive.
        """
        seconds = cls.to_int(value)
        if seconds is None or seconds <= 0:
            return None
        return datetime.fromtimestamp(seconds, tz=FRENCH_TIMEZONE).date()
