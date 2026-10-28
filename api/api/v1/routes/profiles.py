"""Search profile routes: the criteria screen."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.database import get_db
from models.search_profile import SearchProfile
from models.user import User
from schemas.search_profile import SearchProfileResponse, SearchProfileUpdate
from services.auth_service import get_current_user
from services.search_profile_service import SearchProfileService

router = APIRouter(prefix="/profiles", tags=["profiles"])


@router.get("", response_model=list[SearchProfileResponse])
async def list_profiles(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[SearchProfile]:
    """
    Return the profiles of the user.

    Args:
        current_user: The authenticated user.
        db: Database session.

    Returns:
        The profiles.
    """
    return SearchProfileService.list_for_user(db, current_user.id)


@router.put("/{profile_id}", response_model=SearchProfileResponse)
async def update_profile(
    profile_id: int,
    payload: SearchProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SearchProfile:
    """
    Save the criteria and re-evaluate the litters.

    Args:
        profile_id: Profile to save.
        payload: New criteria.
        current_user: The authenticated user.
        db: Database session.

    Returns:
        The saved profile.
    """
    return SearchProfileService.update(db, current_user.id, profile_id, payload)
