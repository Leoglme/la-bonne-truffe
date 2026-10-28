"""The current time as the database stores it: naive UTC."""

from datetime import UTC, datetime


def naive_utc_now() -> datetime:
    """Current time as naive UTC, the storage convention."""
    return datetime.now(UTC).replace(tzinfo=None)
