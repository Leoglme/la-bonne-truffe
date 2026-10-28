"""Source routes: state of each source, and a run launched by hand."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.database import get_db
from enums.listing_source import ListingSource
from models.user import User
from schemas.source_status import SourceStatus
from services.auth_service import get_current_user
from services.collection_runner import collection_runner
from services.collectors.centrale_canine import CentraleCanineCollector
from services.source_status_service import COLLECTED_SOURCES, SourceStatusService

router = APIRouter(prefix="/sources", tags=["sources"])


@router.get("", response_model=list[SourceStatus])
async def list_sources(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[SourceStatus]:
    """
    Return the last run of every source.

    Args:
        current_user: The authenticated user.
        db: Database session.

    Returns:
        The statuses.
    """
    return SourceStatusService.list_statuses(db)


@router.post("/{source}/run", response_model=list[SourceStatus])
def run_source(
    source: ListingSource,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[SourceStatus]:
    """
    Run a collection now (blocking: about one second per page read).

    Args:
        source: The source.
        current_user: The authenticated user.
        db: Database session.

    Returns:
        The statuses after the run.

    Raises:
        HTTPException: 501 for a source without collector yet.
    """
    if source not in COLLECTED_SOURCES:
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Cette source n'est pas encore relevée")
    collection_runner.run_centrale_canine(db, CentraleCanineCollector())
    return SourceStatusService.list_statuses(db)
