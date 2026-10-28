"""The recorded Chiots de France pages (cocker, France), served to a collector without network."""

from pathlib import Path

import httpx

from services.collectors.chiots_de_france import ChiotsDeFranceCollector

FIXTURES = Path(__file__).parent / "fixtures" / "chiots_de_france"

RECORDED_PAGES_BY_PATH: dict[str, str] = {
    "/chiots/cocker-spaniel-anglais/france": "listing_france.html",
    "/detail-annonce-cocker-spaniel-anglais_486970_5.html": "ad_486970.html",
    "/detail-annonce-cocker-spaniel-anglais_487726_5.html": "ad_487726.html",
}

HOME_PAGE = "<!DOCTYPE html><html><body><h1>Chiots de France</h1></body></html>"


def recorded_page(file_name: str) -> str:
    """
    Read a recorded page.

    Args:
        file_name: Its file in the fixtures.

    Returns:
        The HTML.
    """
    return (FIXTURES / file_name).read_text(encoding="utf-8")


def chiots_de_france_collector_serving(
    requests: list[httpx.Request] | None = None, withdrawn_paths: frozenset[str] = frozenset()
) -> ChiotsDeFranceCollector:
    """
    A collector that gets the recorded pages, without pausing between pages. Like the real site, a
    withdrawn ad, or any page not recorded, redirects to the home page.

    Args:
        requests: Filled with every request sent, when given.
        withdrawn_paths: Ad paths to treat as withdrawn.

    Returns:
        The collector.
    """

    def answer(request: httpx.Request) -> httpx.Response:
        """
        Serve the page asked for, like the real site.

        Args:
            request: The collector's request.

        Returns:
            The page, or a redirect to the home page.
        """
        if requests is not None:
            requests.append(request)
        if request.url.path == "/":
            return httpx.Response(200, text=HOME_PAGE)
        file_name = RECORDED_PAGES_BY_PATH.get(request.url.path)
        if file_name is None or request.url.path in withdrawn_paths:
            return httpx.Response(302, headers={"Location": "https://www.chiots-de-france.com/"})
        return httpx.Response(200, text=recorded_page(file_name))

    return ChiotsDeFranceCollector(
        http_client=httpx.Client(transport=httpx.MockTransport(answer), follow_redirects=True),
        sleep=lambda _seconds: None,
    )
