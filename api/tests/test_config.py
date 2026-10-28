"""Settings read from the environment: the sources a machine does not collect."""

import pytest

from core.config import Settings
from enums.listing_source import ListingSource


def test_every_source_is_collected_when_none_is_skipped(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("COLLECT_SKIPPED_SOURCES", raising=False)

    assert Settings(_env_file=None).collect_skipped_sources == frozenset()


def test_skipped_sources_are_read_from_a_comma_separated_list(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("COLLECT_SKIPPED_SOURCES", " centrale_canine, ,chiots_de_france ")

    settings = Settings(_env_file=None)

    assert settings.collect_skipped_sources == {ListingSource.CENTRALE_CANINE, ListingSource.CHIOTS_DE_FRANCE}


def test_a_misspelled_skipped_source_is_refused(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("COLLECT_SKIPPED_SOURCES", "centrale-canine")

    settings = Settings(_env_file=None)

    with pytest.raises(ValueError, match="centrale-canine"):
        _ = settings.collect_skipped_sources
