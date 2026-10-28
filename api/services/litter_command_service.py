"""Changes the user makes on a litter: confirmed colours, follow-up status, notes."""

from sqlalchemy.orm import Session

from core.clock import naive_utc_now
from models.follow_up import FollowUp, FollowUpNote
from schemas.litter import ColorConfirmation, FollowUpNoteCreate, FollowUpUpdate
from services.litter_query_service import LitterQueryService
from services.matching.match_refresh import match_refresh_service


class LitterCommandService:
    """Writes what Léo learned or decided about a litter; every write is scoped to the user."""

    @staticmethod
    def confirm_colors(db: Session, litter_group_id: int, payload: ColorConfirmation) -> None:
        """
        Store the colours confirmed after a call; they override every source. Re-evaluates silently.

        Args:
            db: Database session.
            litter_group_id: The litter.
            payload: Confirmed colours, empty to remove the confirmation.
        """
        group = LitterQueryService.get_group(db, litter_group_id)
        group.confirmed_colors = [color.value for color in dict.fromkeys(payload.colors)]
        db.commit()
        match_refresh_service.refresh(db, naive_utc_now(), should_notify=False)

    @staticmethod
    def set_follow_up(db: Session, user_id: int, litter_group_id: int, payload: FollowUpUpdate) -> FollowUp:
        """
        Create or update the follow-up of a litter (« Suivre » starts it at « à appeler »).

        Args:
            db: Database session.
            user_id: The user.
            litter_group_id: The litter.
            payload: Status, reminder and last contact.

        Returns:
            The follow-up.
        """
        LitterQueryService.get_group(db, litter_group_id)
        follow_up = (
            db.query(FollowUp)
            .filter(FollowUp.user_id == user_id, FollowUp.litter_group_id == litter_group_id)
            .one_or_none()
        )
        if follow_up is None:
            follow_up = FollowUp(user_id=user_id, litter_group_id=litter_group_id)
            db.add(follow_up)
        follow_up.status = payload.status
        follow_up.next_reminder_at = payload.next_reminder_at
        follow_up.last_contact_at = payload.last_contact_at
        db.commit()
        return follow_up

    @classmethod
    def add_note(cls, db: Session, user_id: int, litter_group_id: int, payload: FollowUpNoteCreate) -> FollowUpNote:
        """
        Add a dated note; a litter not followed yet starts being followed.

        Args:
            db: Database session.
            user_id: The user.
            litter_group_id: The litter.
            payload: The note.

        Returns:
            The note.
        """
        LitterQueryService.get_group(db, litter_group_id)
        follow_up = (
            db.query(FollowUp)
            .filter(FollowUp.user_id == user_id, FollowUp.litter_group_id == litter_group_id)
            .one_or_none()
        )
        if follow_up is None:
            follow_up = FollowUp(user_id=user_id, litter_group_id=litter_group_id)
            db.add(follow_up)
            db.flush()
        note = FollowUpNote(follow_up_id=follow_up.id, text=payload.text.strip(), created_at=naive_utc_now())
        db.add(note)
        db.commit()
        return note
