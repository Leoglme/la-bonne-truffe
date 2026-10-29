"""
httpx transports that answer the Centrale Canine collector with the pages a desktop app read with curl,
the server being refused by Cloudflare (docs/02-sources.md).
"""

from collections.abc import Sequence

import httpx

from schemas.centrale_canine_relay import RelayedPageResponse, RelayPageRequest
from services.collectors.system_curl_transport import SKIPPED_REQUEST_HEADERS

CLOUDFLARE_MITIGATION_HEADER = "cf-mitigated"
EMPTY_LITTERS_PAGE: dict[str, object] = {"litters": {"count": 0, "node": []}}


class RelayedPagesTransport(httpx.BaseTransport):
    """Serves the pages the desktop app read; a page it did not read makes the request fail."""

    def __init__(self, responses: Sequence[RelayedPageResponse]) -> None:
        """
        Prepare the transport.

        Args:
            responses: Every page the desktop app read since the relay started.
        """
        self.responses_by_url = {response.url: response for response in responses}

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        """
        Answer with the page the desktop app read at this address.

        Args:
            request: The collector's request.

        Returns:
            The relayed response, whatever its status.

        Raises:
            httpx.ConnectError: When the desktop app could not read the page, or did not read it.
        """
        relayed_response = self.responses_by_url.get(str(request.url))
        if relayed_response is None:
            return self.answer_unread_page(request)
        if relayed_response.status_code is None:
            raise httpx.ConnectError(f"Lecture impossible sur le PC : {relayed_response.curl_error}", request=request)
        headers: dict[str, str] = {}
        if relayed_response.cloudflare_mitigation:
            headers[CLOUDFLARE_MITIGATION_HEADER] = relayed_response.cloudflare_mitigation
        return httpx.Response(
            relayed_response.status_code,
            headers=headers,
            content=relayed_response.body.encode("utf-8"),
            request=request,
        )

    def answer_unread_page(self, request: httpx.Request) -> httpx.Response:
        """
        Fail on a page the desktop app did not read: an empty answer would close the litters of its department.

        Args:
            request: The collector's request.

        Raises:
            httpx.ConnectError: Always.
        """
        raise httpx.ConnectError(f"Page non relevée par le PC : {request.url}", request=request)


class RelayPlanningTransport(RelayedPagesTransport):
    """Notes every page still to read, and answers it with an empty page so that the plan goes on."""

    def __init__(self, responses: Sequence[RelayedPageResponse]) -> None:
        """
        Prepare the transport.

        Args:
            responses: Every page the desktop app read since the relay started.
        """
        super().__init__(responses)
        self.unread_page_requests: list[RelayPageRequest] = []

    def answer_unread_page(self, request: httpx.Request) -> httpx.Response:
        """
        Note the page and the headers curl must send for it, those the system curl transport would send.

        Args:
            request: The collector's request.

        Returns:
            A page without any litter.
        """
        headers = {
            raw_name.decode("latin-1"): raw_value.decode("latin-1")
            for raw_name, raw_value in request.headers.raw
            if raw_name.decode("latin-1").lower() not in SKIPPED_REQUEST_HEADERS
        }
        self.unread_page_requests.append(RelayPageRequest(url=str(request.url), headers=headers))
        return httpx.Response(200, json=EMPTY_LITTERS_PAGE, request=request)
