"""Changes the user makes on a litter: confirmed colours, follow-up status, notes, and looks at the home list."""

from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from core.clock import naive_utc_now
from models.follow_up import FollowUp, FollowUpNote
from models.user import User
from schemas.litter import ColorConfirmation, FollowUpNoteCreate, FollowUpUpdate, SexConfirmation
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
    def confirm_sexes(db: Session, litter_group_id: int, payload: SexConfirmation) -> None:
        """
        Store the males and females confirmed after a call; they override every source. Re-evaluates silently.

        Args:
            db: Database session.
            litter_group_id: The litter.
            payload: Confirmed counts, both empty to remove the confirmation.
        """
        group = LitterQueryService.get_group(db, litter_group_id)
        group.confirmed_male_count = payload.male_count
        group.confirmed_female_count = payload.female_count
        db.commit()
        match_refresh_service.refresh(db, naive_utc_now(), should_notify=False)

    @classmethod
    def set_follow_up(cls, db: Session, user_id: int, litter_group_id: int, payload: FollowUpUpdate) -> FollowUp:
        """
        Create or update the follow-up of a litter (« Suivre » starts it at « à appeler »).

        A reminder moved to another time is pushed again when that time comes.

        Args:
            db: Database session.
            user_id: The user.
            litter_group_id: The litter.
            payload: Status, reminder and last contact.

        Returns:
            The follow-up.
        """
        LitterQueryService.get_group(db, litter_group_id)
        follow_up = cls._find_follow_up(db, user_id, litter_group_id)
        if follow_up is None:
            follow_up = FollowUp(user_id=user_id, litter_group_id=litter_group_id)
            db.add(follow_up)
        next_reminder_at = cls._as_naive_utc(payload.next_reminder_at)
        if next_reminder_at != follow_up.next_reminder_at:
            follow_up.reminder_sent_at = None
        follow_up.status = payload.status
        follow_up.next_reminder_at = next_reminder_at
        follow_up.last_contact_at = cls._as_naive_utc(payload.last_contact_at)
        db.commit()
        return follow_up

    @classmethod
    def remove_follow_up(cls, db: Session, user_id: int, litter_group_id: int) -> None:
        """
        Stop following a litter: its status, reminder and notes are deleted. A litter not followed stays as it is.

        Args:
            db: Database session.
            user_id: The user.
            litter_group_id: The litter.
        """
        LitterQueryService.get_group(db, litter_group_id)
        follow_up = cls._find_follow_up(db, user_id, litter_group_id)
        if follow_up is None:
            return
        db.query(FollowUpNote).filter(FollowUpNote.follow_up_id == follow_up.id).delete()
        db.delete(follow_up)
        db.commit()

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
        follow_up = cls._find_follow_up(db, user_id, litter_group_id)
        if follow_up is None:
            follow_up = FollowUp(user_id=user_id, litter_group_id=litter_group_id)
            db.add(follow_up)
            db.flush()
        note = FollowUpNote(follow_up_id=follow_up.id, text=payload.text.strip(), created_at=naive_utc_now())
        db.add(note)
        db.commit()
        return note

    @classmethod
    def remove_note(cls, db: Session, user_id: int, litter_group_id: int, note_id: int) -> None:
        """
        Delete a note of the follow-up of a litter.

        Args:
            db: Database session.
            user_id: The user.
            litter_group_id: The litter.
            note_id: The note.

        Raises:
            HTTPException: 404 when the note is not one of this litter's follow-up.
        """
        follow_up = cls._find_follow_up(db, user_id, litter_group_id)
        note = db.get(FollowUpNote, note_id)
        if follow_up is None or note is None or note.follow_up_id != follow_up.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note introuvable")
        db.delete(note)
        db.commit()

    @staticmethod
    def record_visit(db: Session, user: User) -> datetime | None:
        """
        Record that the user looks at the home list now, on whatever device.

        Args:
            db: Database session.
            user: The user, loaded in this session.

        Returns:
            The previous look, naive UTC, or None on the first one.
        """
        previous_visit_at = user.litters_visited_at
        user.litters_visited_at = naive_utc_now()
        db.commit()
        return previous_visit_at

    @staticmethod
    def _find_follow_up(db: Session, user_id: int, litter_group_id: int) -> FollowUp | None:
        """
        The follow-up of a litter for the user, if the litter is followed.

        Args:
            db: Database session.
            user_id: The user.
            litter_group_id: The litter.

        Returns:
            The follow-up, or None.
        """
        return (
            db.query(FollowUp)
            .filter(FollowUp.user_id == user_id, FollowUp.litter_group_id == litter_group_id)
            .one_or_none()
        )

    @staticmethod
    def _as_naive_utc(moment: datetime | None) -> datetime | None:
        """
        A time sent by the dashboard, in the storage convention (naive UTC).

        Args:
            moment: Aware time, or naive already read as UTC.

        Returns:
            The naive UTC time, or None.
        """
        if moment is None or moment.tzinfo is None:
            return moment
        return moment.astimezone(UTC).replace(tzinfo=None)
