"""Changes the user makes on a breeder: creation by hand, links, follow, notes. Every write is scoped to the user."""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from core.clock import naive_utc_now, naive_utc_of
from models.breeder import Breeder
from models.breeder_follow import BreederFollow, BreederFollowNote
from models.department import Department
from models.user import User
from schemas.breeder import BreederCreate, BreederFollowNoteCreate, BreederFollowUpdate, BreederUpdate
from services.breeder_matcher import BreederMatcher
from services.breeder_query_service import BreederQueryService
from services.breeder_search_text import BreederSearchText
from services.collectors.breeder_contact_parser import BreederContactParser


class BreederCommandService:
    """Writes what Léo learned or decided about a breeder."""

    @classmethod
    def create_manual(cls, db: Session, user: User, payload: BreederCreate) -> Breeder:
        """
        Add a breeder by hand, or complete the one the phone, or the affix in the department, already names.

        Args:
            db: Database session; committed.
            user: The user adding it.
            payload: Name, place, links, phone, note.

        Returns:
            The breeder, followed when asked.
        """
        phone_e164 = BreederContactParser.phone_e164(payload.phone)
        zip_code = BreederContactParser.postal_code(payload.zip_code)
        department_code = BreederContactParser.department_code(zip_code)
        if department_code is not None and db.get(Department, department_code) is None:
            department_code = None
        affix = BreederContactParser.affix_of_breeding_name(payload.display_name)
        affix_key = BreederContactParser.affix_key(affix)
        breeder = BreederMatcher.find(
            db,
            siren=None,
            scc_breeder_id=None,
            phone_e164=phone_e164,
            affix_key=affix_key,
            department_code=department_code,
        )
        if breeder is None:
            breeder = Breeder(is_manual=True, created_by_user_id=user.id)
            db.add(breeder)
            breeder.display_name = payload.display_name.strip()
            breeder.affix = affix
            breeder.affix_normalized = affix_key
        breeder.phone_e164 = phone_e164 or breeder.phone_e164
        breeder.zip_code = zip_code or breeder.zip_code
        breeder.city = BreederContactParser.readable_name(payload.city) or breeder.city
        breeder.department_code = department_code or breeder.department_code
        if payload.links:
            breeder.links = cls._merged_links(breeder.links or [], [link.model_dump() for link in payload.links])
        if payload.notes:
            breeder.notes = payload.notes.strip() if not breeder.notes else f"{breeder.notes}\n{payload.notes.strip()}"
        breeder.search_text = BreederSearchText.build(breeder)
        db.commit()
        if payload.follow:
            cls.set_follow(db, user.id, breeder.id, BreederFollowUpdate())
        return breeder

    @staticmethod
    def update(db: Session, breeder_id: int, payload: BreederUpdate) -> Breeder:
        """
        Change the links, the phone, the site or the notes of a breeder.

        Args:
            db: Database session; committed.
            breeder_id: The breeder.
            payload: What changes; a field left out stays as it is.

        Returns:
            The breeder.
        """
        breeder = BreederQueryService.get_breeder(db, breeder_id)
        if payload.links is not None:
            breeder.links = [link.model_dump() for link in payload.links]
        if payload.phone is not None:
            breeder.phone_e164 = BreederContactParser.phone_e164(payload.phone) or breeder.phone_e164
        if payload.website is not None:
            breeder.website = payload.website.strip() or None
        if payload.notes is not None:
            breeder.notes = payload.notes.strip() or None
        breeder.search_text = BreederSearchText.build(breeder)
        db.commit()
        return breeder

    @classmethod
    def set_follow(cls, db: Session, user_id: int, breeder_id: int, payload: BreederFollowUpdate) -> BreederFollow:
        """
        Follow a breeder, or change its alerts, its status and its reminder.

        A reminder moved to another time is pushed again when that time comes.

        Args:
            db: Database session; committed.
            user_id: The user.
            breeder_id: The breeder.
            payload: Settings, status, reminder and last contact.

        Returns:
            The follow.
        """
        BreederQueryService.get_breeder(db, breeder_id)
        follow = cls._find_follow(db, user_id, breeder_id)
        if follow is None:
            follow = BreederFollow(user_id=user_id, breeder_id=breeder_id)
            db.add(follow)
        next_reminder_at = naive_utc_of(payload.next_reminder_at)
        if next_reminder_at != follow.next_reminder_at:
            follow.reminder_sent_at = None
        follow.status = payload.status
        follow.notify_new_mating = payload.notify_new_mating
        follow.notify_birth = payload.notify_birth
        follow.notify_new_photos = payload.notify_new_photos
        follow.notify_ignored_colors = payload.notify_ignored_colors
        follow.next_reminder_at = next_reminder_at
        follow.last_contact_at = naive_utc_of(payload.last_contact_at)
        db.commit()
        return follow

    @classmethod
    def remove_follow(cls, db: Session, user_id: int, breeder_id: int) -> None:
        """
        Stop following a breeder: its settings, status, reminder, notes and handled events are deleted.

        Args:
            db: Database session; committed.
            user_id: The user.
            breeder_id: The breeder.
        """
        BreederQueryService.get_breeder(db, breeder_id)
        follow = cls._find_follow(db, user_id, breeder_id)
        if follow is None:
            return
        db.delete(follow)
        db.commit()

    @classmethod
    def add_note(
        cls, db: Session, user_id: int, breeder_id: int, payload: BreederFollowNoteCreate
    ) -> BreederFollowNote:
        """
        Add a dated note; a breeder not followed yet starts being followed.

        Args:
            db: Database session; committed.
            user_id: The user.
            breeder_id: The breeder.
            payload: The note.

        Returns:
            The note.
        """
        BreederQueryService.get_breeder(db, breeder_id)
        follow = cls._find_follow(db, user_id, breeder_id)
        if follow is None:
            follow = BreederFollow(user_id=user_id, breeder_id=breeder_id)
            db.add(follow)
            db.flush()
        note = BreederFollowNote(follow_id=follow.id, text=payload.text.strip(), created_at=naive_utc_now())
        db.add(note)
        db.commit()
        return note

    @classmethod
    def remove_note(cls, db: Session, user_id: int, breeder_id: int, note_id: int) -> None:
        """
        Delete a note of a followed breeder.

        Args:
            db: Database session; committed.
            user_id: The user.
            breeder_id: The breeder.
            note_id: The note.

        Raises:
            HTTPException: 404 when the note is not one of this breeder's follow.
        """
        follow = cls._find_follow(db, user_id, breeder_id)
        note = db.get(BreederFollowNote, note_id)
        if follow is None or note is None or note.follow_id != follow.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note introuvable")
        db.delete(note)
        db.commit()

    @staticmethod
    def _find_follow(db: Session, user_id: int, breeder_id: int) -> BreederFollow | None:
        """
        The follow of a breeder for the user, if followed.

        Args:
            db: Database session.
            user_id: The user.
            breeder_id: The breeder.

        Returns:
            The follow, or None.
        """
        return (
            db.query(BreederFollow)
            .filter(BreederFollow.user_id == user_id, BreederFollow.breeder_id == breeder_id)
            .one_or_none()
        )

    @staticmethod
    def _merged_links(current: list[dict[str, str]], added: list[dict[str, str]]) -> list[dict[str, str]]:
        """
        The links of a breeder with new ones added, each URL once.

        Args:
            current: Links stored.
            added: Links to add.

        Returns:
            The merged links.
        """
        by_url: dict[str, dict[str, str]] = {link["url"]: link for link in current if link.get("url")}
        for link in added:
            by_url.setdefault(link["url"], link)
        return list(by_url.values())
