"""The recorded Cœur de Cocker ads, served to a collector without network."""

from pathlib import Path

import httpx

from services.collectors.coeur_de_cocker import CoeurDeCockerCollector

FIXTURES = Path(__file__).parent / "fixtures" / "coeur_de_cocker"

ADS_PATH = "/wp-json/cdc/v1/adoption/annonces"


def recorded_ads_json() -> str:
    """
    Read the recorded JSON of the ads.

    Returns:
        The JSON text.
    """
    return (FIXTURES / "annonces.json").read_text(encoding="utf-8")


def coeur_de_cocker_collector_serving(
    body: str | None = None, requests: list[httpx.Request] | None = None
) -> CoeurDeCockerCollector:
    """
    A collector that gets the recorded ads, without pausing.

    Args:
        body: Body served for the ads; the recorded JSON when not given.
        requests: Filled with every request sent, when given.

    Returns:
        The collector.
    """

    def answer(request: httpx.Request) -> httpx.Response:
        """
        Serve the ads.

        Args:
            request: The collector's request.

        Returns:
            The JSON, or a 404 for any other address.
        """
        if requests is not None:
            requests.append(request)
        if request.url.path != ADS_PATH:
            return httpx.Response(404, text="Not found")
        return httpx.Response(200, text=body if body is not None else recorded_ads_json())

    return CoeurDeCockerCollector(
        http_client=httpx.Client(transport=httpx.MockTransport(answer)), sleep=lambda _seconds: None
    )
