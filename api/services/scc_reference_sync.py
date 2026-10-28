"""
Reads the filter identifiers of the Centrale Canine breed page: department ``t_ID`` and variety ids.

The page lists them in its « Département » and « Variété » ``<select>`` elements, for instance
``<option value="t_41">35 - Ile-et-Vilaine</option>`` (docs/02-sources.md). Nothing is guessed: a
department or a variety that the page does not list keeps a null identifier.
"""

import re
import unicodedata
from dataclasses import dataclass, field

from selectolax.lexbor import LexborHTMLParser
from sqlalchemy.orm import Session

from enums.listing_source import ListingSource
from models.breed import Breed
from models.breed_variety import BreedVariety
from models.department import Department

DEPARTMENT_OPTION_PATTERN = re.compile(r"^\s*(\d{2,3}|2[AB])\s*-")


@dataclass(frozen=True)
class SccSelectOption:
    """One ``<option>`` of a filter."""

    value: str
    label: str


@dataclass
class SccReferenceOptions:
    """The options of the filters of the breed page."""

    departments: list[SccSelectOption] = field(default_factory=list)
    varieties: list[SccSelectOption] = field(default_factory=list)
    birth_statuses: list[SccSelectOption] = field(default_factory=list)


@dataclass
class SccReferenceSyncResult:
    """What the synchronisation filled in."""

    department_term_ids_set: dict[str, str] = field(default_factory=dict)
    variety_ids_set: dict[str, str] = field(default_factory=dict)
    birth_statuses: list[SccSelectOption] = field(default_factory=list)


class SccReferenceSync:
    """Parses the breed page and stores the identifiers it lists."""

    @staticmethod
    def parse_options(html: str) -> SccReferenceOptions:
        """
        Read every ``<select>`` of the page and sort them by what their options look like.

        Args:
            html: HTML of the breed page.

        Returns:
            The options of the department, variety and « Portées » filters found.
        """
        options = SccReferenceOptions()
        for select in LexborHTMLParser(html).css("select"):
            select_options = [
                SccSelectOption(value=(option.attributes.get("value") or "").strip(), label=option.text(strip=True))
                for option in select.css("option")
            ]
            meaningful = [option for option in select_options if option.value and option.value != "all"]
            if not meaningful:
                continue
            if all(DEPARTMENT_OPTION_PATTERN.match(option.label) for option in meaningful):
                options.departments = meaningful
            elif any(SccReferenceSync._normalize(option.label).startswith("a naitre") for option in select_options):
                options.birth_statuses = select_options
            elif any("dore" in SccReferenceSync._normalize(option.label) for option in meaningful):
                options.varieties = meaningful
        return options

    def sync(self, db: Session, breed: Breed, html: str) -> SccReferenceSyncResult:
        """
        Fill the missing department ``t_ID`` and variety identifiers of a breed from its page.

        Args:
            db: Database session; committed at the end.
            breed: Breed whose page was read.
            html: HTML of the breed page.

        Returns:
            The identifiers set by this run (already known ones are left untouched).
        """
        options = self.parse_options(html)
        result = SccReferenceSyncResult(birth_statuses=options.birth_statuses)

        departments_by_code = {department.code: department for department in db.query(Department)}
        for option in options.departments:
            match = DEPARTMENT_OPTION_PATTERN.match(option.label)
            department = departments_by_code.get(match.group(1)) if match else None
            if department is not None and department.scc_term_id is None:
                department.scc_term_id = option.value
                result.department_term_ids_set[department.code] = option.value

        varieties = db.query(BreedVariety).filter(
            BreedVariety.breed_id == breed.id, BreedVariety.source == ListingSource.CENTRALE_CANINE.value
        )
        varieties_by_label = {self._normalize(variety.label): variety for variety in varieties}
        for option in options.varieties:
            variety = varieties_by_label.get(self._normalize(option.label))
            if variety is not None and variety.source_variety_id is None:
                variety.source_variety_id = option.value
                result.variety_ids_set[variety.label] = option.value

        db.commit()
        return result

    @staticmethod
    def _normalize(label: str) -> str:
        """
        Lowercase a label and strip its accents, to compare labels written slightly differently.

        Args:
            label: Label to normalize.

        Returns:
            The normalized label.
        """
        decomposed = unicodedata.normalize("NFKD", label)
        return "".join(character for character in decomposed if not unicodedata.combining(character)).lower().strip()


scc_reference_sync = SccReferenceSync()
