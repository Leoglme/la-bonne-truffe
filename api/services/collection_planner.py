"""Builds what a collection run reads, from the active search profiles."""

from sqlalchemy.orm import Session

from enums.coat_color import CoatColor
from enums.listing_source import ListingSource
from models.breed import Breed
from models.breed_variety import BreedVariety
from models.department import Department
from models.search_profile import SearchProfile
from services.collectors.centrale_canine import (
    CentraleCanineCollectionPlan,
    SccBreedTarget,
    SccDepartmentTarget,
    SccVarietyTarget,
)
from services.collectors.html_source import HtmlBreedTarget, HtmlCollectionPlan, HtmlDepartmentTarget


class CollectionPlanner:
    """Turns the active profiles into the breeds and departments each collector reads."""

    @staticmethod
    def build_centrale_canine_plan(db: Session) -> CentraleCanineCollectionPlan:
        """
        Plan a Centrale Canine run: every breed of the active profiles, in each of their departments.

        A department whose ``t_ID`` is still unknown cannot be filtered on and is listed apart: the run
        then reads the identifiers the Centrale Canine lists (``CollectionRunner``).

        Args:
            db: Database session.

        Returns:
            The plan, empty when no profile is active.
        """
        breed_slugs, department_codes = CollectionPlanner._profile_breeds_and_departments(db)
        breeds = (
            db.query(Breed)
            .filter(Breed.slug.in_(breed_slugs), Breed.is_active.is_(True), Breed.scc_slug.is_not(None))
            .order_by(Breed.id)
            .all()
        )
        departments_by_code = {
            department.code: department
            for department in db.query(Department).filter(Department.code.in_(department_codes))
        }

        department_targets: list[SccDepartmentTarget] = []
        departments_without_term_id: list[str] = []
        for code in department_codes:
            department = departments_by_code.get(code)
            if department is not None and department.scc_term_id:
                department_targets.append(SccDepartmentTarget(code=code, scc_term_id=department.scc_term_id))
            else:
                departments_without_term_id.append(code)

        return CentraleCanineCollectionPlan(
            breeds=tuple(CollectionPlanner._breed_target(db, breed) for breed in breeds),
            departments=tuple(department_targets),
            departments_without_term_id=tuple(departments_without_term_id),
        )

    @staticmethod
    def build_html_plan(db: Session, source: ListingSource) -> HtmlCollectionPlan:
        """
        Plan a run of an HTML source: every breed of the active profiles that has a slug on that source,
        in each of their departments, with the region the source groups it under.

        Args:
            db: Database session.
            source: The HTML source.

        Returns:
            The plan, empty when no profile is active or no breed is known to the source.
        """
        breed_slugs, department_codes = CollectionPlanner._profile_breeds_and_departments(db)
        breeds = db.query(Breed).filter(Breed.slug.in_(breed_slugs), Breed.is_active.is_(True)).order_by(Breed.id).all()
        breed_targets: list[HtmlBreedTarget] = []
        for breed in breeds:
            source_slug = CollectionPlanner._source_slug(breed, source)
            if source_slug:
                breed_targets.append(HtmlBreedTarget(breed_id=breed.id, source_slug=source_slug))
        departments_by_code = {
            department.code: department
            for department in db.query(Department).filter(Department.code.in_(department_codes))
        }
        return HtmlCollectionPlan(
            breeds=tuple(breed_targets),
            departments=tuple(
                HtmlDepartmentTarget(code=code, region_name=departments_by_code[code].region)
                for code in department_codes
                if code in departments_by_code
            ),
        )

    @staticmethod
    def _profile_breeds_and_departments(db: Session) -> tuple[list[str], list[str]]:
        """
        The breeds and departments of the active profiles, each once, departments in profile order.

        Args:
            db: Database session.

        Returns:
            Breed slugs and department codes.
        """
        profiles = db.query(SearchProfile).filter(SearchProfile.is_active.is_(True)).order_by(SearchProfile.id).all()
        breed_slugs: list[str] = []
        department_codes: list[str] = []
        for profile in profiles:
            breed_slugs.extend(slug for slug in profile.breed_ids if slug not in breed_slugs)
            department_codes.extend(code for code in profile.department_codes if code not in department_codes)
        return breed_slugs, department_codes

    @staticmethod
    def _source_slug(breed: Breed, source: ListingSource) -> str | None:
        """
        The name of a breed on an HTML source: the slug of its addresses, or its name in the ads of Cœur de Cocker.

        Args:
            breed: The breed.
            source: The source.

        Returns:
            The name, or None while unknown for that source.
        """
        if source == ListingSource.CHIENS_DE_FRANCE:
            return breed.chiens_de_france_id
        if source == ListingSource.CHIOTS_DE_FRANCE:
            return breed.chiots_de_france_id
        if source == ListingSource.WHOOF:
            return breed.whoof_id
        if source == ListingSource.COEUR_DE_COCKER:
            return breed.coeur_de_cocker_id
        return None

    @staticmethod
    def _breed_target(db: Session, breed: Breed) -> SccBreedTarget:
        """
        Describe a breed for the collector, with the colours of its known Centrale Canine varieties.

        Args:
            db: Database session.
            breed: Breed to read.

        Returns:
            The breed target.
        """
        varieties = db.query(BreedVariety).filter(
            BreedVariety.breed_id == breed.id,
            BreedVariety.source == ListingSource.CENTRALE_CANINE,
            BreedVariety.source_variety_id.is_not(None),
        )
        return SccBreedTarget(
            breed_id=breed.id,
            scc_slug=breed.scc_slug or "",
            varieties_by_source_id={
                variety.source_variety_id or "": SccVarietyTarget(
                    covered_colors=tuple(CoatColor(color) for color in variety.covered_colors),
                    is_ambiguous=variety.is_ambiguous,
                )
                for variety in varieties
            },
        )
