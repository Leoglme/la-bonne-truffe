"""The current time as the database stores it (naive UTC), and its reading in French time."""

from datetime import UTC, date, datetime, time
from zoneinfo import ZoneInfo

FRENCH_TIMEZONE = ZoneInfo("Europe/Paris")


def naive_utc_now() -> datetime:
    """Current time as naive UTC, the storage convention."""
    return datetime.now(UTC).replace(tzinfo=None)


def to_french_time(moment: datetime) -> datetime:
    """
    Read a stored naive UTC time in French time.

    Args:
        moment: Naive UTC time, as stored.

    Returns:
        The aware time in Europe/Paris.
    """
    return moment.replace(tzinfo=UTC).astimezone(FRENCH_TIMEZONE)


def naive_utc_of_french_time(day: date, hour: int) -> datetime:
    """
    Store a French hour of a day as naive UTC.

    Args:
        day: The calendar day, in French time.
        hour: The hour of that day, in French time.

    Returns:
        The naive UTC time, as the database stores it.
    """
    return datetime.combine(day, time(hour=hour), tzinfo=FRENCH_TIMEZONE).astimezone(UTC).replace(tzinfo=None)


def french_date_of(moment: datetime) -> date:
    """
    Calendar day of a stored naive UTC time, in French time.

    Args:
        moment: Naive UTC time, as stored.

    Returns:
        The day in Europe/Paris.
    """
    return to_french_time(moment).date()
