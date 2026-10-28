"""Sends the notifications: immediate pushes, the evening digest, and the « source en panne » alert."""

import logging
from datetime import datetime

from sqlalchemy.orm import Session

from core.clock import to_french_time
from enums.listing_source import ListingSource
from enums.match_event_kind import MatchEventKind
from enums.notification_kind import NotificationKind
from enums.source_run_status import SourceRunStatus
from models.digest_entry import DigestEntry
from models.litter_group import LitterGroup
from models.notification import Notification
from models.search_profile import SearchProfile
from models.source_run import SourceRun
from models.user import User
from services.matching.criteria import LitterSnapshot
from services.matching.snapshot_builder import LitterSnapshotBuilder
from services.notification_texts import NOTIFICATION_TITLE, SOURCE_NAMES, NotificationTexts
from services.push_service import push_service

logger = logging.getLogger(__name__)

# Consecutive failed runs of a source before Léo is told (docs/02, « Politesse et robustesse »).
FAILED_RUNS_BEFORE_ALERT = 3

IMMEDIATE_EVENT_KINDS: dict[MatchEventKind, NotificationKind] = {
    MatchEventKind.NEW_PREFERRED: NotificationKind.NEW_PREFERRED,
    MatchEventKind.BORN: NotificationKind.BORN,
    MatchEventKind.UPGRADED: NotificationKind.UPGRADED,
}

DIGEST_EVENT_KINDS: frozenset[MatchEventKind] = frozenset(
    {MatchEventKind.NEW_ACCEPTABLE, MatchEventKind.AVAILABILITY_CHANGE}
)


class NotifierService:
    """Turns events into pushes and history rows; a push failure never stops a run."""

    def dispatch(
        self,
        db: Session,
        profile: SearchProfile,
        snapshot: LitterSnapshot,
        events: list[MatchEventKind],
        is_followed: bool,
        now: datetime,
    ) -> list[MatchEventKind]:
        """
        Send or queue each event, as the profile asks.

        A preferred litter is pushed right away, a birth too; an acceptable litter, or a followed one
        offering fewer puppies, waits for the evening digest. An event the profile turned off is still
        recorded as handled, so turning the setting back on later never floods the phone with old litters.

        Args:
            db: Database session; the caller commits.
            profile: Profile the events were raised for.
            snapshot: The litter.
            events: Events raised for the litter.
            is_followed: Whether the litter is in the follow-ups.
            now: Run time, naive UTC.

        Returns:
            The events handled, to record in ``ListingMatch.notified_events``.
        """
        for event in events:
            if event in DIGEST_EVENT_KINDS:
                if profile.notify_acceptable_in_digest:
                    self._queue_for_digest(db, profile.user_id, snapshot.group_id, event, now)
                continue
            is_wanted = profile.notify_preferred_immediately
            if event == MatchEventKind.BORN and is_followed:
                is_wanted = is_wanted or profile.notify_birth_of_followed
            if is_wanted:
                self.send(
                    db,
                    user_id=profile.user_id,
                    kind=IMMEDIATE_EVENT_KINDS[event],
                    body=NotificationTexts.litter_event(event, snapshot),
                    litter_group_id=snapshot.group_id,
                    now=now,
                )
        return events

    def send(
        self,
        db: Session,
        user_id: int,
        kind: NotificationKind,
        body: str,
        litter_group_id: int | None,
        now: datetime,
    ) -> Notification:
        """
        Push one notification to every device of the user and keep it in the bell history.

        Args:
            db: Database session; the caller commits.
            user_id: Recipient.
            kind: Kind of notification.
            body: The sentence.
            litter_group_id: Litter the notification opens, if any.
            now: Sending time, naive UTC.

        Returns:
            The stored notification, with its delivery counts.
        """
        url = f"/portees/{litter_group_id}" if litter_group_id is not None else "/"
        result = push_service.send(db, user_id, NOTIFICATION_TITLE, body, url, tag=f"{kind}-{litter_group_id}")
        notification = Notification(
            user_id=user_id,
            kind=kind,
            title=NOTIFICATION_TITLE,
            body=body,
            url=url,
            litter_group_id=litter_group_id,
            sent_at=now,
            delivered_count=result.delivered,
            failed_count=result.failed,
        )
        db.add(notification)
        db.flush()
        return notification

    def send_due_evening_digests(self, db: Session, now: datetime) -> int:
        """
        Send the evening digest of every profile whose ``digest_hour`` is the current French hour.
        A digest is sent only when it holds at least one litter still active.

        Args:
            db: Database session; committed at the end.
            now: Current time, naive UTC.

        Returns:
            Number of digests sent.
        """
        current_hour = to_french_time(now).hour
        profiles = (
            db.query(SearchProfile)
            .filter(
                SearchProfile.is_active.is_(True),
                SearchProfile.notify_acceptable_in_digest.is_(True),
                SearchProfile.digest_hour == current_hour,
            )
            .all()
        )
        sent_count = 0
        for user_id in sorted({profile.user_id for profile in profiles}):
            entries = (
                db.query(DigestEntry)
                .filter(DigestEntry.user_id == user_id, DigestEntry.sent_at.is_(None))
                .order_by(DigestEntry.id)
                .all()
            )
            acceptable_snapshots: list[LitterSnapshot] = []
            followed_with_fewer_puppies: list[LitterSnapshot] = []
            for entry in entries:
                group = db.get(LitterGroup, entry.litter_group_id)
                snapshot = LitterSnapshotBuilder.build(db, group) if group is not None and group.is_active else None
                entry.sent_at = now
                if snapshot is None:
                    continue
                if entry.event_kind != MatchEventKind.AVAILABILITY_CHANGE:
                    acceptable_snapshots.append(snapshot)
                elif snapshot.puppies_available is not None:
                    followed_with_fewer_puppies.append(snapshot)
            litter_group_ids = {snapshot.group_id for snapshot in [*acceptable_snapshots, *followed_with_fewer_puppies]}
            if litter_group_ids:
                self.send(
                    db,
                    user_id=user_id,
                    kind=NotificationKind.EVENING_DIGEST,
                    body=NotificationTexts.evening_digest(acceptable_snapshots, followed_with_fewer_puppies),
                    litter_group_id=next(iter(litter_group_ids)) if len(litter_group_ids) == 1 else None,
                    now=now,
                )
                sent_count += 1
        db.commit()
        return sent_count

    def alert_if_source_down(self, db: Session, source: ListingSource, now: datetime) -> bool:
        """
        Tell every user once per outage when a source failed its last three runs.

        Args:
            db: Database session; committed when an alert is sent.
            source: The source whose run just failed.
            now: Current time, naive UTC.

        Returns:
            Whether an alert was sent.
        """
        last_runs = (
            db.query(SourceRun)
            .filter(SourceRun.source == source, SourceRun.status != SourceRunStatus.RUNNING)
            .order_by(SourceRun.started_at.desc(), SourceRun.id.desc())
            .limit(FAILED_RUNS_BEFORE_ALERT)
            .all()
        )
        if len(last_runs) < FAILED_RUNS_BEFORE_ALERT or any(run.status != SourceRunStatus.ERROR for run in last_runs):
            return False
        last_success = (
            db.query(SourceRun)
            .filter(SourceRun.source == source, SourceRun.status == SourceRunStatus.OK)
            .order_by(SourceRun.started_at.desc())
            .first()
        )
        outage_start = last_success.finished_at if last_success is not None else None
        already_alerted = db.query(Notification).filter(
            Notification.kind == NotificationKind.SOURCE_DOWN,
            # The alert body starts with the source name (NotificationTexts.source_down).
            Notification.body.startswith(SOURCE_NAMES[source]),
        )
        if outage_start is not None:
            already_alerted = already_alerted.filter(Notification.sent_at > outage_start)
        if already_alerted.first() is not None:
            return False

        body = NotificationTexts.source_down(source, FAILED_RUNS_BEFORE_ALERT, last_runs[0].error_message)
        for (user_id,) in db.query(User.id).filter(User.is_active.is_(True)):
            self.send(db, user_id=user_id, kind=NotificationKind.SOURCE_DOWN, body=body, litter_group_id=None, now=now)
        db.commit()
        logger.warning("Source %s down: alert sent", source)
        return True

    @staticmethod
    def _queue_for_digest(
        db: Session, user_id: int, litter_group_id: int, event: MatchEventKind, now: datetime
    ) -> None:
        """
        Keep an event for the evening digest: a new acceptable litter once, a drop of the puppies left at every
        drop. The table keeps one entry per litter and event, so an entry already sent goes back in the queue.

        Args:
            db: Database session.
            user_id: Recipient.
            litter_group_id: The litter.
            event: The event.
            now: Run time, naive UTC.
        """
        entry = (
            db.query(DigestEntry)
            .filter(
                DigestEntry.user_id == user_id,
                DigestEntry.litter_group_id == litter_group_id,
                DigestEntry.event_kind == event,
            )
            .first()
        )
        if entry is None:
            db.add(DigestEntry(user_id=user_id, litter_group_id=litter_group_id, event_kind=event, created_at=now))
        elif event == MatchEventKind.AVAILABILITY_CHANGE and entry.sent_at is not None:
            entry.sent_at = None
            entry.created_at = now


notifier_service = NotifierService()
