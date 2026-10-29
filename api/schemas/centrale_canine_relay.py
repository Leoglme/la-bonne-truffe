"""Relay of the Centrale Canine by a desktop app: the pages it reads for the API, and what the API asks next."""

from pydantic import BaseModel, Field

from enums.centrale_canine_relay_state import CentraleCanineRelayState
from schemas.source_status import SourceStatus


class RelayedPageResponse(BaseModel):
    """One Centrale Canine page as the desktop app read it, with curl or its browser."""

    url: str
    status_code: int | None = Field(default=None, description="HTTP status; none when the page could not be read")
    body: str = ""
    cloudflare_mitigation: str | None = Field(
        default=None, description="Value of the cf-mitigated header: « challenge » when Cloudflare refuses the client"
    )
    curl_error: str | None = Field(
        default=None,
        description="Why the page could not be read, with curl or the browser (the name stays for the installed apps)",
    )


class RelayPageRequest(BaseModel):
    """A page the desktop app reads with curl, with the headers to send."""

    url: str
    headers: dict[str, str]


class CentraleCanineRelayRequest(BaseModel):
    """A call of the desktop app, with every page it read since the relay started."""

    relay_token: str | None = Field(default=None, description="Token of the relay this app holds; none to start one")
    responses: list[RelayedPageResponse] = Field(default_factory=list)
    is_requested_by_user: bool = Field(
        default=False, description="« Relever maintenant »: run even when the last run is recent"
    )


class CentraleCanineRelayAnswer(BaseModel):
    """What the desktop app does next."""

    state: CentraleCanineRelayState
    relay_token: str | None
    page_requests: list[RelayPageRequest]
    source_statuses: list[SourceStatus]
