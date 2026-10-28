"""Reference data routes: breeds and departments."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.database import get_db
from models.breed import Breed
from models.department import Department
from models.user import User
from schemas.reference import BreedResponse, DepartmentResponse
from services.auth_service import get_current_user

router = APIRouter(tags=["references"])


@router.get("/breeds", response_model=list[BreedResponse])
async def list_breeds(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Breed]:
    """
    Return the breed catalogue, by French name.

    Args:
        current_user: The authenticated user.
        db: Database session.

    Returns:
        Every breed.
    """
    return db.query(Breed).order_by(Breed.name_fr).all()


@router.get("/departments", response_model=list[DepartmentResponse])
async def list_departments(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Department]:
    """
    Return the French departments, by region then code.

    Args:
        current_user: The authenticated user.
        db: Database session.

    Returns:
        Every department.
    """
    return db.query(Department).order_by(Department.region, Department.code).all()
