"""Puppy arrival routes: « C’est lui ! », the preparations to tick, and the search resumed."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from core.clock import naive_utc_now
from core.database import get_db
from models.user import User
from schemas.puppy_arrival import PuppyArrivalChecklist, PuppyArrivalResponse, PuppyArrivalStart
from services.auth_service import get_current_user
from services.puppy_arrival_service import PuppyArrivalService

router = APIRouter(tags=["puppy-arrival"])


@router.get("/puppy-arrival", response_model=PuppyArrivalResponse | None)
async def read_puppy_arrival(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PuppyArrivalResponse | None:
    """
    Return the puppy found, if any.

    Args:
        current_user: The authenticated user.
        db: Database session.

    Returns:
        The arrival, or null while the search goes on.
    """
    arrival = PuppyArrivalService.current(db, current_user.id)
    return PuppyArrivalService.to_response(arrival) if arrival is not None else None


@router.put("/puppy-arrival", response_model=PuppyArrivalResponse)
async def start_puppy_arrival(
    payload: PuppyArrivalStart,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PuppyArrivalResponse:
    """
    Pause the search on the puppy found, or change its litter or arrival day.

    Args:
        payload: The litter and the arrival day.
        current_user: The authenticated user.
        db: Database session.

    Returns:
        The arrival.
    """
    return PuppyArrivalService.start(db, current_user.id, payload.litter_group_id, payload.arrival_on, naive_utc_now())


@router.put("/puppy-arrival/checklist", response_model=PuppyArrivalResponse)
async def update_puppy_arrival_checklist(
    payload: PuppyArrivalChecklist,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PuppyArrivalResponse:
    """
    Keep the preparations ticked.

    Args:
        payload: Keys of the preparations ticked.
        current_user: The authenticated user.
        db: Database session.

    Returns:
        The arrival.
    """
    return PuppyArrivalService.update_checklist(db, current_user.id, payload.done_items)


@router.delete("/puppy-arrival", status_code=status.HTTP_204_NO_CONTENT)
async def resume_search(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """
    Resume the search: the litter alerts go out again.

    Args:
        current_user: The authenticated user.
        db: Database session.
    """
    PuppyArrivalService.resume_search(db, current_user.id)
