"""Readers for the Centrale Canine JSON values."""

from datetime import date, datetime
from zoneinfo import ZoneInfo

# Timestamps are read in French time: a litter born at 00:30 in Rennes is born that day.
FRENCH_TIMEZONE = ZoneInfo("Europe/Paris")


class SccValueParser:
    """
    Turns the raw JSON values into typed ones.

    The site runs on Drupal: most fields come as a one-element list (``"n_birth_date": [1783252800]``),
    a few as plain strings (``"n_variety": "158"``) or booleans (``"n_is_borned": true``). An empty
    list or an empty string means the value is unknown: every reader then returns None.
    """

    @staticmethod
    def first_value(value: object) -> object:
        """
        The value itself, or the first element of a Drupal one-element list.

        Args:
            value: Raw JSON value.

        Returns:
            The scalar value, or None for an empty list.
        """
        if isinstance(value, list):
            return value[0] if value else None
        return value

    @classmethod
    def to_text(cls, value: object) -> str | None:
        """
        Read a text value.

        Args:
            value: Raw JSON value.

        Returns:
            The stripped text, or None when empty.
        """
        scalar = cls.first_value(value)
        if scalar is None or isinstance(scalar, bool):
            return None
        text = str(scalar).strip()
        return text or None

    @classmethod
    def to_int(cls, value: object) -> int | None:
        """
        Read an integer value.

        Args:
            value: Raw JSON value (``3``, ``[3]``, ``"3"``, ``3.0``).

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
            value: Raw JSON value (``4.5``, ``[4.5]``, ``"4,5"``).

        Returns:
            The number, or None when empty or not a number.
        """
        scalar = cls.first_value(value)
        if isinstance(scalar, bool):
            return None
        if isinstance(scalar, int | float):
            return float(scalar)
        text = cls.to_text(scalar)
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
            value: Raw JSON value (``true``, ``[1]``, ``"1"``, ``"true"``).

        Returns:
            The boolean, or None when empty or unreadable.
        """
        scalar = cls.first_value(value)
        if isinstance(scalar, bool):
            return scalar
        text = cls.to_text(scalar)
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
            value: Seconds since the epoch (``[1791212409]`` or ``1791212409``).

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
            value: Seconds since the epoch (``[1783252800]`` or ``1783252800``).

        Returns:
            The day, or None when empty or not positive.
        """
        seconds = cls.to_int(value)
        if seconds is None or seconds <= 0:
            return None
        return datetime.fromtimestamp(seconds, tz=FRENCH_TIMEZONE).date()

    @classmethod
    def to_coordinates(cls, value: object) -> tuple[float, float] | None:
        """
        Read a ``"latitude,longitude"`` location.

        Args:
            value: Raw JSON value (``["48.44418,-1.162504"]``).

        Returns:
            The latitude and the longitude, or None when empty or unreadable.
        """
        text = cls.to_text(value)
        if text is None or "," not in text:
            return None
        latitude_text, longitude_text = text.split(",", 1)
        latitude = cls.to_float(latitude_text)
        longitude = cls.to_float(longitude_text)
        if latitude is None or longitude is None:
            return None
        return latitude, longitude
