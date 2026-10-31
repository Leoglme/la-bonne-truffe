"""PuppyArrivalService: the puppy found pauses the search and keeps the list of what to prepare."""

from datetime import date, datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models.digest_entry import DigestEntry
from models.puppy_arrival import PuppyArrival
from schemas.puppy_arrival import PuppyArrivalResponse
from services.litter_query_service import LitterQueryService


class PuppyArrivalService:
    """Starts, follows and ends the « chiot trouvé » mode of a user."""

    @staticmethod
    def current(db: Session, user_id: int) -> PuppyArrival | None:
        """
        The puppy the user found, if any.

        Args:
            db: Database session.
            user_id: The user.

        Returns:
            The arrival, or None while the search goes on.
        """
        return db.query(PuppyArrival).filter(PuppyArrival.user_id == user_id).one_or_none()

    @staticmethod
    def is_search_paused(db: Session, user_id: int) -> bool:
        """
        Whether the litter alerts of the user wait: they found their puppy.

        Args:
            db: Database session.
            user_id: The user.

        Returns:
            True while a puppy arrival exists.
        """
        return db.query(PuppyArrival.id).filter(PuppyArrival.user_id == user_id).first() is not None

    @classmethod
    def start(
        cls, db: Session, user_id: int, litter_group_id: int, arrival_on: date, now: datetime
    ) -> PuppyArrivalResponse:
        """
        Pause the search on the puppy found; a second « C’est lui ! » changes the litter or the day, not the ticks.

        The litters queued for the evening digest are dropped: the search is over.

        Args:
            db: Database session.
            user_id: The user.
            litter_group_id: Litter of the puppy.
            arrival_on: Day the puppy comes home.
            now: Pause time, naive UTC.

        Returns:
            The arrival.

        Raises:
            HTTPException: 404 when the litter does not exist.
        """
        LitterQueryService.get_group(db, litter_group_id)
        arrival = cls.current(db, user_id)
        if arrival is None:
            arrival = PuppyArrival(user_id=user_id, done_items=[], created_at=now)
            db.add(arrival)
        arrival.litter_group_id = litter_group_id
        arrival.arrival_on = arrival_on
        db.query(DigestEntry).filter(DigestEntry.user_id == user_id, DigestEntry.sent_at.is_(None)).delete()
        db.commit()
        return cls.to_response(arrival)

    @classmethod
    def update_checklist(cls, db: Session, user_id: int, done_items: list[str]) -> PuppyArrivalResponse:
        """
        Keep the preparations ticked.

        Args:
            db: Database session.
            user_id: The user.
            done_items: Keys of the preparations ticked; a key given twice counts once.

        Returns:
            The arrival.

        Raises:
            HTTPException: 404 while no puppy was found.
        """
        arrival = cls.current(db, user_id)
        if arrival is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Aucun chiot trouvé pour l’instant.")
        arrival.done_items = list(dict.fromkeys(done_items))
        db.commit()
        return cls.to_response(arrival)

    @classmethod
    def resume_search(cls, db: Session, user_id: int) -> None:
        """
        End the « chiot trouvé » mode: the alerts go out again, for the litters that appear from now on.

        Args:
            db: Database session.
            user_id: The user.
        """
        arrival = cls.current(db, user_id)
        if arrival is not None:
            db.delete(arrival)
            db.commit()

    @staticmethod
    def to_response(arrival: PuppyArrival) -> PuppyArrivalResponse:
        """
        The arrival as the API returns it.

        Args:
            arrival: The stored arrival.

        Returns:
            Its payload.
        """
        return PuppyArrivalResponse(
            litter_group_id=arrival.litter_group_id,
            arrival_on=arrival.arrival_on,
            done_items=list(arrival.done_items),
            paused_since=arrival.created_at,
        )
