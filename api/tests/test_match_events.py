"""EventService: which events a new verdict raises, once each."""

from enums.match_event_kind import MatchEventKind
from enums.match_tier import MatchTier
from services.matching.events import EventService


def test_first_preferred_verdict_raises_new_preferred() -> None:
    events = EventService.detect(None, MatchTier.PREFERRED, {}, has_just_been_born=False, is_followed=False)

    assert events == [MatchEventKind.NEW_PREFERRED]


def test_acceptable_becoming_preferred_raises_upgraded() -> None:
    events = EventService.detect(
        MatchTier.ACCEPTABLE, MatchTier.PREFERRED, {"new_acceptable": "x"}, has_just_been_born=False, is_followed=False
    )

    assert events == [MatchEventKind.UPGRADED]


def test_new_acceptable_goes_to_the_digest_once() -> None:
    first = EventService.detect(None, MatchTier.ACCEPTABLE, {}, has_just_been_born=False, is_followed=False)
    again = EventService.detect(
        MatchTier.ACCEPTABLE, MatchTier.ACCEPTABLE, {"new_acceptable": "x"}, has_just_been_born=False, is_followed=False
    )

    assert first == [MatchEventKind.NEW_ACCEPTABLE]
    assert again == []


def test_birth_of_a_preferred_or_followed_litter_raises_born_alone() -> None:
    preferred = EventService.detect(
        MatchTier.PREFERRED, MatchTier.PREFERRED, {"new_preferred": "x"}, has_just_been_born=True, is_followed=False
    )
    followed = EventService.detect(
        MatchTier.ACCEPTABLE, MatchTier.ACCEPTABLE, {"new_acceptable": "x"}, has_just_been_born=True, is_followed=True
    )
    neither = EventService.detect(
        MatchTier.ACCEPTABLE, MatchTier.ACCEPTABLE, {"new_acceptable": "x"}, has_just_been_born=True, is_followed=False
    )

    assert preferred == [MatchEventKind.BORN]
    assert followed == [MatchEventKind.BORN]
    assert neither == []


def test_excluded_or_ignored_litters_raise_nothing() -> None:
    for tier in (MatchTier.EXCLUDED, MatchTier.IGNORED):
        assert EventService.detect(None, tier, {}, has_just_been_born=True, is_followed=False) == []
