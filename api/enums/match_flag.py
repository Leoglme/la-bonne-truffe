"""Unknown facts that lowered a litter's tier."""

from enum import StrEnum


class MatchFlag(StrEnum):
    """An unknown fact: it never excludes a litter, it keeps it below « préférée » and is shown to confirm."""

    COLOR_TO_CONFIRM = "color_to_confirm"
    SEX_UNKNOWN = "sex_unknown"
    LOF_UNKNOWN = "lof_unknown"
    PRICE_UNKNOWN = "price_unknown"
    DEPARTMENT_UNKNOWN = "department_unknown"
