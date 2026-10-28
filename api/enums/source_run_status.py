"""Outcome of one collection run on a source."""

from enum import StrEnum


class SourceRunStatus(StrEnum):
    """Outcome of one collection run on a source; ``running`` until it ends."""

    RUNNING = "running"
    OK = "ok"
    ERROR = "error"
