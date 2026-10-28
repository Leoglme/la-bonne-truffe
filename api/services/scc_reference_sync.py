"""
Reads the filter identifiers of the Centrale Canine: department ``t_ID`` and variety identifiers.

Every litters page lists them in ``litters.filters``, for instance ``"t_41": "35 - Ile-et-Vilaine"``
and ``"158": "rouge et dore"`` (docs/02-sources.md). The department list only holds the departments
that have litters of the breed at that moment. Nothing is guessed: a department the list does not
hold keeps its identifier (or none), and a variety the seeders do not know is only reported.
"""

import re
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from enums.listing_source import ListingSource
from models.breed import Breed
from models.breed_variety import BreedVariety
from models.department import Department

DEPARTMENT_LABEL_PATTERN = re.compile(r"^\s*(\d{2,3}|2[AB])\s*-")


@dataclass(frozen=True)
class SccFilterOption:
    """One accepted value of a filter, with its label."""

    value: str
    label: str


@dataclass
class SccReferenceOptions:
    """The accepted values of the department, variety and « Portées » filters."""

    departments: list[SccFilterOption] = field(default_factory=list)
    varieties: list[SccFilterOption] = field(default_factory=list)
    birth_statuses: list[SccFilterOption] = field(default_factory=list)


@dataclass
class SccReferenceSyncResult:
    """What the synchronisation filled in, and the varieties the seeders do not know."""

    department_term_ids_set: dict[str, str] = field(default_factory=dict)
    unknown_varieties: list[SccFilterOption] = field(default_factory=list)
    birth_statuses: list[SccFilterOption] = field(default_factory=list)


class SccReferenceSync:
    """Stores the department identifiers a litters page lists, and checks its varieties."""

    @classmethod
    def parse_options(cls, filters: dict[str, dict[str, str]]) -> SccReferenceOptions:
        """
        Read the ``litters.filters`` object of a page.

        Args:
            filters: Filter name → value → label, as ``CentraleCanineCollector.page_filters`` returns it.

        Returns:
            The options of the three filters; ``all`` is left out.
        """
        return SccReferenceOptions(
            departments=cls._options_of(filters, "department"),
            varieties=cls._options_of(filters, "variety"),
            birth_statuses=cls._options_of(filters, "is_borned"),
        )

    def sync(self, db: Session, breed: Breed, filters: dict[str, dict[str, str]]) -> SccReferenceSyncResult:
        """
        Store the department ``t_ID`` a page lists, and report the varieties no seeded variety carries.

        The page is the authority: an identifier that changed on the site is updated. A variety is never
        mapped to colours on a guess: an unknown one is only reported.

        Args:
            db: Database session; committed at the end.
            breed: Breed whose page was read.
            filters: Filter name → value → label, from the page.

        Returns:
            What was set, and the unknown varieties.
        """
        options = self.parse_options(filters)
        result = SccReferenceSyncResult(birth_statuses=options.birth_statuses)

        departments_by_code = {department.code: department for department in db.query(Department)}
        for option in options.departments:
            match = DEPARTMENT_LABEL_PATTERN.match(option.label)
            department = departments_by_code.get(match.group(1)) if match else None
            if department is not None and department.scc_term_id != option.value:
                department.scc_term_id = option.value
                result.department_term_ids_set[department.code] = option.value

        known_variety_ids = {
            variety.source_variety_id
            for variety in db.query(BreedVariety).filter(
                BreedVariety.breed_id == breed.id, BreedVariety.source == ListingSource.CENTRALE_CANINE
            )
        }
        result.unknown_varieties = [option for option in options.varieties if option.value not in known_variety_ids]

        db.commit()
        return result

    @staticmethod
    def _options_of(filters: dict[str, dict[str, str]], filter_name: str) -> list[SccFilterOption]:
        """
        The options of one filter, ``all`` excluded.

        Args:
            filters: Filter name → value → label.
            filter_name: ``department``, ``variety`` or ``is_borned``.

        Returns:
            The options, in the page's order.
        """
        return [
            SccFilterOption(value=value, label=label)
            for value, label in filters.get(filter_name, {}).items()
            if value != "all"
        ]


scc_reference_sync = SccReferenceSync()
