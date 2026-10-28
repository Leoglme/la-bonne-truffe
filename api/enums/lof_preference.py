"""How much a search profile cares about the LOF."""

from enum import StrEnum


class LofPreference(StrEnum):
    """How much a search profile cares about the LOF."""

    REQUIRED = "required"
    PREFERRED = "preferred"
    ANY = "any"
