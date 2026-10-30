"""Reference data routes: the French departments."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.database import get_db
from models.department import Department
from models.user import User
from schemas.reference import DepartmentResponse
from services.auth_service import get_current_user

router = APIRouter(tags=["references"])


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
