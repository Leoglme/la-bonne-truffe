"""The recorded Chiens de France pages (cocker, Bretagne), served to a collector without network."""

from pathlib import Path

import httpx

from services.collectors.chiens_de_france import ChiensDeFranceCollector

FIXTURES = Path(__file__).parent / "fixtures" / "chiens_de_france"

RECORDED_PAGES_BY_PATH: dict[str, str] = {
    "/chiots/cocker-spaniel-anglais/france/bretagne": "listing_bretagne.html",
    "/chiot/2199887": "puppy_2199887.html",
    "/saillie/494882": "litter_to_come_494882.html",
}

LISTING_PATH_PREFIX = "/chiots/"

LISTING_WITHOUT_AD = "<!DOCTYPE html><html><body><h1>Chiots de race</h1></body></html>"

STILL_CLOCK_SECONDS = 100.0


def recorded_page(file_name: str) -> str:
    """
    Read a recorded page.

    Args:
        file_name: Its file in the fixtures.

    Returns:
        The HTML.
    """
    return (FIXTURES / file_name).read_text(encoding="utf-8")


def chiens_de_france_collector_serving(
    requests: list[httpx.Request] | None = None, pauses: list[float] | None = None
) -> ChiensDeFranceCollector:
    """
    A collector that gets the recorded pages, a listing without ad for the other regions and a 404 for
    any other ad (withdrawn). It does not wait between pages: the pauses it would make are recorded.

    Args:
        requests: Filled with every request sent, when given.
        pauses: Filled with every pause asked, when given; the clock then stands still.

    Returns:
        The collector.
    """

    def answer(request: httpx.Request) -> httpx.Response:
        """
        Serve the page asked for, like the real site.

        Args:
            request: The collector's request.

        Returns:
            The page, or a 404.
        """
        if requests is not None:
            requests.append(request)
        file_name = RECORDED_PAGES_BY_PATH.get(request.url.path)
        if file_name is not None:
            return httpx.Response(200, text=recorded_page(file_name))
        if request.url.path.startswith(LISTING_PATH_PREFIX):
            return httpx.Response(200, text=LISTING_WITHOUT_AD)
        return httpx.Response(404)

    recorded_pauses = pauses if pauses is not None else []
    return ChiensDeFranceCollector(
        http_client=httpx.Client(transport=httpx.MockTransport(answer)),
        sleep=recorded_pauses.append,
        monotonic_clock=lambda: STILL_CLOCK_SECONDS,
    )
