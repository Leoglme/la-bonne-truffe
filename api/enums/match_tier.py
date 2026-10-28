"""Verdict of a litter group against a search profile."""

from enum import StrEnum


class MatchTier(StrEnum):
    """Verdict of a litter group against a search profile; it decides the notification."""

    PREFERRED = "preferred"
    ACCEPTABLE = "acceptable"
    IGNORED = "ignored"
    EXCLUDED = "excluded"
