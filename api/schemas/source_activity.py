"""What runs now, on the server and on the computers: the Sources page of every device shows it live."""

from pydantic import BaseModel, Field

from enums.listing_source import ListingSource


class CentraleCanineRelayActivity(BaseModel):
    """Where the relay of the Centrale Canine stands: a computer reading its pages, or a request waiting for one."""

    is_relaying: bool = Field(description="A computer reads the Centrale Canine pages now")
    source: ListingSource | None = Field(description="The relayed source being read")
    pages_read_count: int = Field(description="Pages of that source read so far")
    pages_left_count: int = Field(description="Pages of that source asked for and not read yet")
    is_requested: bool = Field(description="A relay asked from a device waits for the next check of a computer")
    is_desktop_app_on: bool = Field(description="A desktop app called within the last minutes: a computer is on")


class SourceActivity(BaseModel):
    """What runs now, for every device to show its buttons loading, wherever the run was asked."""

    running_sources: list[ListingSource] = Field(
        description="Sources the server reads now: a scheduled run of the worker, or a run asked by hand"
    )
    relay: CentraleCanineRelayActivity | None = Field(
        description="The relay by the desktop app; none when the server reads the Centrale Canine itself"
    )
