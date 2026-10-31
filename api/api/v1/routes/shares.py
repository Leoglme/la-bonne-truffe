"""Share routes: the private link of a litter, and the page it opens without an account."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from core.clock import naive_utc_now
from core.database import get_db
from models.user import User
from schemas.litter_share import LitterShareCreate, LitterShareLink, SharedLitter
from services.auth_service import get_current_user
from services.litter_share_service import LitterShareService

router = APIRouter(tags=["shares"])


@router.post("/litters/{litter_id}/shares", response_model=LitterShareLink, status_code=status.HTTP_201_CREATED)
async def share_litter(
    litter_id: int,
    payload: LitterShareCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> LitterShareLink:
    """
    Create the link of a litter, valid thirty days.

    Args:
        litter_id: The litter.
        payload: Word for the people the link goes to.
        current_user: The authenticated user.
        db: Database session.

    Returns:
        The link to send.
    """
    return LitterShareService.create(db, current_user, litter_id, payload.message, naive_utc_now())


@router.get("/shares/{token}", response_model=SharedLitter)
async def read_shared_litter(token: str, db: Session = Depends(get_db)) -> SharedLitter:
    """
    Read the page of a shared link. No account: the secret link is the key.

    Args:
        token: Secret part of the link.
        db: Database session.

    Returns:
        The litter, the sharer's first name and their word.
    """
    return LitterShareService.read(db, token, naive_utc_now())
