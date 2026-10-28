"""Whether a listing is registered in the LOF (French pedigree book)."""

from enum import StrEnum


class LofStatus(StrEnum):
    """Whether a listing is registered in the LOF (French pedigree book)."""

    LOF = "lof"
    NON_LOF = "non_lof"
    UNKNOWN = "unknown"
