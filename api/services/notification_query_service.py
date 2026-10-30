"""Reads the notification history for the bell: each notification with the litters it is about."""

from sqlalchemy.orm import Session

from enums.match_event_kind import MatchEventKind
from models.notification import Notification
from schemas.notification import NotificationListResponse, NotificationLitter, NotificationResponse
from services.litter_query_service import LitterQueryService


class NotificationQueryService:
    """Lists the notifications of a user, newest first, with their litters and the unread count."""

    @classmethod
    def list_history(cls, db: Session, user_id: int, limit: int, before: int | None) -> NotificationListResponse:
        """
        Read a page of the history of a user.

        Args:
            db: Database session.
            user_id: The user.
            limit: Page size.
            before: Only the notifications whose id is strictly below this one, for « voir plus ».

        Returns:
            The page and the unread count.
        """
        query = db.query(Notification).filter(Notification.user_id == user_id)
        if before is not None:
            query = query.filter(Notification.id < before)
        rows = query.order_by(Notification.id.desc()).limit(limit).all()
        unread_count = (
            db.query(Notification).filter(Notification.user_id == user_id, Notification.read_at.is_(None)).count()
        )
        litters = LitterQueryService.list_notification_litters(db, user_id, cls._litter_group_ids_of(rows))
        return NotificationListResponse(
            items=[cls._with_litters(row, litters) for row in rows],
            unread_count=unread_count,
        )

    @staticmethod
    def _litter_group_ids_of(rows: list[Notification]) -> set[int]:
        """
        Every litter the notifications of a page are about.

        Args:
            rows: The notifications.

        Returns:
            The group ids, from the single litter and the digest litters.
        """
        group_ids: set[int] = {row.litter_group_id for row in rows if row.litter_group_id is not None}
        for row in rows:
            group_ids.update(entry["litter_group_id"] for entry in row.digest_litters)
        return group_ids

    @staticmethod
    def _with_litters(row: Notification, litters: dict[int, NotificationLitter]) -> NotificationResponse:
        """
        The payload of a notification, with its litter and, for a digest, its litters with their event.

        Args:
            row: The stored notification.
            litters: The litters of the page, by group id.

        Returns:
            The payload.
        """
        digest_litters: list[NotificationLitter] = []
        for entry in row.digest_litters:
            litter = litters.get(entry["litter_group_id"])
            if litter is not None:
                digest_litters.append(litter.model_copy(update={"digest_event": MatchEventKind(entry["event"])}))
        return NotificationResponse(
            id=row.id,
            kind=row.kind,
            title=row.title,
            body=row.body,
            url=row.url,
            litter_group_id=row.litter_group_id,
            sent_at=row.sent_at,
            read_at=row.read_at,
            litter=litters.get(row.litter_group_id) if row.litter_group_id is not None else None,
            litters=digest_litters,
        )


notification_query_service = NotificationQueryService()
