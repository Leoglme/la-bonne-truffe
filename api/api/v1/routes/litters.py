"""Litter routes: home screen list and its visits, detail, confirmed colours, follow-up and notes."""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from core.database import get_db
from enums.listing_kind import ListingKind
from enums.match_tier import MatchTier
from models.user import User
from schemas.litter import (
    ColorConfirmation,
    FollowUpCard,
    FollowUpNoteCreate,
    FollowUpNoteResponse,
    FollowUpUpdate,
    LitterCard,
    LitterDetail,
    LitterVisit,
    SexConfirmation,
)
from services.auth_service import get_current_user
from services.litter_command_service import LitterCommandService
from services.litter_query_service import LitterQueryService, LitterSort

router = APIRouter(tags=["litters"])


@router.get("/litters", response_model=list[LitterCard])
async def list_litters(
    tier: MatchTier | None = None,
    kind: ListingKind | None = None,
    active: bool = True,
    sort: LitterSort = LitterSort.SCORE,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[LitterCard]:
    """
    Return the litters of the home screen.

    Args:
        tier: Only this tier (« Préférées »).
        kind: Only this kind (« À naître »).
        active: Active litters, or the ones gone from their sources.
        sort: By score or by freshness.
        current_user: The authenticated user.
        db: Database session.

    Returns:
        The cards.
    """
    return LitterQueryService.list_cards(db, current_user.id, tier, kind, active, sort)


@router.post("/litters/visit", response_model=LitterVisit)
async def record_litters_visit(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> LitterVisit:
    """
    Record that the home list is looked at now; the dashboard calls it once per launch.

    Args:
        current_user: The authenticated user.
        db: Database session.

    Returns:
        The previous look: the litters first seen after it are the new ones.
    """
    return LitterVisit(previous_visit_at=LitterCommandService.record_visit(db, current_user))


@router.get("/litters/{litter_id}", response_model=LitterDetail)
async def read_litter(
    litter_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> LitterDetail:
    """
    Return the detail of a litter.

    Args:
        litter_id: The litter.
        current_user: The authenticated user.
        db: Database session.

    Returns:
        The detail.
    """
    return LitterQueryService.detail(db, current_user.id, litter_id)


@router.patch("/litters/{litter_id}/colors", response_model=LitterDetail)
async def confirm_litter_colors(
    litter_id: int,
    payload: ColorConfirmation,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> LitterDetail:
    """
    Confirm the colours of a litter after a call.

    Args:
        litter_id: The litter.
        payload: Confirmed colours.
        current_user: The authenticated user.
        db: Database session.

    Returns:
        The updated detail.
    """
    LitterCommandService.confirm_colors(db, litter_id, payload)
    return LitterQueryService.detail(db, current_user.id, litter_id)


@router.patch("/litters/{litter_id}/sexes", response_model=LitterDetail)
async def confirm_litter_sexes(
    litter_id: int,
    payload: SexConfirmation,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> LitterDetail:
    """
    Confirm the males and females of a litter after a call, when the sources do not tell.

    Args:
        litter_id: The litter.
        payload: Confirmed counts, both empty to remove the confirmation.
        current_user: The authenticated user.
        db: Database session.

    Returns:
        The updated detail.
    """
    LitterCommandService.confirm_sexes(db, litter_id, payload)
    return LitterQueryService.detail(db, current_user.id, litter_id)


@router.put("/litters/{litter_id}/follow-up", response_model=LitterDetail)
async def set_litter_follow_up(
    litter_id: int,
    payload: FollowUpUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> LitterDetail:
    """
    Follow a litter, or change where the exchange stands.

    Args:
        litter_id: The litter.
        payload: Status and reminder.
        current_user: The authenticated user.
        db: Database session.

    Returns:
        The updated detail.
    """
    LitterCommandService.set_follow_up(db, current_user.id, litter_id, payload)
    return LitterQueryService.detail(db, current_user.id, litter_id)


@router.delete("/litters/{litter_id}/follow-up", response_model=LitterDetail)
async def remove_litter_follow_up(
    litter_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> LitterDetail:
    """
    Stop following a litter: its status, reminder and notes are deleted.

    Args:
        litter_id: The litter.
        current_user: The authenticated user.
        db: Database session.

    Returns:
        The detail, without follow-up.
    """
    LitterCommandService.remove_follow_up(db, current_user.id, litter_id)
    return LitterQueryService.detail(db, current_user.id, litter_id)


@router.post("/litters/{litter_id}/notes", response_model=FollowUpNoteResponse, status_code=status.HTTP_201_CREATED)
async def add_litter_note(
    litter_id: int,
    payload: FollowUpNoteCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FollowUpNoteResponse:
    """
    Add a dated note to the follow-up of a litter.

    Args:
        litter_id: The litter.
        payload: The note.
        current_user: The authenticated user.
        db: Database session.

    Returns:
        The note.
    """
    note = LitterCommandService.add_note(db, current_user.id, litter_id, payload)
    return FollowUpNoteResponse(id=note.id, created_at=note.created_at, text=note.text)


@router.delete("/litters/{litter_id}/notes/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_litter_note(
    litter_id: int,
    note_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """
    Delete a note of the follow-up of a litter.

    Args:
        litter_id: The litter.
        note_id: The note.
        current_user: The authenticated user.
        db: Database session.
    """
    LitterCommandService.remove_note(db, current_user.id, litter_id, note_id)


@router.get("/follow-ups", response_model=list[FollowUpCard])
async def list_follow_ups(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = Query(default=100, ge=1, le=500),
) -> list[FollowUpCard]:
    """
    Return the followed litters, the next reminder first.

    Args:
        current_user: The authenticated user.
        db: Database session.
        limit: Maximum number of follow-ups.

    Returns:
        The follow-up cards.
    """
    return LitterQueryService.list_follow_ups(db, current_user.id)[:limit]
