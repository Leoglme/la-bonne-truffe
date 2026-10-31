"""How every ingestion refreshes a field: the value a source gives now, or the stored one when it gives none."""

from datetime import datetime
from typing import TypeVar

StoredValue = TypeVar("StoredValue", str, bool, int, float, datetime)


def known_or_current(new_value: StoredValue | None, current_value: StoredValue | None) -> StoredValue | None:
    """
    The value the source gives now, or the stored one when the source gives none.

    Args:
        new_value: Value read by the collector.
        current_value: Value stored.

    Returns:
        The value to keep.
    """
    return new_value if new_value is not None else current_value
