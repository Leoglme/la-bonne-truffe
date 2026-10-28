"""Level a search profile gives to a coat colour."""

from enum import StrEnum


class ColorPreferenceLevel(StrEnum):
    """Level a search profile gives to a coat colour."""

    PREFERRED = "preferred"
    ACCEPTABLE = "acceptable"
    IGNORED = "ignored"
