"""Source routes: state of each source, what runs now, a run launched by hand, and the relay of the desktop app."""

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session, sessionmaker

from core.clock import naive_utc_now
from core.database import get_db
from enums.listing_source import ListingSource
from models.user import User
from schemas.centrale_canine_relay import CentraleCanineRelayAnswer, CentraleCanineRelayRequest
from schemas.source_activity import SourceActivity
from schemas.source_status import SourceStatus
from services.auth_service import get_current_user
from services.centrale_canine_relay import RelayLeaseLostError, centrale_canine_relay
from services.source_activity_service import SourceActivityService
from services.source_run_launcher import source_run_launcher
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


@router.get("/activity", response_model=SourceActivity)
def read_source_activity(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SourceActivity:
    """
    Return what runs now, wherever it was asked: the Sources page of every device polls it every few seconds.

    Args:
        current_user: The authenticated user.
        db: Database session.

    Returns:
        The sources the server reads, and where the relay of the desktop app stands.
    """
    return _current_activity(db)


@router.post("/{source}/run", response_model=SourceActivity, status_code=status.HTTP_202_ACCEPTED)
def run_source(
    source: ListingSource,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SourceActivity:
    """
    Run a collection now, in the background once the answer is sent; a source that runs already is not run twice.

    Args:
        source: The source.
        background_tasks: Where the run goes on after the answer.
        current_user: The authenticated user.
        db: Database session.

    Returns:
        What runs now, the source included.

    Raises:
        HTTPException: 409 for a source the desktop app reads; 501 for a source this server does not collect.
    """
    if source in DESKTOP_RELAYED_SOURCES:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Cette source est relevée par l'app Windows")
    if source not in COLLECTED_SOURCES:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Cette source n'est pas relevée par ce serveur"
        )
    if source_run_launcher.claim(db, source, naive_utc_now()):
        session_factory = sessionmaker(bind=db.get_bind(), autoflush=False)
        background_tasks.add_task(source_run_launcher.run, session_factory, source)
    return _current_activity(db)


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


@router.post("/centrale_canine/relay-request", response_model=SourceActivity)
def request_centrale_canine_relay(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SourceActivity:
    """
    Ask the desktop app of a computer that is on to read the Centrale Canine at its next check, within a minute.

    Args:
        current_user: The authenticated user.
        db: Database session.

    Returns:
        What runs now, the request waiting included.

    Raises:
        HTTPException: 409 when this server reads the Centrale Canine itself.
    """
    if ListingSource.CENTRALE_CANINE not in DESKTOP_RELAYED_SOURCES:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Ce serveur relève lui-même la Centrale Canine"
        )
    centrale_canine_relay.request_run()
    return _current_activity(db)


def _current_activity(db: Session) -> SourceActivity:
    """
    What runs now, with the relay of the desktop app when this server lets it read the Centrale Canine.

    Args:
        db: Database session.

    Returns:
        The activity.
    """
    relay = centrale_canine_relay if DESKTOP_RELAYED_SOURCES else None
    return SourceActivityService.read(db, relay, naive_utc_now())
