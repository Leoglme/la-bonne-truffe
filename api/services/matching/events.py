"""Which events a new verdict raises (docs/04, « Les événements qui notifient »)."""

from datetime import date

from enums.match_event_kind import MatchEventKind
from enums.match_tier import MatchTier

NEWS_WINDOW_DAYS = 3

ALWAYS_NEWS_EVENTS: frozenset[MatchEventKind] = frozenset(
    {MatchEventKind.BORN, MatchEventKind.UPGRADED, MatchEventKind.AVAILABILITY_CHANGE}
)


class EventService:
    """
    Compares the previous and the new verdict of a group; each (group, event) is raised once, except a drop of
    the puppies left on a followed litter, raised at every drop whatever the tier of the litter.
    """

    @staticmethod
    def detect(
        previous_tier: MatchTier | None,
        new_tier: MatchTier,
        notified_events: dict[str, str],
        has_just_been_born: bool,
        is_followed: bool,
        has_fewer_puppies_available: bool = False,
    ) -> list[MatchEventKind]:
        """
        Raise the events of a group for one profile.

        A birth carries the news by itself: when a litter is born and enters « préférée » in the same
        run, only ``born`` is raised (the other events are then recorded as notified by the caller).

        Args:
            previous_tier: Tier before this evaluation, None for a group never evaluated.
            new_tier: Tier now.
            notified_events: Events already notified for this group and profile.
            has_just_been_born: Whether the litter went from « à naître » to « née » during this run.
            is_followed: Whether the litter is in the user's follow-ups.
            has_fewer_puppies_available: Whether the litter offers fewer puppies than before this run.

        Returns:
            The events to notify, possibly none.
        """
        events: list[MatchEventKind] = []
        is_birth_worth_telling = new_tier == MatchTier.PREFERRED or (is_followed and new_tier != MatchTier.EXCLUDED)
        if has_just_been_born and MatchEventKind.BORN not in notified_events and is_birth_worth_telling:
            return [MatchEventKind.BORN]

        was_ever_preferred = (
            MatchEventKind.NEW_PREFERRED in notified_events or MatchEventKind.UPGRADED in notified_events
        )
        if new_tier == MatchTier.PREFERRED and not was_ever_preferred:
            if previous_tier == MatchTier.ACCEPTABLE:
                events.append(MatchEventKind.UPGRADED)
            else:
                events.append(MatchEventKind.NEW_PREFERRED)
        if (
            new_tier == MatchTier.ACCEPTABLE
            and previous_tier not in (MatchTier.ACCEPTABLE, MatchTier.PREFERRED)
            and MatchEventKind.NEW_ACCEPTABLE not in notified_events
            and not was_ever_preferred
        ):
            events.append(MatchEventKind.NEW_ACCEPTABLE)
        if has_fewer_puppies_available and is_followed:
            events.append(MatchEventKind.AVAILABILITY_CHANGE)
        return events

    @staticmethod
    def is_news(event: MatchEventKind, appeared_on: date, today: date) -> bool:
        """
        Whether an event is worth a push or a line in the digest.

        A birth or a move up to « préférée » always is. A new litter is only when it went online in the
        last few days: one online for weeks is recorded silently, so the first collection does not push
        every litter already published.

        Args:
            event: The event.
            appeared_on: Day the litter went online.
            today: Day of the evaluation, in French time.

        Returns:
            True when the event is sent.
        """
        if event in ALWAYS_NEWS_EVENTS:
            return True
        return (today - appeared_on).days <= NEWS_WINDOW_DAYS
