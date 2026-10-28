"""Builds what a collection run reads, from the active search profiles."""

from sqlalchemy.orm import Session

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


class CollectionPlanner:
    """Turns the active profiles into the breeds and departments each collector reads."""

    @staticmethod
    def build_centrale_canine_plan(db: Session) -> CentraleCanineCollectionPlan:
        """
        Plan a Centrale Canine run: every breed of the active profiles, in each of their departments.

        A department whose ``t_ID`` is still unknown cannot be filtered on and is listed apart, so the
        run log tells to run ``python cli.py scc-sync``.

        Args:
            db: Database session.

        Returns:
            The plan, empty when no profile is active.
        """
        profiles = db.query(SearchProfile).filter(SearchProfile.is_active.is_(True)).order_by(SearchProfile.id).all()
        breed_slugs: list[str] = []
        department_codes: list[str] = []
        for profile in profiles:
            breed_slugs.extend(slug for slug in profile.breed_ids if slug not in breed_slugs)
            department_codes.extend(code for code in profile.department_codes if code not in department_codes)

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
            BreedVariety.source == ListingSource.CENTRALE_CANINE.value,
            BreedVariety.source_variety_id.is_not(None),
        )
        return SccBreedTarget(
            breed_id=breed.id,
            scc_slug=breed.scc_slug or "",
            varieties_by_source_id={
                variety.source_variety_id or "": SccVarietyTarget(
                    covered_colors=tuple(variety.covered_colors), is_ambiguous=variety.is_ambiguous
                )
                for variety in varieties
            },
        )
