"""Re-evaluates every active litter for every active profile, stores the verdicts, raises the events."""

from dataclasses import dataclass, field
from datetime import datetime

from sqlalchemy.orm import Session

from core.clock import french_date_of
from enums.match_event_kind import MatchEventKind
from enums.match_tier import MatchTier
from models.follow_up import FollowUp
from models.listing_match import ListingMatch
from models.litter_group import LitterGroup
from models.search_profile import SearchProfile
from services.matching.criteria import ProfileCriteria
from services.matching.events import EventService
from services.matching.matching_service import MatchingService, MatchVerdict
from services.matching.snapshot_builder import LitterSnapshotBuilder
from services.notifier import notifier_service


@dataclass
class RefreshSummary:
    """What a refresh did."""

    evaluated_count: int = 0
    raised_events: list[tuple[int, MatchEventKind]] = field(default_factory=list)


class MatchRefreshService:
    """Keeps ``listing_matches`` in step with the litters and the profiles."""

    def refresh(
        self,
        db: Session,
        now: datetime,
        born_group_ids: set[int] | None = None,
        should_notify: bool = True,
        profile_ids: set[int] | None = None,
        fewer_puppies_group_ids: set[int] | None = None,
    ) -> RefreshSummary:
        """
        Evaluate every active group against every active profile.

        After a collection the events that are news are sent (``EventService.is_news``). After a change
        of criteria (``should_notify`` False) they are only recorded as handled: Léo is looking at the
        app, and a new setting must not push every litter it reclassifies.

        Args:
            db: Database session; committed at the end.
            now: Evaluation time, naive UTC.
            born_group_ids: Groups whose birth appeared during this run.
            should_notify: Whether the raised events are sent.
            profile_ids: Only these profiles (a new account); every active profile when None.
            fewer_puppies_group_ids: Groups that offer fewer puppies since the previous run.

        Returns:
            The summary.
        """
        summary = RefreshSummary()
        today = french_date_of(now)
        groups = db.query(LitterGroup).filter(LitterGroup.is_active.is_(True)).order_by(LitterGroup.id).all()
        profile_query = db.query(SearchProfile).filter(SearchProfile.is_active.is_(True))
        if profile_ids is not None:
            profile_query = profile_query.filter(SearchProfile.id.in_(profile_ids))
        profiles = profile_query.order_by(SearchProfile.id).all()
        just_born = born_group_ids or set()
        offering_fewer_puppies = fewer_puppies_group_ids or set()

        for profile in profiles:
            criteria = ProfileCriteria.from_profile(profile)
            followed_group_ids = {
                group_id
                for (group_id,) in db.query(FollowUp.litter_group_id).filter(FollowUp.user_id == profile.user_id)
            }
            for group in groups:
                snapshot = LitterSnapshotBuilder.build(db, group)
                if snapshot is None:
                    continue
                verdict = MatchingService.evaluate(snapshot, criteria, today)
                match = self._store_verdict(db, group.id, profile.id, verdict, now)
                previous_tier = match.tier if match.id is not None else None
                match.tier = verdict.tier
                summary.evaluated_count += 1

                is_followed = group.id in followed_group_ids
                events = EventService.detect(
                    previous_tier=previous_tier,
                    new_tier=verdict.tier,
                    notified_events=match.notified_events,
                    has_just_been_born=group.id in just_born,
                    is_followed=is_followed,
                    has_fewer_puppies_available=group.id in offering_fewer_puppies,
                )
                if not events:
                    continue
                events_to_send = [event for event in events if EventService.is_news(event, snapshot.appeared_on, today)]
                if should_notify and events_to_send:
                    notifier_service.dispatch(db, profile, snapshot, events_to_send, is_followed, now)
                handled = dict(match.notified_events)
                for event in events:
                    handled[event.value] = now.isoformat()
                    summary.raised_events.append((group.id, event))
                if MatchEventKind.BORN in events and verdict.tier == MatchTier.PREFERRED:
                    handled.setdefault(MatchEventKind.NEW_PREFERRED.value, now.isoformat())
                match.notified_events = handled
        db.commit()
        return summary

    @staticmethod
    def _store_verdict(
        db: Session, litter_group_id: int, profile_id: int, verdict: MatchVerdict, now: datetime
    ) -> ListingMatch:
        """
        Write score, reasons and flags on the match of a group, creating it if needed. The tier is
        left to the caller, who needs the previous one first.

        Args:
            db: Database session.
            litter_group_id: The group.
            profile_id: The profile.
            verdict: The new verdict.
            now: Evaluation time.

        Returns:
            The match; a new one has no id yet.
        """
        match = (
            db.query(ListingMatch)
            .filter(ListingMatch.litter_group_id == litter_group_id, ListingMatch.profile_id == profile_id)
            .one_or_none()
        )
        if match is None:
            match = ListingMatch(litter_group_id=litter_group_id, profile_id=profile_id, notified_events={})
            db.add(match)
        match.score = verdict.score
        match.reasons = [{"text": reason.text, "points": reason.points} for reason in verdict.reasons]
        match.flags = [flag.value for flag in verdict.flags]
        match.computed_at = now
        return match


match_refresh_service = MatchRefreshService()
