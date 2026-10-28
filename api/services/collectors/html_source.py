"""What the HTML collectors share: the plan a run reads, and what it brings back."""

from dataclasses import dataclass, field
from typing import Protocol

from services.collectors.raw_listing import RawListing


@dataclass(frozen=True)
class HtmlBreedTarget:
    """A breed to read on an HTML source, with the slug the source uses in its addresses."""

    breed_id: int
    source_slug: str


@dataclass(frozen=True)
class HtmlDepartmentTarget:
    """A department of the profiles, with the region the sources group it under."""

    code: str
    region_name: str


@dataclass(frozen=True)
class HtmlCollectionPlan:
    """What one run reads on an HTML source: the breeds of the active profiles, in their departments."""

    breeds: tuple[HtmlBreedTarget, ...]
    departments: tuple[HtmlDepartmentTarget, ...]


@dataclass(frozen=True)
class HtmlRawPage:
    """One page exactly as received, kept for ``cli.py collect --save-raw``."""

    url: str
    html: str


@dataclass
class HtmlCollection:
    """Listings read by a run, the departments it covered, and the pages they come from."""

    listings: list[RawListing] = field(default_factory=list)
    collected_department_codes: set[str] = field(default_factory=set)
    raw_pages: list[HtmlRawPage] = field(default_factory=list)


class HtmlSourceCollector(Protocol):
    """What the collection runner needs from an HTML collector."""

    def collect(self, plan: HtmlCollectionPlan) -> HtmlCollection:
        """
        Read the source for a plan.

        Args:
            plan: Breeds and departments to read.

        Returns:
            The listings, the departments covered and the pages read.
        """
        ...
