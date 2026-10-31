"""The recorded pages of a breeder site on Chiens de France (cocker), served to a collector without network."""

from pathlib import Path

import httpx

from services.collectors.chiens_de_france_sites import ChiensDeFranceSiteCollector, SiteTarget

FIXTURES = Path(__file__).parent / "fixtures" / "chiens_de_france_sites"

BREED_SLUG = "cocker-spaniel-anglais"
SITE_HOST_SUFFIX = ".chiens-de-france.com"
RECORDED_SITE_SLUG = "elevage-a"
EMPTY_SITE_SLUG = "elevage-b"
BROKEN_SITE_SLUG = "elevage-c"

RECORDED_PAGES_BY_PATH: dict[str, str] = {
    f"/{BREED_SLUG}/saillies": "litters_to_come.html",
    f"/{BREED_SLUG}/chiots": "litters_for_sale.html",
    f"/{BREED_SLUG}/chiots-a-vendre/495610": "litter_for_sale_495610.html",
    f"/{BREED_SLUG}/chiens/femelles": "females.html",
    f"/{BREED_SLUG}/chiens/etalons": "studs.html",
    f"/{BREED_SLUG}/chien/1212400": "dog_1212400.html",
}

EMPTY_SITE_PAGES_BY_PATH: dict[str, str] = {
    f"/{BREED_SLUG}/saillies": "litters_to_come_empty.html",
    f"/{BREED_SLUG}": "home.html",
}

STILL_CLOCK_SECONDS = 100.0
BROKEN_SITE_STATUS_CODE = 500


def site_target(slug: str, fresh_dog_external_ids: frozenset[str] = frozenset()) -> SiteTarget:
    """
    A site of the fixtures to read, for the cocker.

    Args:
        slug: Subdomain of the site (``elevage-a``).
        fresh_dog_external_ids: Dogs whose page is not read again.

    Returns:
        The site target.
    """
    return SiteTarget(
        breeder_id=1,
        breeder_source_id=slug,
        site_url=f"https://{slug}{SITE_HOST_SUFFIX}",
        breed_id=1,
        breed_slug=BREED_SLUG,
        fresh_dog_external_ids=fresh_dog_external_ids,
    )


def recorded_page(file_name: str) -> str:
    """
    Read a recorded page.

    Args:
        file_name: Its file in the fixtures.

    Returns:
        The HTML.
    """
    return (FIXTURES / file_name).read_text(encoding="utf-8")


def chiens_de_france_site_collector_serving(
    requests: list[httpx.Request] | None = None, pauses: list[float] | None = None
) -> ChiensDeFranceSiteCollector:
    """
    A collector that gets the recorded pages of ``elevage-a``, the empty litter list and the home page of
    ``elevage-b``, a 500 for every page of ``elevage-c`` and a 404 for any other page (the site has none).
    It does not wait between pages: the pauses it would make are recorded.

    Args:
        requests: Filled with every request sent, when given.
        pauses: Filled with every pause asked, when given; the clock then stands still.

    Returns:
        The collector.
    """

    def answer(request: httpx.Request) -> httpx.Response:
        """
        Serve the page asked for, like the real sites.

        Args:
            request: The collector's request.

        Returns:
            The page, a 404 or a 500.
        """
        if requests is not None:
            requests.append(request)
        slug = request.url.host.removesuffix(SITE_HOST_SUFFIX)
        if slug == BROKEN_SITE_SLUG:
            return httpx.Response(BROKEN_SITE_STATUS_CODE)
        pages_by_path = {RECORDED_SITE_SLUG: RECORDED_PAGES_BY_PATH, EMPTY_SITE_SLUG: EMPTY_SITE_PAGES_BY_PATH}
        file_name = pages_by_path.get(slug, {}).get(request.url.path)
        if file_name is None:
            return httpx.Response(404)
        return httpx.Response(200, text=recorded_page(file_name))

    recorded_pauses = pauses if pauses is not None else []
    return ChiensDeFranceSiteCollector(
        http_client=httpx.Client(transport=httpx.MockTransport(answer)),
        sleep=recorded_pauses.append,
        monotonic_clock=lambda: STILL_CLOCK_SECONDS,
    )
