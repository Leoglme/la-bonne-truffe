"""
The alerts of the followed breeders (docs/04, « Les alertes d'éleveur »): a mating declared, a litter born, new
photos or a new ad on one of their litters, whatever the department and the tier of the litter.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from enums.breeder_event_kind import BreederEventKind
from enums.color_preference_level import ColorPreferenceLevel
from enums.listing_source import ListingSource
from enums.notification_kind import NotificationKind
from models.breeder import Breeder
from models.breeder_follow import BreederFollow, BreederFollowEvent
from models.listing import Listing
from models.listing_change import ListingChange
from models.litter_group import LitterGroup
from models.notification import Notification
from models.search_profile import SearchProfile
from services.matching.criteria import LitterSnapshot, ProfileCriteria
from services.matching.snapshot_builder import LitterSnapshotBuilder
from services.notification_texts import NotificationTexts
from services.notifier import notifier_service
from services.puppy_arrival_service import PuppyArrivalService

BREEDER_EVENT_NOTIFICATION_KINDS: dict[BreederEventKind, NotificationKind] = {
    BreederEventKind.NEW_MATING: NotificationKind.BREEDER_NEW_MATING,
    BreederEventKind.BIRTH: NotificationKind.BREEDER_BIRTH,
    BreederEventKind.NEW_PHOTOS: NotificationKind.BREEDER_NEW_PHOTOS,
    BreederEventKind.NEW_AD: NotificationKind.BREEDER_NEW_AD,
}
LITTER_PUSH_KINDS: frozenset[NotificationKind] = frozenset(
    {
        NotificationKind.NEW_PREFERRED,
        NotificationKind.BORN,
        NotificationKind.UPGRADED,
        *BREEDER_EVENT_NOTIFICATION_KINDS.values(),
    }
)
PHOTOS_FIELD = "photos"
NEW_PHOTOS_EVENT_REPEAT_DELAY = timedelta(days=1)


@dataclass
class BreederRunFacts:
    """What a run brought that a followed breeder's alerts are about."""

    new_group_ids: set[int] = field(default_factory=set)
    born_group_ids: set[int] = field(default_factory=set)
    new_listing_ids: list[int] = field(default_factory=list)
    changed_listing_ids: list[int] = field(default_factory=list)
    run_started_at: datetime | None = None
    first_site_read_breeder_ids: frozenset[int] = frozenset()


class BreederAlertService:
    """Raises the events of the followed breeders after a run, and pushes each one once."""

    def raise_events(self, db: Session, facts: BreederRunFacts, now: datetime, should_notify: bool) -> int:
        """
        Compare what the run brought with the breeders each user follows, and notify once per event.

        An event is recorded even when it is not sent (setting off, search paused, colour ignored, site of the
        breeder read for the first time, or the litter itself just pushed), so that it never comes back.

        Args:
            db: Database session; committed at the end.
            facts: What the run brought.
            now: Run time, naive UTC.
            should_notify: Whether anything is sent; the first run of a source records silently.

        Returns:
            Number of pushes sent.
        """
        follows = db.query(BreederFollow).all()
        if not follows:
            return 0
        candidate_group_ids = facts.new_group_ids | facts.born_group_ids
        photo_group_ids = self._groups_with_new_photos(db, facts)
        new_ad_sources = self._groups_with_new_ad(db, facts)
        new_ad_group_ids = set(new_ad_sources)
        candidate_group_ids |= photo_group_ids | new_ad_group_ids
        if not candidate_group_ids:
            return 0
        groups_by_breeder: dict[int, list[LitterGroup]] = {}
        for group in db.query(LitterGroup).filter(LitterGroup.id.in_(candidate_group_ids)):
            if group.breeder_id is not None:
                groups_by_breeder.setdefault(group.breeder_id, []).append(group)

        sent_count = 0
        for follow in follows:
            groups = groups_by_breeder.get(follow.breeder_id, [])
            if not groups:
                continue
            breeder = db.get(Breeder, follow.breeder_id)
            criteria = self._criteria_of(db, follow.user_id)
            is_paused = PuppyArrivalService.is_search_paused(db, follow.user_id)
            is_site_read_for_the_first_time = follow.breeder_id in facts.first_site_read_breeder_ids
            for group in sorted(groups, key=lambda candidate: candidate.id):
                snapshot = LitterSnapshotBuilder.build(db, group)
                if snapshot is None:
                    continue
                for kind in self._kinds_of(group, facts, photo_group_ids, new_ad_group_ids):
                    if self._is_handled(db, follow, group.id, kind, now):
                        continue
                    is_wanted = self._is_wanted(follow, kind, snapshot, criteria)
                    is_sent = False
                    if should_notify and is_wanted and not is_paused and not is_site_read_for_the_first_time:
                        new_ad_source = new_ad_sources.get(group.id)
                        is_sent = self._notify(db, follow, breeder, group, kind, snapshot, new_ad_source, now)
                    sent_count += int(is_sent)
                    db.add(
                        BreederFollowEvent(
                            follow_id=follow.id, litter_group_id=group.id, kind=kind, created_at=now, sent_at=now
                        )
                    )
        db.commit()
        return sent_count

    @classmethod
    def _groups_with_new_photos(cls, db: Session, facts: BreederRunFacts) -> set[int]:
        """
        The groups whose listings got a photo never seen on them before during the run: two sources that give the
        same ad different photos, in turn, bring nothing new.

        Args:
            db: Database session.
            facts: What the run brought.

        Returns:
            Group ids.
        """
        if not facts.changed_listing_ids or facts.run_started_at is None:
            return set()
        changed_listing_ids = {
            change.listing_id
            for change in db.query(ListingChange).filter(
                ListingChange.listing_id.in_(facts.changed_listing_ids),
                ListingChange.field == PHOTOS_FIELD,
                ListingChange.changed_at >= facts.run_started_at,
            )
            if cls._adds_unseen_photo(db, change)
        }
        if not changed_listing_ids:
            return set()
        return {
            group_id
            for (group_id,) in db.query(Listing.litter_group_id).filter(Listing.id.in_(changed_listing_ids))
            if group_id is not None
        }

    @staticmethod
    def _adds_unseen_photo(db: Session, change: ListingChange) -> bool:
        """
        Whether a change of the photos of a listing brings a photo the listing never had.

        Args:
            db: Database session.
            change: The change of the photos.

        Returns:
            True when one of its photos is new to the listing.
        """
        seen_photos = set(json.loads(change.old_value or "[]"))
        for earlier_change in db.query(ListingChange).filter(
            ListingChange.listing_id == change.listing_id,
            ListingChange.field == PHOTOS_FIELD,
            ListingChange.id < change.id,
        ):
            seen_photos |= set(json.loads(earlier_change.old_value or "[]"))
            seen_photos |= set(json.loads(earlier_change.new_value or "[]"))
        return bool(set(json.loads(change.new_value or "[]")) - seen_photos)

    @staticmethod
    def _groups_with_new_ad(db: Session, facts: BreederRunFacts) -> dict[int, ListingSource]:
        """
        The groups already known that gained a listing on another source during the run, with that source.

        Args:
            db: Database session.
            facts: What the run brought.

        Returns:
            The source of the new listing, by group id.
        """
        if not facts.new_listing_ids:
            return {}
        return {
            group_id: source
            for (group_id, source) in db.query(Listing.litter_group_id, Listing.source).filter(
                Listing.id.in_(facts.new_listing_ids)
            )
            if group_id is not None and group_id not in facts.new_group_ids
        }

    @staticmethod
    def _kinds_of(
        group: LitterGroup, facts: BreederRunFacts, photo_group_ids: set[int], new_ad_group_ids: set[int]
    ) -> list[BreederEventKind]:
        """
        The events a group raises for a followed breeder.

        Args:
            group: The group.
            facts: What the run brought.
            photo_group_ids: Groups with new photos.
            new_ad_group_ids: Groups with a new ad.

        Returns:
            The kinds, in a stable order.
        """
        kinds: list[BreederEventKind] = []
        if group.id in facts.born_group_ids:
            kinds.append(BreederEventKind.BIRTH)
        elif group.id in facts.new_group_ids:
            kinds.append(BreederEventKind.BIRTH if group.birth_date is not None else BreederEventKind.NEW_MATING)
        if group.id in photo_group_ids:
            kinds.append(BreederEventKind.NEW_PHOTOS)
        if group.id in new_ad_group_ids and BreederEventKind.NEW_PHOTOS not in kinds:
            kinds.append(BreederEventKind.NEW_AD)
        return kinds

    @staticmethod
    def _is_handled(db: Session, follow: BreederFollow, group_id: int, kind: BreederEventKind, now: datetime) -> bool:
        """
        Whether the event was already raised for this follow, this litter and this kind; new photos count
        again after a day.

        Args:
            db: Database session.
            follow: The follow.
            group_id: The group.
            kind: The event.
            now: Run time.

        Returns:
            True when nothing is to do.
        """
        existing = (
            db.query(BreederFollowEvent)
            .filter(
                BreederFollowEvent.follow_id == follow.id,
                BreederFollowEvent.litter_group_id == group_id,
                BreederFollowEvent.kind == kind,
            )
            .order_by(BreederFollowEvent.created_at.desc())
            .first()
        )
        if existing is None:
            return False
        if kind == BreederEventKind.NEW_PHOTOS:
            return now - existing.created_at < NEW_PHOTOS_EVENT_REPEAT_DELAY
        return True

    @staticmethod
    def _is_wanted(
        follow: BreederFollow, kind: BreederEventKind, snapshot: LitterSnapshot, criteria: ProfileCriteria | None
    ) -> bool:
        """
        Whether the follow asks for this event, and whether the litter's colours allow it. New ads and new photos
        of a litter all reserved or sold, such as one a breeder's site moved to its past litters, are not worth a push.

        Args:
            follow: The follow, with its settings.
            kind: The event.
            snapshot: The litter.
            criteria: The user's criteria, None without an active profile.

        Returns:
            True when the event is sent.
        """
        is_setting_on = {
            BreederEventKind.NEW_MATING: follow.notify_new_mating,
            BreederEventKind.BIRTH: follow.notify_birth,
            BreederEventKind.NEW_PHOTOS: follow.notify_new_photos,
            BreederEventKind.NEW_AD: follow.notify_new_photos,
        }[kind]
        if not is_setting_on:
            return False
        if kind in (BreederEventKind.NEW_AD, BreederEventKind.NEW_PHOTOS) and snapshot.puppies_available == 0:
            return False
        if follow.notify_ignored_colors or criteria is None or not snapshot.has_certain_colors:
            return True
        return any(criteria.level_of(reading.color) != ColorPreferenceLevel.IGNORED for reading in snapshot.colors)

    def _notify(
        self,
        db: Session,
        follow: BreederFollow,
        breeder: Breeder | None,
        group: LitterGroup,
        kind: BreederEventKind,
        snapshot: LitterSnapshot,
        new_ad_source: ListingSource | None,
        now: datetime,
    ) -> bool:
        """
        Push an event, unless the litter was already pushed in this run, for itself or for its breeder.

        Args:
            db: Database session.
            follow: The follow.
            breeder: The followed breeder.
            group: The litter.
            kind: The event.
            snapshot: The litter.
            new_ad_source: Where the new ad of the litter appeared, for a new ad.
            now: Run time.

        Returns:
            Whether a push went out.
        """
        if self._was_litter_just_pushed(db, follow.user_id, group.id, now):
            return False
        breeder_name = (breeder.card_name if breeder is not None else None) or snapshot.name
        notifier_service.send(
            db,
            user_id=follow.user_id,
            kind=BREEDER_EVENT_NOTIFICATION_KINDS[kind],
            title=NotificationTexts.breeder_event_title(kind, breeder_name),
            body=NotificationTexts.breeder_event(kind, snapshot, new_ad_source),
            litter_group_id=group.id,
            now=now,
        )
        return True

    @staticmethod
    def _was_litter_just_pushed(db: Session, user_id: int, group_id: int, now: datetime) -> bool:
        """
        Whether a notification about this litter went out in the same run, for itself or for its breeder: one
        notification then suffices.

        Args:
            db: Database session.
            user_id: The user.
            group_id: The group.
            now: Run time, the ``sent_at`` of the pushes of this run.

        Returns:
            True when the litter was pushed.
        """
        return (
            db.query(Notification)
            .filter(
                Notification.user_id == user_id,
                Notification.litter_group_id == group_id,
                Notification.sent_at == now,
                Notification.kind.in_(LITTER_PUSH_KINDS),
            )
            .first()
            is not None
        )

    @staticmethod
    def _criteria_of(db: Session, user_id: int) -> ProfileCriteria | None:
        """
        The criteria of the user's first active profile.

        Args:
            db: Database session.
            user_id: The user.

        Returns:
            The criteria, or None without an active profile.
        """
        profile = (
            db.query(SearchProfile)
            .filter(SearchProfile.user_id == user_id, SearchProfile.is_active.is_(True))
            .order_by(SearchProfile.id)
            .first()
        )
        return ProfileCriteria.from_profile(profile) if profile is not None else None


breeder_alert_service = BreederAlertService()
