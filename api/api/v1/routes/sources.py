"""Source routes: state of each source, a run launched by hand, and the relay of the desktop app."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.clock import naive_utc_now
from core.database import get_db
from enums.listing_source import ListingSource
from models.user import User
from schemas.centrale_canine_relay import CentraleCanineRelayAnswer, CentraleCanineRelayRequest
from schemas.source_status import SourceStatus
from services.auth_service import get_current_user
from services.centrale_canine_relay import RelayLeaseLostError, centrale_canine_relay
from services.collection_runner import collection_runner
from services.source_status_service import COLLECTED_SOURCES, DESKTOP_RELAYED_SOURCES, SourceStatusService

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
        HTTPException: 409 for a source the desktop app reads; 501 for a source this machine does not collect.
    """
    if source in DESKTOP_RELAYED_SOURCES:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Cette source est relevée par l'app Windows")
    if source not in COLLECTED_SOURCES:
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Cette source n'est pas encore relevée")
    collection_runner.run_source(db, source)
    return SourceStatusService.list_statuses(db)


@router.post("/centrale_canine/relay", response_model=CentraleCanineRelayAnswer)
def relay_centrale_canine(
    relay_request: CentraleCanineRelayRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CentraleCanineRelayAnswer:
    """
    Relay the Centrale Canine through the desktop app: start the run of the hour, ask for the pages still
    to read, then run the collection on them.

    Args:
        relay_request: The call of the desktop app, with every page it read since the relay started.
        current_user: The authenticated user.
        db: Database session.

    Returns:
        What the desktop app does next.

    Raises:
        HTTPException: 409 when this server reads the Centrale Canine itself, or when the relay token expired.
    """
    if ListingSource.CENTRALE_CANINE not in DESKTOP_RELAYED_SOURCES:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Ce serveur relève lui-même la Centrale Canine"
        )
    try:
        return centrale_canine_relay.answer(db, relay_request, naive_utc_now())
    except RelayLeaseLostError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error


@router.post("/centrale_canine/relay-request", status_code=status.HTTP_204_NO_CONTENT)
def request_centrale_canine_relay(current_user: User = Depends(get_current_user)) -> None:
    """
    Ask the desktop app of a computer that is on to read the Centrale Canine at its next check, within five minutes.

    Args:
        current_user: The authenticated user.

    Raises:
        HTTPException: 409 when this server reads the Centrale Canine itself.
    """
    if ListingSource.CENTRALE_CANINE not in DESKTOP_RELAYED_SOURCES:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Ce serveur relève lui-même la Centrale Canine"
        )
    centrale_canine_relay.request_run()
