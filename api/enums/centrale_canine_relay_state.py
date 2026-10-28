"""Where a relay of the Centrale Canine stands, as the API tells the desktop app."""

from enum import StrEnum


class CentraleCanineRelayState(StrEnum):
    """What the desktop app does next: nothing, read pages, or show the run that just ended."""

    NOT_DUE = "not_due"
    BUSY = "busy"
    PAGES_NEEDED = "pages_needed"
    RUN_FINISHED = "run_finished"
