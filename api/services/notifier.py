"""
Sends the notifications: immediate pushes, the evening digest, follow-up reminders, and the alerts of a source
that fails or that nobody relays any more.
"""

import logging
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from core.clock import to_french_time
from enums.follow_up_status import FollowUpStatus
from enums.listing_source import ListingSource
from enums.match_event_kind import MatchEventKind
from enums.notification_kind import NotificationKind
from enums.source_run_status import SourceRunStatus
from models.digest_entry import DigestEntry
from models.follow_up import FollowUp
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

# Time without a successful run of a source the Windows app relays before Léo is told (docs/04).
SILENCE_BEFORE_ALERT = timedelta(hours=3)

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
        if self._has_alerted_since(db, NotificationKind.SOURCE_DOWN, source, outage_start):
            return False

        body = NotificationTexts.source_down(source, FAILED_RUNS_BEFORE_ALERT, last_runs[0].error_message)
        self._alert_every_user(db, NotificationKind.SOURCE_DOWN, body, now)
        logger.warning("Source %s down: alert sent", source)
        return True

    def alert_if_source_silent(self, db: Session, source: ListingSource, now: datetime) -> bool:
        """
        Tell every user once per silence when a source has had no successful run for ``SILENCE_BEFORE_ALERT``.

        Meant for the sources the Windows app relays: their runs are not scheduled here, so a computer that
        is off or an app that is signed out leaves no failed run behind, only silence. The next successful
        run ends the silence; a new one is alerted again.

        Args:
            db: Database session; committed when an alert is sent.
            source: The source to check.
            now: Current time, naive UTC.

        Returns:
            Whether an alert was sent.
        """
        last_success = (
            db.query(SourceRun)
            .filter(SourceRun.source == source, SourceRun.status == SourceRunStatus.OK)
            .order_by(SourceRun.started_at.desc(), SourceRun.id.desc())
            .first()
        )
        last_success_at = (last_success.finished_at or last_success.started_at) if last_success is not None else None
        if last_success_at is not None and last_success_at > now - SILENCE_BEFORE_ALERT:
            return False
        if self._has_alerted_since(db, NotificationKind.SOURCE_SILENT, source, last_success_at):
            return False

        silent_hours = int(SILENCE_BEFORE_ALERT.total_seconds() // 3600)
        body = NotificationTexts.source_silent(source, silent_hours)
        self._alert_every_user(db, NotificationKind.SOURCE_SILENT, body, now)
        logger.warning("Source %s silent: alert sent", source)
        return True

    def send_due_follow_up_reminders(self, db: Session, now: datetime) -> int:
        """
        Push every follow-up reminder whose time has come, once; a dismissed litter is not reminded.

        Args:
            db: Database session; committed when a reminder is sent.
            now: Current time, naive UTC.

        Returns:
            Number of reminders sent.
        """
        due_follow_ups = (
            db.query(FollowUp)
            .filter(
                FollowUp.next_reminder_at.is_not(None),
                FollowUp.next_reminder_at <= now,
                FollowUp.reminder_sent_at.is_(None),
                FollowUp.status != FollowUpStatus.DISMISSED,
            )
            .all()
        )
        for follow_up in due_follow_ups:
            group = db.get(LitterGroup, follow_up.litter_group_id)
            snapshot = LitterSnapshotBuilder.build(db, group) if group is not None else None
            self.send(
                db,
                user_id=follow_up.user_id,
                kind=NotificationKind.FOLLOW_UP_REMINDER,
                body=NotificationTexts.follow_up_reminder(snapshot.name if snapshot is not None else None),
                litter_group_id=follow_up.litter_group_id,
                now=now,
            )
            follow_up.reminder_sent_at = now
        db.commit()
        return len(due_follow_ups)

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

    @staticmethod
    def _has_alerted_since(db: Session, kind: NotificationKind, source: ListingSource, since: datetime | None) -> bool:
        """
        Whether an alert of that kind about a source was already sent after a moment.

        Args:
            db: Database session.
            kind: Kind of alert.
            source: The source; the alert body starts with its name (``NotificationTexts``).
            since: Start of the outage or of the silence; None looks at every alert ever sent.

        Returns:
            True when such an alert exists.
        """
        alerts = db.query(Notification).filter(
            Notification.kind == kind, Notification.body.startswith(SOURCE_NAMES[source])
        )
        if since is not None:
            alerts = alerts.filter(Notification.sent_at > since)
        return alerts.first() is not None

    def _alert_every_user(self, db: Session, kind: NotificationKind, body: str, now: datetime) -> None:
        """
        Push an alert to every active user and keep it in their bell history.

        Args:
            db: Database session; committed.
            kind: Kind of alert.
            body: The sentence.
            now: Sending time, naive UTC.
        """
        for (user_id,) in db.query(User.id).filter(User.is_active.is_(True)):
            self.send(db, user_id=user_id, kind=kind, body=body, litter_group_id=None, now=now)
        db.commit()


notifier_service = NotifierService()
