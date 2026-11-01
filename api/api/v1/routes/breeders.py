"""Breeder routes: the Éleveurs list, the search, the detail, the creation by hand, its links, the follow, its notes."""

from fastapi import APIRouter, BackgroundTasks, Depends, Query, status
from sqlalchemy.orm import Session, sessionmaker

from core.clock import naive_utc_now
from core.database import get_db
from enums.breeder_link_kind import BreederLinkKind
from enums.listing_source import ListingSource
from models.user import User
from schemas.breeder import (
    BreederCard,
    BreederCreate,
    BreederDetail,
    BreederFilter,
    BreederFollowNoteCreate,
    BreederFollowNoteResponse,
    BreederFollowUpdate,
    BreederLinkCreate,
    BreederLinkPreview,
    BreederSearchResults,
    BreederSocialAccount,
    BreederSort,
    BreederUpdate,
)
from services.auth_service import get_current_user
from services.breeder_command_service import BreederCommandService
from services.breeder_link_service import breeder_link_service
from services.breeder_query_service import BreederQueryService
from services.source_run_launcher import source_run_launcher

router = APIRouter(prefix="/breeders", tags=["breeders"])


@router.get("", response_model=list[BreederCard])
async def list_breeders(
    filter: BreederFilter = BreederFilter.ALL,
    sort: BreederSort = BreederSort.PROMISING,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[BreederCard]:
    """
    Return the breeders of the Éleveurs tab.

    Args:
        filter: Which breeders (« Suivis », « Gold », « Spaniel Club », « Une portée en cours »).
        sort: The most promising first, or by name.
        current_user: The authenticated user.
        db: Database session.

    Returns:
        The cards.
    """
    return BreederQueryService.list_cards(db, current_user.id, filter, sort)


@router.get("/search", response_model=BreederSearchResults)
async def search_breeders(
    q: str = Query(default="", max_length=120),
    limit: int = Query(default=8, ge=1, le=30),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BreederSearchResults:
    """
    Return the suggestions for what the user typed: breeders, then litters.

    Args:
        q: The query; accents, spaces and case do not matter.
        limit: Breeders and litters kept at most, each.
        current_user: The authenticated user.
        db: Database session.

    Returns:
        The suggestions.
    """
    return BreederQueryService.search(db, current_user.id, q, limit)


@router.get("/{breeder_id}", response_model=BreederDetail)
async def read_breeder(
    breeder_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BreederDetail:
    """
    Return the detail of a breeder.

    Args:
        breeder_id: The breeder.
        current_user: The authenticated user.
        db: Database session.

    Returns:
        The detail.
    """
    return BreederQueryService.detail(db, current_user.id, breeder_id)


@router.post("", response_model=BreederDetail, status_code=status.HTTP_201_CREATED)
async def create_breeder(
    payload: BreederCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BreederDetail:
    """
    Add a breeder by hand (found on Facebook, on a sign, by word of mouth), and follow it when asked.

    Args:
        payload: Name, place, links, phone, note.
        current_user: The authenticated user.
        db: Database session.

    Returns:
        The detail of the breeder, which may be one already known.
    """
    breeder = BreederCommandService.create_manual(db, current_user, payload)
    return BreederQueryService.detail(db, current_user.id, breeder.id)


@router.patch("/{breeder_id}", response_model=BreederDetail)
async def update_breeder(
    breeder_id: int,
    payload: BreederUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BreederDetail:
    """
    Change the links, the phone, the site or the notes of a breeder.

    Args:
        breeder_id: The breeder.
        payload: What changes.
        current_user: The authenticated user.
        db: Database session.

    Returns:
        The updated detail.
    """
    BreederCommandService.update(db, breeder_id, payload)
    return BreederQueryService.detail(db, current_user.id, breeder_id)


@router.post("/{breeder_id}/links/preview", response_model=BreederLinkPreview)
def preview_breeder_link(
    breeder_id: int,
    payload: BreederLinkCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BreederLinkPreview:
    """
    Tell what a pasted link is before it is added: the breeder's site on Chiens de France, a social account, or
    another site, whose page is read for the accounts it links.

    Args:
        breeder_id: The breeder.
        payload: The link.
        current_user: The authenticated user.
        db: Database session.

    Returns:
        What the app recognises.
    """
    BreederQueryService.get_breeder(db, breeder_id)
    reading = breeder_link_service.read(payload.url)
    return BreederLinkPreview(
        kind=reading.kind,
        address=reading.address,
        social_accounts=[
            BreederSocialAccount(account=account, url=address) for account, address in reading.social_accounts.items()
        ],
        is_page_read=reading.is_page_read,
    )


@router.post("/{breeder_id}/links", response_model=BreederDetail)
def add_breeder_link(
    breeder_id: int,
    payload: BreederLinkCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BreederDetail:
    """
    Add a pasted link to a breeder; its site on Chiens de France is read at once, in the background, unless a
    reading of the sites runs already.

    Args:
        breeder_id: The breeder.
        payload: The link.
        background_tasks: Where the reading of the site goes on after the answer.
        current_user: The authenticated user.
        db: Database session.

    Returns:
        The updated detail.
    """
    reading = breeder_link_service.add(db, breeder_id, payload.url)
    if reading.kind == BreederLinkKind.CHIENS_DE_FRANCE_SITE and source_run_launcher.claim(
        db, ListingSource.CHIENS_DE_FRANCE_SITES, naive_utc_now()
    ):
        session_factory = sessionmaker(bind=db.get_bind(), autoflush=False)
        background_tasks.add_task(source_run_launcher.read_breeder_site, session_factory, breeder_id)
    return BreederQueryService.detail(db, current_user.id, breeder_id)


@router.put("/{breeder_id}/follow", response_model=BreederDetail)
async def set_breeder_follow(
    breeder_id: int,
    payload: BreederFollowUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BreederDetail:
    """
    Follow a breeder, or change its alerts, its status and its reminder.

    Args:
        breeder_id: The breeder.
        payload: Settings, status, reminder.
        current_user: The authenticated user.
        db: Database session.

    Returns:
        The updated detail.
    """
    BreederCommandService.set_follow(db, current_user.id, breeder_id, payload)
    return BreederQueryService.detail(db, current_user.id, breeder_id)


@router.delete("/{breeder_id}/follow", response_model=BreederDetail)
async def remove_breeder_follow(
    breeder_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BreederDetail:
    """
    Stop following a breeder: its settings, status, reminder and notes are deleted.

    Args:
        breeder_id: The breeder.
        current_user: The authenticated user.
        db: Database session.

    Returns:
        The detail, without follow.
    """
    BreederCommandService.remove_follow(db, current_user.id, breeder_id)
    return BreederQueryService.detail(db, current_user.id, breeder_id)


@router.post("/{breeder_id}/notes", response_model=BreederFollowNoteResponse, status_code=status.HTTP_201_CREATED)
async def add_breeder_note(
    breeder_id: int,
    payload: BreederFollowNoteCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BreederFollowNoteResponse:
    """
    Add a dated note to a followed breeder.

    Args:
        breeder_id: The breeder.
        payload: The note.
        current_user: The authenticated user.
        db: Database session.

    Returns:
        The note.
    """
    note = BreederCommandService.add_note(db, current_user.id, breeder_id, payload)
    return BreederFollowNoteResponse(id=note.id, created_at=note.created_at, text=note.text)


@router.delete("/{breeder_id}/notes/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_breeder_note(
    breeder_id: int,
    note_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """
    Delete a note of a followed breeder.

    Args:
        breeder_id: The breeder.
        note_id: The note.
        current_user: The authenticated user.
        db: Database session.
    """
    BreederCommandService.remove_note(db, current_user.id, breeder_id, note_id)
