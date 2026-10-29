"""The recorded Whoof listing (cocker, all of France), served to a collector without network."""

import html
import json
import re
from pathlib import Path
from typing import Any

import httpx

from services.collectors.whoof import WhoofCollector

FIXTURES = Path(__file__).parent / "fixtures" / "whoof"

LISTING_PATH = "/race/cocker-spaniel-anglais/annonces"


def recorded_listing() -> str:
    """
    Read the recorded listing page.

    Returns:
        The HTML.
    """
    return (FIXTURES / "listing_cocker.html").read_text(encoding="utf-8")


def recorded_ads() -> list[dict[str, Any]]:
    """
    The ads of the recorded listing page, as the collector reads them.

    Returns:
        The ads.
    """
    ads, _last_page_number = WhoofCollector.parse_listing_page(recorded_listing())
    return ads


def listing_with(ads: list[dict[str, Any]], last_page_number: int) -> str:
    """
    The recorded listing page with other ads and another number of pages.

    Args:
        ads: The ads of the page.
        last_page_number: Its last page number.

    Returns:
        The HTML.
    """
    data_page_match = re.search(r'data-page="([^"]*)"', recorded_listing())
    assert data_page_match is not None
    page = json.loads(html.unescape(data_page_match.group(1)))
    page["props"]["ads"]["data"] = ads
    page["props"]["ads"]["meta"]["last_page"] = last_page_number
    return f'<div id="app" data-page="{html.escape(json.dumps(page, ensure_ascii=False), quote=True)}"></div>'


def whoof_collector_serving(
    pages_by_number: dict[int, str] | None = None, requests: list[httpx.Request] | None = None
) -> WhoofCollector:
    """
    A collector that gets the listing pages, without pausing between pages.

    Args:
        pages_by_number: The HTML of each listing page; the recorded page alone when not given.
        requests: Filled with every request sent, when given.

    Returns:
        The collector.
    """
    served_pages = pages_by_number or {1: recorded_listing()}

    def answer(request: httpx.Request) -> httpx.Response:
        """
        Serve the listing page asked for.

        Args:
            request: The collector's request.

        Returns:
            The page, or a 404 for any other address.
        """
        if requests is not None:
            requests.append(request)
        page_number = int(request.url.params.get("page", "1"))
        if request.url.path != LISTING_PATH or page_number not in served_pages:
            return httpx.Response(404, text="Not found")
        return httpx.Response(200, text=served_pages[page_number])

    return WhoofCollector(http_client=httpx.Client(transport=httpx.MockTransport(answer)), sleep=lambda _seconds: None)
